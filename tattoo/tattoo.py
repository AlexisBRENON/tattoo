#! /usr/bin/env python3

import math
import argparse
import subprocess

from Crypto.Cipher import AES
from Crypto.Hash import HMAC, MD5, SHA256
from Crypto.Protocol.KDF import PBKDF2

import svgwrite

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
        default=u"É♂ 20160222"
    )
    parser.add_argument(
        "--width", "-w",
        help="Tattoo width in mm",
        type=int,
        default=65
    )

    args = parser.parse_args()

    if args.decode:
        decode()
    else:
        text = args.encode
        print("Text to encode: '{}'".format(text))
        encode(text, args.width)

def encode(text, width):
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

    import base64
    print(base64.b64encode(encoding_output))

    # Get binary representation
    str_data = "".join(["{:08b}".format(byte) for byte in list(encoding_output)])
    bits_data = [int(b) for b in str_data]
    bits_data.reverse()

    # Define some tattoo properties
    num_vertices = 6 # Shape of cell (6 = honeycomb, 3 = triangle)
    tattoo_bit_width = 8 # Number of bits per line
    tattoo_bit_height = int(len(bits_data)/tattoo_bit_width) # Number of lines

    # Define some properties of bit representation
    outside_radius = 0.92 # Radius used to draw poligon. With 1 poligons will be tangent
    hole_radius = 0.56
    inside_radius = 0.35
    print("bit radius: ", outside_radius)
    print("hole_radius: ", hole_radius)
    print("inside bit radius: ", inside_radius)

    bit_height = 2 * outside_radius * max([
        math.cos(2 * math.pi * v / num_vertices) for v in range(num_vertices)
        ]) # Height of a bit representation.
    bit_width = 2 * outside_radius * max([
        math.sin(2 * math.pi * v / num_vertices) for v in range(num_vertices)
        ]) # Width of a bit representation
    print("bit height and width: ", bit_height, bit_width)

    tattoo_width = ((tattoo_bit_width + 0.5) * bit_width) # Total width of the tattoo
    print("tattoo width: ", tattoo_width)
    scale = width * 3.78 / tattoo_width # Compute scale to match given width (3.78 is pixels per mm)

    # Scale used values
    outside_radius *= scale
    hole_radius *= scale
    inside_radius *= scale
    bit_height *= scale
    bit_width *= scale

    # Start drawing with margin (just for easy printing)
    margin_x = 3 * bit_width
    margin_y = 3 * bit_height

    dwg = svgwrite.Drawing('tattoo.svg', size=('210mm', '297mm'))

    center_x = margin_x + outside_radius
    center_y = margin_y + outside_radius

    def shift_bit(_):
        nonlocal center_x
        center_x = center_x + (2 * scale)
    def shift_byte(j):
        nonlocal center_y, center_x
        center_y = center_y + (math.sqrt(3) * scale)
        x_shift = 0 if j%2 == 1 else (outside_radius)
        center_x = outside_radius + x_shift + margin_x
    def draw_0():
        polygon = draw_1()
        points = [(
            center_x + hole_radius * math.sin(2 * math.pi * v / num_vertices),
            center_y + hole_radius * math.cos(2 * math.pi * v / num_vertices)
        ) for v in range(num_vertices)]
        polygon.push(['M', points[0], 'L', *points[1:], 'Z'])
        return polygon
    def draw_1():
        points = ["{} {}".format(
            center_x + outside_radius * math.sin(2 * math.pi * v / num_vertices),
            center_y + outside_radius * math.cos(2 * math.pi * v / num_vertices)
        ) for v in range(num_vertices)]
        polygon = svgwrite.path.Path(
            d=['M', points[0], 'L', *points[1:], 'Z'],
            stroke_width=0, fill="black", fill_rule="evenodd")
        return polygon


    for j in range(tattoo_bit_height):
        for i in range(tattoo_bit_width):
            bit = bits_data.pop()
            if bit == 0:
                dwg.add(draw_0())
            elif bit == 1:
                dwg.add(draw_1())
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
