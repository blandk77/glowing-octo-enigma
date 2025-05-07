import os
import time
import asyncio
import logging
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import (
    BOT_TOKEN, API_ID, API_HASH, ADMINS, OWNER, FFMPEG_PATH, FFMPEG_PROFILES,
    TEMP_DIR, VALID_EXTENSIONS
)
from utils import (
    get_system_stats, format_size, progress_bar, update_progress, run_ffmpeg
)

# Setup logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize bot
app = Client("encoder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Queue for encoding jobs
job_queue = []
current_job = None

# Ensure temp directory exists
Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)

async def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMINS

async def validate_config():
    """Validate config at startup."""
    if not BOT_TOKEN or not API_ID or not API_HASH:
        logging.error("Invalid bot token, API ID, or API hash")
        raise ValueError("Invalid bot configuration")
    if not ADMINS:
        logging.error("No admins defined")
        raise ValueError("No admins defined")
    if not FFMPEG_PROFILES:
        logging.error("No FFmpeg profiles defined")
        raise ValueError("No FFmpeg profiles defined")

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    if not await is_admin(message.from_user.id):
        await message.reply_text("You are not an authorized user!")
        return
    await message.reply_text("Welcome! Send a video file to encode.")

@Client.on_message(filters.media | filters.document)
async def handle_file(client: Client, message: Message):
    """Handle incoming video files."""
    if not await is_admin(message.from_user.id):
        logging.info("Non-admin user %s tried to send a file", message.from_user.id)
        return

    file = message.video or message.document
    if not file:
        await message.reply_text("Please send a valid video file.")
        return

    file_name = file.file_name or "video.mp4"
    ext = Path(file_name).suffix.lower()
    if ext not in VALID_EXTENSIONS:
        await message.reply_text("Unsupported file format. Please send a video file (e.g., .mp4, .mkv).")
        return

    # Ask for encoding profile
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"encode_{name}_{message.id}")]
        for name in FFMPEG_PROFILES.keys()
    ]
    await message.reply_text(
        "Select encoding profile:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@Client.on_callback_query(filters.regex(r"encode_(.+)_(\d+)"))
async def select_profile(client: Client, callback_query):
    """Handle encoding profile selection."""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("You are not authorized!")
        return

    profile, message_id = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
    message = callback_query.message
    file = message.reply_to_message.video or message.reply_to_message.document
    file_name = file.file_name or "video.mp4"

    job = {
        "user_id": callback_query.from_user.id,
        "message": message.reply_to_message,
        "profile": profile,
        "file_name": file_name,
        "status_message": await message.reply_text(f"Added to queue. Position: {len(job_queue) + 1}"),
    }

    job_queue.append(job)
    await callback_query.message.delete()  # Remove profile selection message
    await callback_query.answer(f"Added to queue using {profile} profile.")
    logging.info("Job added to queue: %s, profile: %s", file_name, profile)

    if not current_job:
        await process_queue()

@Client.on_callback_query(filters.regex("cancel_job"))
async def cancel_job(client: Client, callback_query):
    """Cancel a job."""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("You are not authorized!")
        return

    global current_job
    for job in job_queue:
        if job["status_message"].id == callback_query.message.id:
            job_queue.remove(job)
            await job["status_message"].edit_text("Job cancelled.")
            logging.info("Job cancelled: %s", job["file_name"])
            return

    if current_job and current_job["status_message"].id == callback_query.message.id:
        current_job = None
        await callback_query.message.edit_text("Job cancelled.")
        logging.info("Current job cancelled.")
        await process_queue()

    await callback_query.answer("Job cancelled.")

async def process_queue():
    """Process jobs in the queue."""
    global current_job
    if not job_queue or current_job:
        return

    current_job = job_queue.pop(0)
    message = current_job["message"]
    file = message.video or message.document
    file_name = current_job["file_name"]
    profile = current_job["profile"]
    status_message = current_job["status_message"]

    try:
        # Update queue positions
        for i, job in enumerate(job_queue):
            await job["status_message"].edit_text(
                f"In queue. Position: {i + 1}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel", callback_data="cancel_job")]]
                ),
            )

        # Download file
        input_file = os.path.join(TEMP_DIR, f"input_{file.file_id}{Path(file_name).suffix}")
        start_time = time.time()
        last_update = 0
        downloaded = 0

        async def progress(current, total):
            nonlocal downloaded, last_update
            downloaded = current
            if time.time() - last_update >= 10:
                speed = current / (time.time() - start_time) if time.time() > start_time else 0
                if not await update_progress(
                    client, status_message, current, total, speed, start_time, "download"
                ):
                    raise Exception("Insufficient disk space")
                last_update = time.time()

        await client.download_media(file, file_name=input_file, progress=progress)
        logging.info("Downloaded file: %s", input_file)

        # Encode file
        output_file = os.path.join(TEMP_DIR, f"output_{file.file_id}{Path(file_name).suffix}")
        await status_message.edit_text("Starting encoding...")
        encode_start = time.time()
        last_update = 0

        async def encode_progress():
            nonlocal last_update
            while os.path.exists(input_file):
                if time.time() - last_update >= 10:
                    compressed_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
                    await update_progress(
                        client, status_message, 0, 0, 0, encode_start, "encode",
                        file_name, compressed_size
                    )
                    last_update = time.time()
                await asyncio.sleep(1)

        encode_task = asyncio.create_task(encode_progress())
        success = run_ffmpeg(input_file, output_file, FFMPEG_PROFILES[profile])
        encode_task.cancel()

        if not success or not os.path.exists(output_file):
            await status_message.edit_text("Encoding failed!")
            logging.error("Encoding failed for %s", file_name)
            raise Exception("Encoding failed")

        # Upload file
        await status_message.edit_text("Starting upload...")
        start_time = time.time()
        last_update = 0
        uploaded = 0

        async def upload_progress(current, total):
            nonlocal uploaded, last_update
            uploaded = current
            if time.time() - last_update >= 10:
                speed = current / (time.time() - start_time) if time.time() > start_time else 0
                await update_progress(
                    client, status_message, current, total, speed, start_time, "upload"
                )
                last_update = time.time()

        await client.send_video(
            chat_id=message.chat.id,
            video=output_file,
            file_name=file_name,
            progress=upload_progress,
        )
        await status_message.edit_text("Encoding and upload completed!")
        logging.info("Uploaded file: %s", output_file)

    except Exception as e:
        await status_message.edit_text(f"Error: {str(e)}")
        logging.error("Error processing job %s: %s", file_name, str(e))
    finally:
        # Clean up
        for f in [input_file, output_file]:
            if os.path.exists(f):
                os.remove(f)
                logging.info("Deleted temp file: %s", f)
        current_job = None
        await process_queue()

async def main():
    """Main function to start the bot."""
    await validate_config()
    await app.start()
    await app.send_message(OWNER, "Bot started successfully!")
    logging.info("Bot started")
    await asyncio.Event().wait()  # Keep bot running

if __name__ == "__main__":
    asyncio.run(main())
