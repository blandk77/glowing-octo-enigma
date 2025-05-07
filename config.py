# Bot configuration
BOT_TOKEN = "7898251858:AAEH62w1B0wWw5M7Fq8J62tebzTH30zXuM4"
API_ID = 27394279
API_HASH = "90a9aa4c31afa3750da5fd686c410851"
ADMINS = [7465574522]
OWNER = 7465574522

# FFmpeg configuration
FFMPEG_PATH = "ffmpeg" 
FFMPEG_PROFILES = {
    "H265": (
        '-vf "drawtext=text=\'For More Animes In Low MB, Check Out @Animes_Guy in Telegram\':'
        'x=\'if(gte(t,240),w-(t-240)*60,NAN)\':y=10:fontsize=20:fontcolor=white:'
        'enable=\'gte(t,240)\':box=0" -map 0 -c:v libx265 -pix_fmt yuv420p -crf 30 '
        '-c:s copy -s 1920x1080 -b:v 150k -c:a libopus -b:a 35k -preset veryfast'
    ),
    "AV1": (
        '-vf "drawtext=text=\'For More Animes In Low MB, Check Out @Animes_Guy in Telegram\':'
        'x=\'if(gte(t,240),w-(t-240)*60,NAN)\':y=10:fontsize=20:fontcolor=white:'
        'enable=\'gte(t,240)\':box=0" -map 0 -c:v libaom-av1 -pix_fmt yuv420p -crf 30 '
        '-cpu-used 4 -c:s copy -s 1920x1080 -b:v 150k -c:a libopus -b:a 35k'
    ),
    "H264": (
        '-vf "drawtext=text=\'For More Animes In Low MB, Check Out @Animes_Guy in Telegram\':'
        'x=\'if(gte(t,240),w-(t-240)*60,NAN)\':y=10:fontsize=20:fontcolor=white:'
        'enable=\'gte(t,240)\':box=0" -map 0 -c:v libx264 -pix_fmt yuv420p -crf 28 '
        '-c:s copy -s 1920x1080 -b:v 200k -c:a libopus -b:a 35k -preset veryfast'
    ),
    "VP9": (
        '-vf "drawtext=text=\'For More Animes In Low MB, Check Out @Animes_Guy in Telegram\':'
        'x=\'if(gte(t,240),w-(t-240)*60,NAN)\':y=10:fontsize=20:fontcolor=white:'
        'enable=\'gte(t,240)\':box=0" -map 0 -c:v libvpx-vp9 -pix_fmt yuv420p -crf 30 '
        '-b:v 150k -c:s copy -s 1920x1080 -c:a libopus -b:a 35k'
    ),
}

# Temporary storage
TEMP_DIR = "./temp"

# Valid video extensions
VALID_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
