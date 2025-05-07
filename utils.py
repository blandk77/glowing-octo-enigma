import os
import time
import psutil
import logging
import subprocess
from pathlib import Path
from pyrogram.types import Message
from pyrogram import Client
from humanize import naturalsize

# Setup logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def get_system_stats():
    """Get system stats: CPU, RAM, disk space."""
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": cpu_usage,
        "ram": ram.percent,
        "disk_left": disk.free,
    }

def format_size(size):
    """Convert bytes to human-readable format."""
    return naturalsize(size, binary=True)

def progress_bar(percentage):
    """Generate progress bar with ⬢ and ⬡."""
    filled = int(percentage / 5)  # 20 segments for 100%
    empty = 20 - filled
    return "⬢" * filled + "⬡" * empty

async def update_progress(
    client: Client,
    message: Message,
    current: int,
    total: int,
    speed: float,
    start_time: float,
    stage: str,
    file_name: str = None,
    compressed_size: int = None,
):
    """Update progress bar for download/upload/encoding."""
    stats = get_system_stats()
    percentage = (current / total) * 100 if total > 0 else 0
    elapsed = time.time() - start_time
    eta = (total - current) / speed if speed > 0 else 0
    speed_str = format_size(speed) + "/s"

    # Check for high RAM usage
    if stats["ram"] >= 90:
        await message.reply_text("⚠️ Warning: RAM usage is above 90%! Continuing process.")

    # Check for low disk space
    if stats["disk_left"] < 1 * 1024 * 1024 * 1024:  # Less than 1GB
        await message.reply_text("⚠️ Error: Insufficient disk space!")
        logging.error("Insufficient disk space: %s left", format_size(stats["disk_left"]))
        return False

    bar = progress_bar(percentage)
    if stage == "download":
        text = (
            "⚠️ Please wait...\n\n"
            "☃️ Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....\n\n"
            f"{bar}\n"
            "╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
            f"┣ sɪᴢᴇ: {format_size(current)} | {format_size(total)}\n"
            f"┣ ᴅᴏɴᴇ: {percentage:.2f}%\n"
            f"┣ sᴩᴇᴇᴅ: {speed_str}\n"
            f"┣ ᴇᴛᴀ: {int(eta)}s\n"
            "╰━━━━━━━━━━━━━━━➣\n\n"
            "╭─⌯══ sʏsᴛᴇᴍ | ʜᴛᴏᴘ ══⌯──★\n"
            f"├ ᴄᴘᴜ ᴜsᴀɢᴇ: {stats['cpu']:.1f}%\n"
            f"├ ʀᴀᴍ ᴜsᴀɢᴇ: {stats['ram']:.1f}%\n"
            f"├ ᴅɪsᴋ sᴘᴀᴄᴇ ʟᴇғᴛ: {format_size(stats['disk_left'])}\n"
            f"├ ᴅᴏᴡɴʟᴏᴀᴅ / ᴜᴘʟᴏᴀ sᴩᴇᴇᴅ: {speed_str}\n"
            "╰─══ Telegram Guy!!══─★"
        )
    elif stage == "encode":
        text = (
            "🗜 Compressing...\n\n"
            "╭─⌯══ sʏsᴛᴇᴍ | ʜᴛᴏᴘ ══⌯──★\n"
            f"├ ᴄᴘᴜ ᴜsᴀɢᴇ: {stats['cpu']:.1f}%\n"
            f"├ ʀᴀᴍ ᴜsᴀɢᴇ: {stats['ram']:.1f}%\n"
            f"├ ᴅɪsᴋ sᴘᴀᴄᴇ ʟᴇғᴛ: {format_size(stats['disk_left'])}\n"
            f"├ ᴘʀᴏᴄᴇssɪɴɢ ᴍᴇᴅɪᴀ: {file_name}\n"
            f"├ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ: {format_size(total)}\n"
            f"├ ᴄᴏᴍᴘʀᴇssᴇᴅ: {format_size(compressed_size) if compressed_size else 'N/A'}\n"
            "╰─══ Telegram Guy!!══─★"
        )
    elif stage == "upload":
        text = (
            "⚠️ Please wait...\n\n"
            "🌨️ Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....\n\n"
            f"{bar}\n"
            "╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
            f"┣ sɪᴢᴇ: {format_size(current)} | {format_size(total)}\n"
            f"┣ ᴅᴏɴᴇ: {percentage:.2f}%\n"
            f"┣ sᴩᴇᴇᴅ: {speed_str}\n"
            f"┣ ᴇᴛᴀ: {int(eta)}s\n"
            "╰━━━━━━━━━━━━━━━➣\n\n"
            "╭─⌯══ sʏsᴛᴇᴍ | ʜᴛᴏᴘ ══⌯──★\n"
            f"├ ᴄᴘᴜ ᴜsᴀɢᴇ: {stats['cpu']:.1f}%\n"
            f"├ ʀᴀᴍ ᴜsᴀɢᴇ: {stats['ram']:.1f}%\n"
            f"├ ᴅɪsᴋ sᴘᴀᴄᴇ ʟᴇғᴛ: {format_size(stats['disk_left'])}\n"
            f"├ ᴅᴏᴡɴʟᴏᴀᴅ / ᴜᴩʟᴏᴀ sᴩᴇᴇᴅ: {speed_str}\n"
            "╰─══ ᴘᴀɴᴅᴀᴡᴇᴘ ══─★"
        )

    try:
        await message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="cancel_job")]]
            ),
        )
    except Exception as e:
        logging.error("Failed to update progress: %s", e)
    return True

def run_ffmpeg(input_file: str, output_file: str, ffmpeg_cmd: str):
    """Run FFmpeg command and return success status."""
    cmd = f"{FFMPEG_PATH} -i \"{input_file}\" {ffmpeg_cmd} \"{output_file}\""
    try:
        process = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        logging.info("FFmpeg command executed: %s", cmd)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("FFmpeg failed: %s", e.stderr)
        return False
