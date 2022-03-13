from argparse import ArgumentParser
from pathlib import Path

parser = ArgumentParser(description="Converts video files to Raw Audio Video "
                                    "(RAV) files.")
parser.add_argument("path", type=Path,
                    help="The path to the video file.")
args = parser.parse_args()

original_path = args.path.expanduser().resolve()
print(f"Video path: {original_path}")
