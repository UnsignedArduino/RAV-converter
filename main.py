from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path
from struct import pack
from subprocess import run

from imageio import get_reader, imwrite

parser = ArgumentParser(description="Converts video files to Raw Audio Video "
                                    "(RAV) files.")
parser.add_argument("path", type=Path,
                    help="The path to the video file.")
parser.add_argument("-d", "--decode", action="store_true",
                    help="Turn a RAV file into an MP4 file")
args = parser.parse_args()

encode = not args.decode

# Charles

audio_channels = 1
audio_sample_rate = 8000
video_fps = 10
video_width = 160

if encode:
    print(f"Encoding video")

    original_path = args.path.expanduser().resolve()
    print(f"Video path: {original_path}")

    print("Converting audio")
    audio_path = original_path.parent / "temp.pcm"

    command = f"ffmpeg -y -i " \
              f"\"{str(original_path)}\" " \
              f"-f u8 -ac {audio_channels} -ar {audio_sample_rate} " \
              f"\"{str(audio_path)}\""
    print(f"Running command: \"{command}\"")
    run(command, shell=True, check=True)

    print(f"Quantifying video")
    video_path = original_path.parent / "temp.mp4"

    command = f"ffmpeg -y -i " \
              f"\"{str(original_path)}\" " \
              f"-vf \"fps={video_fps},scale={video_width}:-1\" -an " \
              f"\"{str(video_path)}\""
    print(f"Running command: \"{command}\"")
    run(command, shell=True, check=True)

    print("Encoding RAV file")
    output_path = original_path.with_suffix(".rav")
    print(f"Output path: {output_path}")

    with output_path.open("wb") as output:
        frame = 0
        with audio_path.open("rb") as audio, \
             get_reader(str(video_path)) as video:
            while True:
                segment_len = int(audio_sample_rate / video_fps)

                audio_segment = audio.read(segment_len)
                audio_length = len(audio_segment)

                if audio_length == 0:
                    print("Reached end of audio stream")
                    break

                image_buffer = BytesIO()
                try:
                    image_frame = video.get_data(frame)
                except IndexError:
                    print("Reached end of video stream")
                    break
                imwrite(image_buffer, image_frame, "jpg")
                video_length = image_buffer.tell()
                image_buffer.seek(0)
                video_segment = image_buffer.read()

                audio_buffer = BytesIO()
                audio_buffer.write(pack("<L", audio_length))
                audio_buffer.write(audio_segment)
                audio_buffer.seek(0)

                video_buffer = BytesIO()
                video_buffer.write(pack("<L", video_length))
                video_buffer.write(video_segment)
                video_buffer.seek(0)

                segment_buffer = BytesIO()
                segment_buffer.write(pack("<L", audio_length + video_length))
                segment_buffer.write(audio_buffer.read())
                segment_buffer.write(video_buffer.read())

                print(f"Frame #{frame} length: {segment_buffer.tell()}")

                segment_buffer.seek(0)

                output.write(pack("<L", frame))
                output.write(segment_buffer.read())

                frame += 1
