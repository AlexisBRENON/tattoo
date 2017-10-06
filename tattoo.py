#! /usr/bin/env python3

import math
import argparse
import subprocess

import svgwrite

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decode", '-d',
        action="store_true"
    )
    parser.add_argument(
        "--encode", '-e',
        type=str
    )
    parser.add_argument(
        "--width", "-w",
        help="Tattoo width in mm",
        type=int
    )

    args = parser.parse_args()

    if args.decode:
        decode()
    else:
        text = None
        if args.encode:
            text = args.encode
        else:
            text = input("Text > ").strip()
        print(text)
        encode(text, args.width)

def encode(text, width):
    encoding_output = subprocess.check_output(
        [
            "openssl", "enc",
            "-aes-128-ecb",
            "-nosalt",
            "-pass", "pass:daddy"
        ],
        input=bytes(text, "utf-8")
    )
    str_data = "".join(["{:08b}".format(byte) for byte in list(encoding_output)])
    bits_data = [int(b) for b in str_data]
    bits_data.reverse()

    num_vertices = 6
    tattoo_bit_width = 8
    tattoo_bit_height = int(len(bits_data)/tattoo_bit_width)

    radius = 0.8
    print(radius)

    bit_height = 2 * radius
    bit_width = 2 * radius * math.sin(2 * math.pi * math.floor(num_vertices/4) / num_vertices)
    print(bit_height, bit_width)

    tattoo_width = ((tattoo_bit_width + 0.5) * 2)
    print(tattoo_width)
    scale = width * 3.78 / tattoo_width
    radius *= scale
    bit_height *= scale
    bit_width *= scale

    margin_x = 3 * bit_width
    margin_y = 3 * bit_height

    dwg = svgwrite.Drawing('tattoo.svg', size=('210mm', '297mm'))
    stroke_color = svgwrite.rgb(0, 0, 0)

    center_x = radius + margin_x
    center_y = math.cos(30) * radius + margin_y

    def shift_bit(_):
        nonlocal center_x
        center_x = center_x + (2 * scale)
    def shift_byte(j):
        nonlocal center_y, center_x
        center_y = center_y + (math.sqrt(3) * scale)
        x_shift = 0 if j%2 == 1 else (radius)
        center_x = radius + x_shift + margin_x
    def draw_0():
        points = [(
            center_x + radius * math.sin(2 * math.pi * v / num_vertices),
            center_y + radius * math.cos(2 * math.pi * v / num_vertices)
        ) for v in range(num_vertices)]
        polygon = dwg.polygon(
            points,
            stroke=stroke_color,
            stroke_width=0,
            fill="black",
        )
        dwg.add(polygon)
        points = [(
            center_x + (radius - 0.1) * math.sin(2 * math.pi * v / num_vertices),
            center_y + (radius - 0.1) * math.cos(2 * math.pi * v / num_vertices)
        ) for v in range(num_vertices)]
        polygon = dwg.polygon(
            points,
            stroke=stroke_color,
            stroke_width=0,
            fill="white"
        )
        dwg.add(polygon)
    def draw_1():
        polygon = dwg.polygon(
            [(
                center_x + radius * math.sin(2 * math.pi * v / num_vertices),
                center_y + radius * math.cos(2 * math.pi * v / num_vertices)
            ) for v in range(num_vertices)],
            stroke=stroke_color,
            stroke_width=0,
            fill="black",
        )
        dwg.add(polygon)

    for j in range(tattoo_bit_height):
        for i in range(tattoo_bit_width):
            bit = bits_data.pop()
            if bit == 0:
                draw_0()
            elif bit == 1:
                draw_1()
            else:
                raise RuntimeError()
            shift_bit(i)
        shift_byte(j)
    dwg.save()

def decode():
    bytes_list = []
    i = 0
    while True:
        byte = input("{}> ".format(i)).strip()
        i += 1
        if byte != "":
            while len(byte) < 8:
                byte += input("{}>> ".format(i-1)).strip()
            bytes_list.append(int(byte, 2))
        else:
            break

    if len(bytes_list) % int(128/8) != 0:
        raise RuntimeError(
            "Invalid number of bytes: {} found, multiple of {} expected".format(
                len(bytes_list),
                int(128/8)
            )
        )
    bytes_data = bytes(bytes_list)
    decoded = subprocess.check_output(
        [
            "openssl", "enc", "-d",
            "-aes-128-ecb",
            "-nosalt",
            "-pass", "pass:daddy"
        ],
        input=bytes_data
    )
    print(str(decoded, "utf-8"))

if __name__ == "__main__":
    main()
