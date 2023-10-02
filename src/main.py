from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path
from struct import error as StructError, pack, unpack
from subprocess import run

import numpy as np
from imageio import get_reader, get_writer

parser = ArgumentParser(description="Encodes/decodes Raw Audio Video (RAV) " "files.")
parser.add_argument(
    "-i",
    "--input",
    type=Path,
    required=True,
    dest="input",
    help="The input video file, for encoding/decoding.",
)
parser.add_argument(
    "-o", "--output", type=Path, dest="output", default=None, help="The output path."
)
parser.add_argument(
    "-d",
    "--decode",
    action="store_true",
    help="Turn a RAV file back into a standard media file",
)
args = parser.parse_args()

encode = not args.decode

audio_channels = 1
audio_sample_rate = 16000
video_fps = 10
video_width = 160

original_path = args.input.expanduser().resolve()
print(f"Video path: {original_path}")

if args.output is None:
    output_path = original_path.with_suffix(".rav")
else:
    output_path = args.output

if encode:
    print("Encoding video")

    print("Converting audio")
    audio_path = original_path.parent / "temp.pcm"

    command = (
        f"ffmpeg -y -i "
        f'"{str(original_path)}" '
        f"-f u8 -ac {audio_channels} -ar {audio_sample_rate} "
        f'"{str(audio_path)}"'
    )
    print(f'Running command: "{command}"')
    run(command, shell=True, check=True)

    print(f"Quantifying video")
    video_path = original_path.parent / "temp.mp4"

    command = (
        f"ffmpeg -y -i "
        f'"{str(original_path)}" '
        f'-vf "fps={video_fps},scale={video_width}:-1" -an '
        f'"{str(video_path)}"'
    )
    print(f'Running command: "{command}"')
    run(command, shell=True, check=True)

    print("Encoding RAV file")

    print(f"Output path: {output_path}")

    video_height = 0

    with output_path.open("wb") as output:
        output.write(pack("<L", 0))  # Frame count, to be written later
        output.write(pack("B", 8))
        output.write(pack("<L", 16000))
        output.write(pack("B", 10))
        output.write(pack("<H", video_width))
        output.write(pack("<H", 0))  # Frame height, to be written later
        frame = 0
        with audio_path.open("rb") as audio, get_reader(str(video_path)) as video:
            while True:
                segment_length = int(audio_sample_rate / video_fps)

                audio_segment = audio.read(segment_length)
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

                video_height = len(image_frame)

                # https://stackoverflow.com/a/61521134/10291933
                R5 = (image_frame[..., 0] >> 3).astype(np.uint16) << 11
                G6 = (image_frame[..., 1] >> 2).astype(np.uint16) << 5
                B5 = (image_frame[..., 2] >> 3).astype(np.uint16)
                image_block = (R5 | G6 | B5).flatten()
                # imwrite(image_buffer, image_frame, "jpg")
                image_buffer.write(pack(f"<{video_width*video_height}H", *image_block))

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
                segment_buffer.write(pack("<L", frame))
                segment_buffer.write(pack("<L", audio_length + video_length))
                segment_buffer.write(audio_buffer.read())
                segment_buffer.write(video_buffer.read())
                segment_buffer.write(pack("<L", audio_length + video_length))

                print(
                    f"Frame #{frame} "
                    f"segment: {segment_buffer.tell()} "
                    f"audio: {audio_length} "
                    f"video: {video_length}"
                )

                segment_buffer.seek(0)

                output.write(segment_buffer.read())

                frame += 1
        output.seek(0)
        output.write(pack("<L", frame + 1))
        output.seek(12)
        output.write(pack("<H", video_height))
else:
    print("Decoding video")

    print("Decoding streams")
    audio_path = original_path.parent / "temp.pcm"
    video_path = original_path.parent / "temp.mp4"
    with original_path.open("rb") as original:
        frame_count = unpack("<L", original.read(4))[0]
        sample_size = unpack("B", original.read(1))[0]
        audio_sample_rate = unpack("<L", original.read(4))[0]
        fps = unpack("B", original.read(1))[0]
        frame_width = unpack("<H", original.read(2))[0]
        frame_height = unpack("<H", original.read(2))[0]
        print(f"frame_count = {frame_count}")
        print(f"sample_size = {sample_size}")
        print(f"audio_sample_rate = {audio_sample_rate}")
        print(f"fps = {fps}")
        print(f"frame_width = {frame_width}")
        print(f"frame_height = {frame_height}")
        with audio_path.open("wb") as temp_audio, get_writer(
            str(video_path), fps=video_fps
        ) as temp_video:
            while True:
                try:
                    frame = unpack("<L", original.read(4))[0]
                except StructError:
                    print("End of stream")
                    break
                segment_length = unpack("<L", original.read(4))[0]

                audio_length = unpack("<L", original.read(4))[0]
                audio = original.read(audio_length)

                image_length = unpack("<L", original.read(4))[0]
                image_block = original.read(image_length)
                image_ints = unpack(f"<{frame_width * frame_height}H", image_block)
                image = np.empty((frame_height, frame_width, 3), np.uint8)
                for pos, val in enumerate(image_ints):
                    r = pos // frame_width
                    c = pos % frame_width
                    R5 = (val & 0b1111100000000000) >> 11
                    G6 = (val & 0b0000011111100000) >> 5
                    B5 = val & 0b0000000000011111
                    R8 = (R5 * 527 + 23) >> 6
                    G8 = (G6 * 259 + 33) >> 6
                    B8 = (B5 * 527 + 23) >> 6
                    image[r][c][0] = R8
                    image[r][c][1] = G8
                    image[r][c][2] = B8

                end_segment_length = unpack("<L", original.read(4))[0]

                assert segment_length == end_segment_length

                temp_audio.write(audio)
                temp_video.append_data(image)

                print(
                    f"Frame #{frame} "
                    f"segment: {segment_length} "
                    f"audio: {audio_length} "
                    f"video: {image_length}"
                )

    print("Merging streams")

    wav_audio_path = audio_path.with_suffix(".wav")

    command = (
        f"ffmpeg -y "
        f"-f u8 -ac {audio_channels} -ar {audio_sample_rate} "
        f'-i "{str(audio_path)}" '
        f'"{str(wav_audio_path)}"'
    )
    print(f'Running command "{command}"')
    run(command, shell=True, check=True)

    print(f"Output path: {output_path}")

    command = (
        f"ffmpeg -y "
        f'-i "{str(video_path)}" '
        f'-i "{str(wav_audio_path)}" '
        f'"{str(output_path)}"'
    )
    print(f'Running command "{command}"')
    run(command, shell=True, check=True)
