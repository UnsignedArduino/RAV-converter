# RAV-converter

Encode/decode Raw Audio Video (RAV) files!

Yes, I came up with a name for this horrible format on the spot.

## Script

I've made a Python script that can convert any media file that FFmpeg supports
to RAV.

### Installation

1. Make sure Python 3 is installed and on path.
2. Make sure FFmpeg is installed and on path.
3. Download repo
4. Install requirements

### Usage

Run with `-h` to show the help:

```commandline
usage: main.py [-h] -i INPUT [-o OUTPUT] [-d]

Encodes/decodes Raw Audio Video (RAV) files.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        The input video file, for encoding/decoding.
  -o OUTPUT, --output OUTPUT
                        The output path.
  -d, --decode          Turn a RAV file back into a standard media file
```

#### Examples:

##### Convert to RAV:

`input.mkv` is the input media file - must be support by your version of
FFmpeg!

`output.rav` is the output RAV file. Note that this is an extremely lossy
conversion, see file format below.

```commandline
python main.py -i "input.mkv" -o "output.rav"
```

#### Convert to media file

`output.rav` is an already existing RAV file.

`output.mkv` is the RAV file that has been converted back into a media file.
Note that RAV files are extremely lossy so the resulting media file will
definitely not look good!

```commandline
python main.py -i "output.rav" -o "output.mkv" -d
```

## Format

### Quality

RAV files carry:

- Audio
    - 8 bit samples
    - 32 khz sampling rate
    - 1 channel
- Video
    - 10 FPS
    - RGB565 bitmap images

Impressive quality, right?

### Byte format

The header is like this:

| File position | Data type                     | Description                                  |
|---------------|-------------------------------|----------------------------------------------|
| 0             | Little endian `unsigned long` | Number of frames.                            |
| 4             | Byte                          | Audio sample size, (in bits) should equal 8. |
| 5             | Little endian `unsigned long` | Audio sample rate, should equal 32000.       |
| 9             | Byte                          | FPS, should equal 10.                        |
| 10            | Little endian `unsigned int`  | Frame width.                                 |
| 12            | Little endian `unsigned int`  | Frame height.                                |

The majority of the file is composed of frames, which last 100 ms (10 FPS) and
includes PCM audio and a RGB565 TFT blast-able bitmap.

A frame goes like this:

| Byte offset              | Data type                                   | Description                                                                                                                                                                                             |
|--------------------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| +4                       | Little endian `unsigned long`               | The frame number.                                                                                                                                                                                       |
| +4                       | Little endian `unsigned long`               | The length of the frame.                                                                                                                                                                                |
| +4                       | Little endian `unsigned long`               | The length of the audio for the frame, should be 16000 bytes.                                                                                                                                           |
| +32000                   | 32000-byte-long block, `unsigned char`s     | The audio data itself.                                                                                                                                                                                  |
| +4                       | Little endian `unsigned long`               | The length of the bitmap image for the frame, a variable amount.                                                                                                                                        |
| +Image length from above | Variable length byte block, `unsigned int`s | The bitmap image itself.                                                                                                                                                                                |
| +4                       | Little endian `unsigned long`               | The length of the frame, useful for seeking backwards. Note that after seeking backwards this many bytes, you will also have to seek 8 more bytes back for the original frame length and frame counter! |

Then the next frame begins, and repeat until EOF.
