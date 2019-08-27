#! /usr/bin/env python3

import math
import base64
import argparse
import random

from collections import namedtuple
from typing import List

import numpy as np
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

from svgwrite import Drawing
from svgwrite.container import Group, Use, Symbol, Style
from svgwrite.pattern import Pattern
from svgwrite.path import Path
from svgwrite.shapes import Polyline, Circle, Rect

from sobol_seq import i4_sobol_generate

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

    ExperimentalTattoo().encode(bits_data)


Point = namedtuple("Point", ("x", "y"))


class ExperimentalTattoo:

    def __init__(self):
        self._define_variables()
        self.dwg = Drawing('tattoo.svg', size=('210mm', '297mm'))
        self.dwg.viewbox(-20, -20, 40, 40)

        self._define_style()
        self._define_dot_pattern()
        self._define_zero_symbol()
        self._define_one_symbol()

    def _define_variables(self):
        self.num_vertices = 6

    def _define_dot_pattern(self):
        # Define pattern for dot work
        dot = Symbol(id="dot")
        dot.add(Circle(center=(0, 0), r=0.5))
        self.dwg.defs.add(dot)
        self.dot_pattern = Pattern((-20, -20), (40, 40), id="dots",
                                   patternUnits="userSpaceOnUse")
        num_dense = 66
        num_light = int(num_dense / 2)
        for i, p in enumerate(
                i4_sobol_generate(2, num_dense) * 40 +
                np.random.rand(num_dense, 2)):
            self.dot_pattern.add(Use(dot.get_iri(), (p[0], p[1]),
                                     class_="dense" if i >= num_light else "dense light"))
        self.dwg.defs.add(self.dot_pattern)

    def _define_zero_symbol(self):
        zero = Symbol(id="zero", class_="bit-0", stroke_width=1, stroke="black", fill="none")
        zero.add(Circle(center=(0, 0), r=20, fill="none", stroke="none"))
        r = 0.75

        for i in range(self.num_vertices):
            vertex = Point(
                20 * math.sin(2 * math.pi * i / self.num_vertices),
                20 * math.cos(2 * math.pi * i / self.num_vertices))

            previous_vertex = Point(
                20 * math.sin(2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices),
                20 * math.cos(2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices))
            start_point = Point(
                (1 - r) * previous_vertex.x + r * vertex.x,
                (1 - r) * previous_vertex.y + r * vertex.y
            )

            next_vertex = Point(
                20 * math.sin(2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices),
                20 * math.cos(2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices))
            end_point = Point(
                (1 - r) * next_vertex.x + r * vertex.x,
                (1 - r) * next_vertex.y + r * vertex.y
            )

            line = Polyline([start_point, vertex, end_point])
            zero.add(line)
        self.dwg.defs.add(zero)

    def _define_one_symbol(self):
        one = Symbol(id="one", class_="bit-1", stroke_width=1, stroke="black")
        one.add(Circle(center=(0, 0), r=20, fill="none", stroke="none"))

        face_symbol = Symbol(id="face")
        points = ["{} {}".format(
            20 * math.sin(2 * math.pi * v / self.num_vertices),
            20 * math.cos(2 * math.pi * v / self.num_vertices)
        ) for v in range(0, 3)]
        data = ['M', "0 0 L", *points, 'Z']
        path = Path(data, fill=self.dot_pattern.get_funciri())
        face_symbol.add(path)
        self.dwg.defs.add(face_symbol)

        classes = [None, "dots-light", "dots-dense"]
        for i in range(0, 3):
            face = Use(face_symbol.get_iri())
            face.rotate(i * 120)
            if classes[i]:
                face.attribs['class'] = classes[i]
            one.add(face)
        self.dwg.defs.add(one)

    def encode(self, bits_data: List[int]):
        test = Use("#one")
        self.dwg.add(test)
        self.dwg.save(pretty=True)


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

        # Define pattern for dot work
        dot = Circle(center=(0, 0), r=0.5, stroke_width=0, fill="none")
        self.dwg.defs.add(dot)
        self.dot_pattern = Pattern((0, 0), (self.bit_size.x, self.bit_size.y),
                                   id="dots")
        num_dense = int(0.66 * self.bit_size.x * self.bit_size.y)
        num_light = int(num_dense / 2)
        for i, p in enumerate(
                i4_sobol_generate(2, num_dense) *
                np.array([self.bit_size.x, self.bit_size.y]) +
                np.random.rand(num_dense, 2)):
            self.dot_pattern.add(Use(dot.get_iri(), (p[0], p[1]),
                                     class_="dense" if i > num_light else "dense light"))
        self.dwg.defs.add(self.dot_pattern)

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

        filling_patterns = [
            ("none", []),
            (self.dot_pattern.get_funciri(), ["dot-light"]),
            (self.dot_pattern.get_funciri(), ["dense"])
        ]
        for i in range(0, 3):
            points = ["{} {}".format(
                self.center.x + self.outside_radius * math.sin(2 * math.pi * v / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(2 * math.pi * v / self.num_vertices)
            ) for v in range(2 * i, 2 * (i + 1) + 1)]
            data = ['M', "{0.x} {0.y}".format(self.center), 'L', *points, 'Z']
            path = Path(data,
                        fill=filling_patterns[i][0],
                        class_=filling_patterns[i][1])
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
                self.center.x + self.outside_radius * math.sin(
                    2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(
                    2 * math.pi * (i + self.num_vertices - 1) / self.num_vertices))
            start_point = Point(
                (1 - r) * previous_point.x + r * mid_point.x,
                (1 - r) * previous_point.y + r * mid_point.y
            )
            next_point = Point(
                self.center.x + self.outside_radius * math.sin(
                    2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices),
                self.center.y + self.outside_radius * math.cos(
                    2 * math.pi * (i + self.num_vertices + 1) / self.num_vertices))
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
                    byte += input("{}>> ".format(i - 1)).strip()
                bytes_list.append(int(byte, 2))
            else:
                break
        except EOFError:
            print("")
            break

    if len(bytes_list) % int(128 / 8) != 0:
        raise RuntimeError(
            "Invalid number of bytes: {} found, multiple of {} expected".format(
                len(bytes_list),
                int(128 / 8)
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
