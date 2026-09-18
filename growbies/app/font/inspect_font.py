#!/usr/bin/env python3

FIRST_CHAR = 0x20
GLYPH_WIDTH_TILES = 2
GLYPH_HEIGHT_TILES = 3

GLYPH_WIDTH = GLYPH_WIDTH_TILES * 8
GLYPH_HEIGHT = GLYPH_HEIGHT_TILES * 8

GLYPH_SIZE = (
    GLYPH_WIDTH_TILES *
    GLYPH_HEIGHT_TILES *
    8
)

TARGET_CHARS = '0123456789.-'


def glyph_offset(char):
    return 4 + (ord(char) - FIRST_CHAR) * GLYPH_SIZE


def extract_glyph(data, char):
    offset = glyph_offset(char)

    return data[
        offset:offset + GLYPH_SIZE
    ]


def glyph_to_pixels(glyph):
    pixels = [
        [False] * GLYPH_WIDTH
        for _ in range(GLYPH_HEIGHT)
    ]

    for tile_y in range(GLYPH_HEIGHT_TILES):
        for tile_x in range(GLYPH_WIDTH_TILES):

            tile_offset = (
                tile_y *
                GLYPH_WIDTH_TILES *
                8 +
                tile_x * 8
            )

            for y in range(8):
                byte = glyph[
                    tile_offset + y
                ]

                for x in range(8):
                    if byte & (1 << x):
                        pixels[
                            tile_y * 8 + y
                        ][
                            tile_x * 8 + x
                        ] = True

    return pixels


def print_glyph(char, glyph):
    pixels = glyph_to_pixels(glyph)

    print()
    print('=' * 40)
    print(f"CHARACTER: {char!r}")
    print('=' * 40)

    for y, row in enumerate(pixels):
        print(
            f'{y:02d} ' +
            ''.join(
                '██' if pixel else '  '
                for pixel in row
            )
        )


def main():
    with open('font.bin', 'rb') as f:
        data = f.read()

    print(f'Font size: {len(data)} bytes')
    print(
        f'Glyph size: {GLYPH_SIZE} bytes '
        f'({GLYPH_WIDTH}x{GLYPH_HEIGHT} pixels)'
    )

    if len(data) != 4564:
        raise RuntimeError(
            f'Expected 4564 bytes, '
            f'got {len(data)}'
        )

    for char in TARGET_CHARS:
        glyph = extract_glyph(data, char)

        if len(glyph) != GLYPH_SIZE:
            raise RuntimeError(
                f'Bad glyph size for {char!r}: '
                f'{len(glyph)}'
            )

        print_glyph(char, glyph)


if __name__ == '__main__':
    main()
