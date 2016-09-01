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

    args = parser.parse_args()

    if args.decode:
        decode()
    else:
        create()

def create():
    encoding_output = subprocess.check_output(
        [
            "openssl", "enc",
            "-aes-128-ecb",
            "-nosalt",
            "-pass", "pass:daddy"
        ],
        input=bytes("Éliam BRENON - 2016-02-22\n", "utf-8")
    )
    str_data = "".join(["{:08b}".format(byte) for byte in list(encoding_output)])

    dwg = svgwrite.Drawing('tattoo.svg')

    nb_lines = int(len(str_data)/16)

    center_y = 0
    center_x = 0
    for j in range(nb_lines):
        for i, bit in enumerate(
                str_data[
                    j*int(len(str_data)/nb_lines):
                    (j+1)*int(len(str_data)/nb_lines)
                ]
        ):
            poly_vertex = 3
            stroke_color = svgwrite.rgb(0, 0, 0)
            stroke_width = 0.1
            fill_color = "none"
            radius = 5
            shift_y = 0 if (j+i)%2 == 0 else (0.5*radius)
            center_x -= radius * math.sin(2 * math.pi * (poly_vertex-1) / poly_vertex)
            dwg.add(
                dwg.polygon(
                    [
                        (
                            center_x + math.pow(-1, (j+i)%2) * radius * math.sin(2 * math.pi * v / poly_vertex),
                            center_y + shift_y + math.pow(-1, (j+i)%2) * radius * math.cos(2 * math.pi * v / poly_vertex)
                        ) for v in range(poly_vertex)
                    ],
                    stroke=stroke_color,
                    stroke_width=stroke_width,
                    fill=fill_color
                )
            )
        center_y += radius*1.5
        center_x = 0

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
