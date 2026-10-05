import os
import subprocess
import imageio_ffmpeg


# =========================================================
# INPUT / OUTPUT
# =========================================================

input_video = os.path.join(
    "output",
    "traffic_demo_full.mp4"
)

output_video = os.path.join(
    "output",
    "traffic_demo_full_h264.mp4"
)


# =========================================================
# CHECK INPUT
# =========================================================

if not os.path.exists(input_video):

    raise FileNotFoundError(
        f"Input video not found: {input_video}"
    )


print("Input video:")
print(input_video)

print(
    "Input size:",
    round(
        os.path.getsize(input_video) / (1024 * 1024),
        2
    ),
    "MB"
)


# =========================================================
# GET FFMPEG
# =========================================================

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

print("\nFFmpeg:")
print(ffmpeg_path)


# =========================================================
# CONVERT TO H264
# =========================================================

command = [
    ffmpeg_path,

    "-y",

    "-i",
    input_video,

    # H.264 video
    "-c:v",
    "libx264",

    # Browser-friendly pixel format
    "-pix_fmt",
    "yuv420p",

    # Good quality
    "-crf",
    "23",

    # Fast encoding
    "-preset",
    "medium",

    # Improve browser playback
    "-movflags",
    "+faststart",

    # No audio needed
    "-an",

    output_video
]


print("\nConverting video...")
print("Please wait until conversion finishes.\n")


result = subprocess.run(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)


print(result.stdout)


# =========================================================
# CHECK RESULT
# =========================================================

if result.returncode != 0:

    raise RuntimeError(
        "Video conversion failed."
    )


if not os.path.exists(output_video):

    raise RuntimeError(
        "Converted video was not created."
    )


print("\n" + "=" * 50)
print("VIDEO CONVERSION SUCCESSFUL")
print("=" * 50)

print(
    "Output:",
    output_video
)

print(
    "Output size:",
    round(
        os.path.getsize(output_video)
        /
        (1024 * 1024),
        2
    ),
    "MB"
)

print("\nUse this video in Streamlit:")
print(
    "output/traffic_demo_full_h264.mp4"
)