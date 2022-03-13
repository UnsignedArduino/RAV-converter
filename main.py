from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

parser = ArgumentParser(description="Converts video files to Raw Audio Video "
                                    "(RAV) files.")
parser.add_argument("path", type=Path,
                    help="The path to the video file.")
parser.add_argument("-d", "--decode", action="store_true",
                    help="Turn a RAV file into an MP4 file")
args = parser.parse_args()

encode = not args.decode

if encode:
    print(f"Encoding video")

    original_path = args.path.expanduser().resolve()
    print(f"Video path: {original_path}")

    print("Converting audio")
    audio_path = original_path.parent / "temp.pcm"

    command = f"ffmpeg -y -i " \
              f"\"{str(original_path)}\" " \
              "-f u8 -ac 1 -ar 8000 " \
              f"\"{str(audio_path)}\""
    print(f"Running command: \"{command}\"")
    run(command, shell=True, check=True)

    print(f"Quantifying video")
    video_path = original_path.parent / "temp.mp4"

    command = f"ffmpeg -y -i " \
              f"\"{str(original_path)}\" " \
              f"-vf \"fps=10,scale=160:-1\" -an " \
              f"\"{str(video_path)}\""
    print(f"Running command: \"{command}\"")
    run(command, shell=True, check=True)
