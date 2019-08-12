#! /usr/bin/env python3

import math
import base64
import argparse

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from collections import namedtuple

from svgwrite import Drawing
from svgwrite.container import Group
from svgwrite.path import Path
from svgwrite.shapes import Polyline
from typing import Sequence, List

import pkcs7


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decode", '-d',
        action="store_true"
    )
    parser.add_argument(
        "--encode", '-e',
        type=str,
        default=u"L♂ 20190807"
    )
    args = parser.parse_args()

    if args.decode:
        decode()
    else:
        text = args.encode
        print("Text to encode: '{}'".format(text))
        encode(text)


def encode(text):
    # Derive key
    password = b"daddy"
    block_size = 16
    md = SHA256.new(password)
    key = md.digest()[0:block_size]
    print("key=" + "".join(["{:02X}".format(b) for b in key]))

    # Compute ciphered message
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pkcs7.pad(bytes(text, "utf-8"), block_size))
    encoding_output = encrypted

    print(base64.b64encode(encoding_output))

    # Get binary representation
    str_data = "".join(["{:08b}".format(byte) for byte in list(encoding_output)])
    bits_data = [int(b) for b in str_data]
    bits_data.reverse()

    print(bits_data)

    Tattoo().encode(bits_data)


Point = namedtuple("Point", ("x", "y"))


class Tattoo:
    def __init__(self):
        millimeter_width = 65
        self.tattoo_bit_width = 8  # Number of bits per line
        self.num_vertices = 6
        self.outside_radius = 1.15  # Radius used to draw polygon. With 1 polygons will be tangent

        bit_height = 2 * self.outside_radius * max([
            math.cos(2 * math.pi * v / self.num_vertices) for v in range(self.num_vertices)
        ])  # Height of a bit representation.
        bit_width = 2 * self.outside_radius * max([
            math.sin(2 * math.pi * v / self.num_vertices) for v in range(self.num_vertices)
        ])  # Width of a bit representation
        self.bit_size = Point(
            bit_width, bit_height
        )

        tattoo_width = ((self.tattoo_bit_width + 0.5) * self.bit_size.x)  # Total width of the tattoo
        # Compute scale to match given width (3.78 is pixels per mm)
        self.scale = millimeter_width * 3.78 / tattoo_width

        # Scale used values
        self.outside_radius *= self.scale
        self.bit_size = Point(
            bit_height * self.scale,
            bit_width * self.scale
        )

        # Start drawing with margin (just for easy printing)
        self.margin = Point(3 * bit_width, 3 * bit_height)

        self.dwg = Drawing('tattoo.svg', size=('210mm', '297mm'))

        self.center = Point(
            self.margin.x + self.scale,
            self.margin.y + self.outside_radius)

    def encode(self, bits_data: List[int]):
        tattoo_bit_height = int(len(bits_data) / self.tattoo_bit_width)
        for j in range(tattoo_bit_height):
            for i in range(self.tattoo_bit_width):
                bit = bits_data.pop()
                if bit == 0:
                    self.draw0()
                elif bit == 1:
                    self.draw1()
                else:
                    raise RuntimeError()
                self.shift_bit()
            self.shift_byte(j)
        self.dwg.save()

    def shift_bit(self):
        self.center = Point(
            self.center.x + (2 * self.scale),
            self.center.y
        )

    def shift_byte(self, j):
        x_shift = 0 if j % 2 == 1 else self.scale
        self.center = Point(
            self.margin.x + self.scale + x_shift,
            self.center.y + (math.sqrt(3) * self.scale)
        )

    def draw1(self):
        group = Group(
            class_="bit-1",
            stroke_width=1, stroke="black"
        )

        for i in range(0, 3):
            points = ["{} {}".format(
                self.center.x + self.outside_radius * math.sin(2 * math.pi * v / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(2 * math.pi * v / self.num_vertices)
            ) for v in range(2 * i, 2 * (i + 1) + 1)]
            data = ['M', "{0.x} {0.y}".format(self.center), 'L', *points, 'Z']
            path = Path(data,
                        fill="rgb({0}, {0}, {0})".format(255 - 48 * (i + 1)))
            group.add(path)
        self.dwg.add(group)

    def draw0(self):
        group = Group(
            class_="bit-0",
            stroke_width=1, stroke="black",
            fill="none"
        )

        r = 0.75

        for i in range(self.num_vertices):
            mid_point = Point(
                self.center.x + self.outside_radius * math.sin(2 * math.pi * i / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(2 * math.pi * i / self.num_vertices))
            previous_point = Point(
                self.center.x + self.outside_radius * math.sin(2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices))
            start_point = Point(
                (1 - r) * previous_point.x + r * mid_point.x,
                (1 - r) * previous_point.y + r * mid_point.y
            )
            next_point = Point(
                self.center.x + self.outside_radius * math.sin(2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices))
            end_point = Point(
                (1 - r) * next_point.x + r * mid_point.x,
                (1 - r) * next_point.y + r * mid_point.y
            )
            line = Polyline([start_point, mid_point, end_point])
            group.add(line)
        self.dwg.add(group)


def decode():
    bytes_list = []
    i = 0
    while True:
        try:
            byte = input("{}> ".format(i)).strip()
            i += 1
            if byte != "":
                while len(byte) < 8:
                    byte += input("{}>> ".format(i-1)).strip()
                bytes_list.append(int(byte, 2))
            else:
                break
        except EOFError:
            print("")
            break

    if len(bytes_list) % int(128/8) != 0:
        raise RuntimeError(
            "Invalid number of bytes: {} found, multiple of {} expected".format(
                len(bytes_list),
                int(128/8)
            )
        )
    bytes_data = bytes(bytes_list)

    password = b"daddy"
    block_size = 16
    md = SHA256.new(password)
    key = md.digest()[0:block_size]
    print("key=" + "".join(["{:02X}".format(b) for b in key]))

    # Decrypt and unpad bytes
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(bytes_data)
    decoded = pkcs7.unpad(decrypted, block_size)
    print(str(decoded, "utf-8"))


if __name__ == "__main__":
    main()
