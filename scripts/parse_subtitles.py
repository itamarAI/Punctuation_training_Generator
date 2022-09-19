import webvtt
import pandas as pd
import glob
from pathlib import Path
from typing import Generator

##********************************************************************************************************************************
## Parses the subtitle file - returns the transcript as a string 

def vtt_lines(src) -> Generator[str, None, None]:
    """
    Extracts all text lines from a vtt file which may contain duplicates

    :param src: File path or file like object
    :return: Generator for lines as strings
    """
    vtt = webvtt.read(src)

    for caption in vtt:  # type: webvtt.structures.Caption
        # A caption which may contain multiple lines
        for line in caption.text.strip().splitlines():  # type: str
            # Process each one of them
            yield line


def deduplicated_lines(lines) -> Generator[str, None, None]:
    """
    Filters all duplicated lines from list or generator

    :param lines: iterable or generator of stringsa
    :return: Generator for lines as strings without duplicates
    """
    last_line = ""
    for line in lines:
        if line == last_line:
            continue

        last_line = line
        yield line


def vtt_to_linear_text(src, line_end="\n"):
    """
    Converts an vtt caption file to linear text.

    :param src: Path or path like object to an existing vtt file
    :param savefile: Path object to save content in
    :param line_end: Default to line break. May be set to a space for a single line output.
    """
    transcript = ''
    #with savefile.open("w") as writer:
    for line in deduplicated_lines(vtt_lines(src)):
        transcript = transcript + line.replace("&nbsp;", " ").strip() + " "
        #writer.write(line.replace("&nbsp;", " ").strip() + " ")
    
    return transcript