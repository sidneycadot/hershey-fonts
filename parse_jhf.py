#! /usr/bin/env python3

from PIL import Image, ImageDraw
import numpy as np
import math
import glob

def parse_jhf_file(filename: str):

    font = []

    with open(filename, "r") as fi:

        for line in fi:

            assert line.endswith("\n")

            line = line[:-1]

            identifier = int(line[:5])

            # size of the glyph description, in units of 2 characters each.
            size = int(line[5:8])

            assert len(line) == 8 + 2 * size

            x_left  = ord(line[8]) - 82
            x_right = ord(line[9]) - 82

            idx = 10
            strokes = []
            stroke = []
            while idx < len(line):
                if line[idx:idx+2] == " R":
                    if len(stroke) > 0:
                        # Flush current stroke, if any.
                        strokes.append(tuple(stroke))
                        stroke.clear()
                else:
                    stroke.append((ord(line[idx]) - 82, ord(line[idx + 1]) - 82))
                idx += 2

            if len(stroke) > 0:
                # Flush current stroke, if any.
                strokes.append(tuple(stroke))
                stroke.clear()

            glyph = (identifier, x_left, x_right, tuple(strokes))

            font.append(glyph)

    return font


def string_to_glyph(font, s):
    charmap = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

    n_strokes = []
    n_x_left = 0
    n_x_right = 0

    x_offset = 0

    first = True

    for c in s:
        idx = charmap.find(c)
        if c == -1:
            idx = len(charmap) # 95

        (x_left, x_right, strokes) = font[idx]

        if first:
            n_x_left = n_x_right = x_left
            first = False

        print(n_x_right, c)

        for stroke in strokes:
            nstroke = [(x + n_x_right - x_left, y) for (x, y) in stroke]
            n_strokes.append(tuple(nstroke))

        n_x_right += (x_right - x_left)

    return (n_x_left, n_x_right, tuple(n_strokes))

def render_string(font, s, scale, filename):
    (x_left, x_right, strokes) = string_to_glyph(font, s)

    print(strokes)

    x_min = +math.inf
    x_max = -math.inf
    y_min = +math.inf
    y_max = -math.inf
    for stroke in strokes:
        for (x, y) in stroke:
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)

    width  = scale * (x_max - x_min)
    height = scale * (y_max - y_min)

    im = Image.new('RGB', (width, height), "white")
    draw  = ImageDraw.Draw(im)

    for stroke in strokes:
        drawstroke = [((x - x_min) * scale, (y - y_min) * scale) for (x, y) in stroke]
        draw.line(drawstroke, fill='black')

    im.save(filename)


def make_jhf_image(filename):

    assert filename.endswith(".jhf")

    try:
        characters = parse_jhf_file(filename)
    except Exception as e:
        print("Error while reading file '{}': {}".format(filename, e))
        return

    x_min = +math.inf
    x_max = -math.inf
    y_min = +math.inf
    y_max = -math.inf
    for (identifier, x_left, x_right, strokes) in characters:
        for stroke in strokes:
            for (x, y) in stroke:
                x_min = min(x_min, x)
                x_max = max(x_max, x)
                y_min = min(y_min, y)
                y_max = max(y_max, y)

    scale = 10

    n = len(characters)

    c_width  = (x_max - x_min) * scale
    c_height = (y_max - y_min) * scale

    nx = min(16, n)
    ny = (n + nx - 1) // nx

    im = Image.new('RGB', (nx * c_width, ny * c_height), "white")
    draw  = ImageDraw.Draw(im)

    for (index, (identifier, x_left, x_right, strokes)) in enumerate(characters, 0):
        for stroke in strokes:
            drawstroke = [((index % nx) * c_width + (x - x_min) * scale, (index // nx) * c_height + (y - y_min) * scale) for (x, y) in stroke]
            draw.line(drawstroke, fill='black')

    filename_png = filename[:-4] + ".png"

    im.save(filename_png)

for filename in glob.glob("fonts/*.jhf"):
    print("Processing {} ...".format(filename))
    make_jhf_image(filename)
