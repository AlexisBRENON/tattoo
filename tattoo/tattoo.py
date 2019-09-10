#! /usr/bin/env python3

import math
import base64
import argparse

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
Dimensions = namedtuple("Style", ("stroke_width", "bit_radius"))


class Polygon:
    def __init__(self, num_vertices: int):
        self.num_vertices = num_vertices
        self.T_deg = 180 / num_vertices
        self.T_rad = math.radians(self.T_deg)
        self.outer_circle_radius = 1 / (2 * math.sin(math.pi / num_vertices))
        self.apotheme = self.outer_circle_radius * math.cos(self.T_rad)
        self.inner_circle_radius = self.apotheme


class ExperimentalTattoo:

    def __init__(self):
        self._define_variables()
        self.dwg = Drawing('tattoo.svg', size=('210mm', '297mm'))

        self._define_zero_symbol()
        self._define_one_symbol()

    def _define_variables(self):
        self.poly = Polygon(6)
        self.dimens = Dimensions(1, 20)

    def _define_zero_symbol(self):
        zero = Symbol(id="zero", class_="bit-0", stroke_width=1, stroke="black", fill="none")
        zero.add(Circle(center=(0, 0), r=self.dimens.bit_radius, fill="none", stroke="none"))
        r = 0.75

        n = self.poly.num_vertices
        for i in range(n):
            vertex = Point(
                self.dimens.bit_radius * math.sin(2 * math.pi * i / n),
                self.dimens.bit_radius * math.cos(2 * math.pi * i / n))

            previous_vertex = Point(
                self.dimens.bit_radius * math.sin(2 * math.pi * (i + n - 1) / n),
                self.dimens.bit_radius * math.cos(2 * math.pi * (i + n - 1) / n))
            start_point = Point(
                (1 - r) * previous_vertex.x + r * vertex.x,
                (1 - r) * previous_vertex.y + r * vertex.y
            )

            next_vertex = Point(
                self.dimens.bit_radius * math.sin(2 * math.pi * (i + n + 1) / n),
                self.dimens.bit_radius * math.cos(2 * math.pi * (i + n + 1) / n))
            end_point = Point(
                (1 - r) * next_vertex.x + r * vertex.x,
                (1 - r) * next_vertex.y + r * vertex.y
            )

            line = Polyline([start_point, vertex, end_point], stroke_linejoin="bevel")
            zero.add(line)
        self.dwg.defs.add(zero)

    def _define_one_symbol(self):
        dot = Symbol(id="dot")
        dot.add(Circle(center=(0, 0), r=self.dimens.stroke_width * 0.4, fill="black", stroke="none"))
        self.dwg.defs.add(dot)

        one = Symbol(id="one", class_="bit-1", stroke_width=1, stroke="black")
        one.add(Circle(center=(0, 0), r=self.dimens.bit_radius, fill="none", stroke="none"))

        empty_face_symbol = Symbol(id="empty_face")
        light_face_symbol = Symbol(id="light_face")
        dense_face_symbol = Symbol(id="dense_face")

        points = ["{} {}".format(
            self.dimens.bit_radius * math.sin(2 * math.pi * v / self.poly.num_vertices),
            self.dimens.bit_radius * math.cos(2 * math.pi * v / self.poly.num_vertices)
        ) for v in range(0, 3)]
        data = ['M', "0 0 L", *points, 'Z']

        path = Path(data, fill="none", stroke_linejoin="bevel")
        empty_face_symbol.add(path)
        light_face_symbol.add(path)
        dense_face_symbol.add(path)

        x0 = 0
        x1 = self.dimens.bit_radius * math.sin(2 * math.pi * 2 / self.poly.num_vertices)
        y0 = self.dimens.bit_radius * math.cos(2 * math.pi * 2 / self.poly.num_vertices)
        y1 = self.poly.outer_circle_radius * self.dimens.bit_radius
        w = x1 - x0
        h = y1 - y0
        h_rect = y1

        num_dense = 200
        num_light = int(num_dense / 2)
        points = np.apply_along_axis(
            lambda p: np.array([p[0] * w, p[1] * h_rect + p[0] * y0]),
            1,
            np.clip(
                i4_sobol_generate(2, num_dense) + np.random.rand(num_dense, 2) / h,
                0, 1
            ))
        for p in points[:num_light]:
            light_face_symbol.add(Use(dot.get_iri(), (p[0], p[1])))
            dense_face_symbol.add(Use(dot.get_iri(), (p[0], p[1])))
        for p in points[num_light:]:
            dense_face_symbol.add(Use(dot.get_iri(), (p[0], p[1])))
        self.dwg.defs.add(empty_face_symbol)
        self.dwg.defs.add(light_face_symbol)
        self.dwg.defs.add(dense_face_symbol)

        f1 = Use(empty_face_symbol.get_iri())
        one.add(f1)
        f2 = Use(dense_face_symbol.get_iri())
        f2.rotate(120)
        one.add(f2)
        f3 = Use(light_face_symbol.get_iri())
        f3.rotate(240)
        one.add(f3)
        self.dwg.defs.add(one)

    def encode(self, bits_data: List[int]):
        tattoo_bit_height = int(len(bits_data) / 8)
        x, y = 0, 0
        xmin, xmax = 0, 0
        ymin, ymax = 0, 0
        tattoo = Group(id="tattoo")
        for j in range(tattoo_bit_height):
            for i in range(8):
                if x > xmax:
                    xmax = x
                if y > ymax:
                    ymax = y
                bit = bits_data.pop()
                if bit == 0:
                    tattoo.add(Use("#zero", (x, y)))
                elif bit == 1:
                    tattoo.add(Use("#one", (x, y)))
                else:
                    raise RuntimeError()
                x, y = self.shift_bit(x, y)
            x, y = self.shift_byte(j, y)

        xmax += self.poly.inner_circle_radius * self.dimens.bit_radius * 2
        ymax += self.poly.outer_circle_radius * self.dimens.bit_radius * 2
        tattoo_width = xmax - xmin
        tattoo_height = ymax - ymin
        scaled_width_mm = 65
        scale_factor = scaled_width_mm * 3.78 / tattoo_width
        scaled_height_mm = tattoo_height * scale_factor / 3.78
        tattoo.scale(scale_factor)
        tattoo.translate(
            3.78 * (210 - scaled_width_mm) / 2,
            3.78 * (297 - scaled_height_mm) / 2
        )
        self.dwg.add(tattoo)
        self.dwg.save(pretty=True)

    def shift_bit(self, x, y):
        return x + 2 * self.poly.inner_circle_radius * self.dimens.bit_radius, y

    def shift_byte(self, j, y):
        return (
            0 if j % 2 == 1 else self.poly.inner_circle_radius * self.dimens.bit_radius,
            y + (math.sqrt(3) * self.poly.inner_circle_radius * self.dimens.bit_radius)
        )


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
