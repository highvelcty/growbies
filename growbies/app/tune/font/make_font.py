#!/usr/bin/env python3

FIRST_CHAR = 0x20
LAST_CHAR = 0x7e

GLYPH_WIDTH_TILES = 2
GLYPH_HEIGHT_TILES = 3

GLYPH_WIDTH = GLYPH_WIDTH_TILES * 8
GLYPH_HEIGHT = GLYPH_HEIGHT_TILES * 8

GLYPH_SIZE = (
    GLYPH_WIDTH_TILES *
    GLYPH_HEIGHT_TILES *
    8
)

TARGET_CHARS = '0123456789'

INPUT = 'font.bin'
OUTPUT = 'growbies_font_courR18_2x3_r.c'


def glyph_offset(char):
    return 4 + (ord(char) - FIRST_CHAR) * GLYPH_SIZE


def extract_glyph(data, char):
    offset = glyph_offset(char)

    return data[
        offset:offset + GLYPH_SIZE
    ]


def glyph_to_pixels(glyph):
    '''
    Convert a U8x8 glyph into a conventional
    [y][x] pixel array.

    U8x8 stores each 8-byte tile as:

        byte 0 = X column 0
        byte 1 = X column 1
        ...
        byte 7 = X column 7

    Within each byte:

        bit 0 = Y pixel 0
        ...
        bit 7 = Y pixel 7
    '''

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

            for x in range(8):

                byte = glyph[
                    tile_offset + x
                ]

                for y in range(8):

                    if byte & (1 << y):

                        pixels[
                            tile_y * 8 + y
                        ][
                            tile_x * 8 + x
                        ] = True

    return pixels


def pixels_to_glyph(pixels):
    '''
    Convert a conventional [y][x] pixel array
    back into U8x8's column-oriented format.
    '''

    glyph = bytearray(GLYPH_SIZE)

    for tile_y in range(GLYPH_HEIGHT_TILES):
        for tile_x in range(GLYPH_WIDTH_TILES):

            tile_offset = (
                tile_y *
                GLYPH_WIDTH_TILES *
                8 +
                tile_x * 8
            )

            for x in range(8):

                byte = 0

                for y in range(8):

                    if pixels[
                        tile_y * 8 + y
                    ][
                        tile_x * 8 + x
                    ]:
                        byte |= 1 << y

                glyph[
                    tile_offset + x
                ] = byte

    return glyph


def print_glyph(char, glyph):
    '''
    Print a glyph as ASCII art so we can inspect it.
    '''

    pixels = glyph_to_pixels(glyph)

    print()
    print('=' * 40)
    print(f'CHARACTER: {char!r}')
    print('=' * 40)

    for y, row in enumerate(pixels):

        print(
            f'{y:02d} ' +
            ''.join(
                '██' if pixel else '  '
                for pixel in row
            )
        )


def stretch_vertical(glyph):
    '''
    Vertically scale the occupied portion of a glyph
    into rows 2 through 23.

    Rows 0 and 1 are deliberately left blank to provide
    two horizontal pixel lines of space at the top.

    Horizontal geometry is left completely unchanged.
    '''

    source = glyph_to_pixels(glyph)

    occupied_rows = [
        y
        for y in range(GLYPH_HEIGHT)
        if any(source[y])
    ]

    if not occupied_rows:
        return glyph

    top = min(occupied_rows)
    bottom = max(occupied_rows)

    source_height = bottom - top + 1

    target_top = 2
    target_bottom = GLYPH_HEIGHT - 1

    target_height = (
        target_bottom -
        target_top +
        1
    )

    result = [
        [False] * GLYPH_WIDTH
        for _ in range(GLYPH_HEIGHT)
    ]

    # -------------------------------------------------------------------------
    # Map each target row back to the corresponding source row.
    #
    # This is nearest-neighbor scaling. It avoids the previous interpolation
    # calculation's tendency to produce unexpected repeated/skipped rows.
    # -------------------------------------------------------------------------

    for target_y in range(target_height):

        source_y = (
            target_y * source_height
            + target_height // 2
        ) // target_height

        source_y = min(
            source_y,
            source_height - 1
        )

        result[
            target_top + target_y
        ] = source[
            top + source_y
        ].copy()

    return pixels_to_glyph(result)


def make_minus_glyph():
    '''
    Make a clean two-pixel-high minus sign.

    Rows 0 and 1 remain blank, matching the digit glyphs.
    '''

    pixels = [
        [False] * GLYPH_WIDTH
        for _ in range(GLYPH_HEIGHT)
    ]

    y = 12

    for x in range(1, 15):

        pixels[y][x] = True
        pixels[y + 1][x] = True

    return pixels_to_glyph(pixels)


def make_period_glyph():
    '''
    Make a clean four-by-four period near the bottom
    of the glyph cell.

    Rows 0 and 1 remain blank, matching the digit glyphs.
    '''

    pixels = [
        [False] * GLYPH_WIDTH
        for _ in range(GLYPH_HEIGHT)
    ]

    for y in range(19, 23):

        for x in range(6, 10):

            pixels[y][x] = True

    return pixels_to_glyph(pixels)


def format_c(data):
    '''
    Format bytes as concatenated C string literals,
    matching the style of the original font.
    '''

    lines = []

    for offset in range(0, len(data), 24):

        chunk = data[
            offset:offset + 24
        ]

        escaped = []

        for value in chunk:

            if (
                32 <= value <= 126
                and value not in (34, 92)
            ):
                escaped.append(chr(value))
            else:
                escaped.append(
                    f'\\{value:o}'
                )

        lines.append(
            '  "' +
            ''.join(escaped) +
            '"'
        )

    return '\n'.join(lines)


def main():

    with open(INPUT, 'rb') as f:
        data = bytearray(f.read())

    if len(data) != 4564:

        raise RuntimeError(
            f'Expected 4564 bytes, '
            f'got {len(data)}'
        )

    if data[0] != FIRST_CHAR:

        raise RuntimeError(
            f'Unexpected first character: '
            f'{data[0]:#x}'
        )

    if data[1] != LAST_CHAR:

        raise RuntimeError(
            f'Unexpected last character: '
            f'{data[1]:#x}'
        )

    if data[2] != GLYPH_WIDTH_TILES:

        raise RuntimeError(
            f'Unexpected glyph width: '
            f'{data[2]}'
        )

    if data[3] != GLYPH_HEIGHT_TILES:

        raise RuntimeError(
            f'Unexpected glyph height: '
            f'{data[3]}'
        )

    output = bytearray(data)

    # -------------------------------------------------------------------------
    # Digits
    # -------------------------------------------------------------------------

    for char in TARGET_CHARS:

        glyph = extract_glyph(
            data,
            char
        )

        print_glyph(char, glyph)

        new_glyph = stretch_vertical(
            glyph
        )

        offset = glyph_offset(char)

        output[
            offset:offset + GLYPH_SIZE
        ] = new_glyph

    # -------------------------------------------------------------------------
    # Punctuation
    #
    # Do not vertically stretch these. A thin '-' or '.' becomes a filled
    # block when stretched.
    # -------------------------------------------------------------------------

    minus_offset = glyph_offset('-')

    output[
        minus_offset:
        minus_offset + GLYPH_SIZE
    ] = make_minus_glyph()

    period_offset = glyph_offset('.')

    output[
        period_offset:
        period_offset + GLYPH_SIZE
    ] = make_period_glyph()

    # -------------------------------------------------------------------------
    # Write C source
    # -------------------------------------------------------------------------

    with open(OUTPUT, 'w') as f:

        f.write(
            'const uint8_t '
            'growbies_font_courR18_2x3_r[4564] '
            'U8X8_FONT_SECTION('
            '"growbies_font_courR18_2x3_r"'
            ') =\n'
        )

        f.write(
            format_c(output)
        )

        f.write(';\n')

    print()
    print(f'Wrote {OUTPUT}')


if __name__ == '__main__':
    main()