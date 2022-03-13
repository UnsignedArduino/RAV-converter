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

The converter will leave lots of `temp.*` files behind, you can delete those.
Make sure that there are no files named `temp` beause they will be overwritten 
by FFmpeg!

## Format

### Quality

RAV files carry:
- Audio
  - 8 bit samples
  - 8 khz sampling rate
  - 1 channel
- Video
  - 10 FPS
  - 160x(auto-calculated) frame size
  - JPEG images

Impressive quality, right?

### Byte format

The entire file is composed of frames, which last 100 ms (10 FPS) and includes
PCM audio and an JPEG image. 

A frame goes like this:

| Byte offset                   | Data type                                    | Description                                                                                                                                                                                             |
|-------------------------------|----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| +4                            | Little endian `unsigned long`                | The frame number.                                                                                                                                                                                       |
| +4                            | Little endian `unsigned long`                | The length of the frame.                                                                                                                                                                                |
| +4                            | Little endian `unsigned long`                | The length of the audio for the frame, should be 800 bytes.                                                                                                                                             |
| +800                          | 800-byte-long block, `unsigned char`s        | The audio data itself.                                                                                                                                                                                  |
| +4                            | Little endian `unsigned long`                | The length of the JPEG image for the frame, a variable amount (usually ~1 kb)                                                                                                                           |
| +JPEG image length from above | Variable length byte block, `unsigned char`s | The JPEG image itself.                                                                                                                                                                                  |
| +4                            | Little endian `unsigned long`                | The length of the frame, useful for seeking backwards. Note that after seeking backwards this many bytes, you will also have to seek 8 more bytes back for the original frame length and frame counter! |

Then the next frame begins, and repeat until EOF.
