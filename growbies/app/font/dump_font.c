#include <stdio.h>
#include <stdint.h>

#include "/home/meyer/code/growbies/firmware/.pio/libdeps/scale/U8g2/src/clib/u8x8_fonts.c"

int main(void)
{
    fwrite(
        u8x8_font_courR18_2x3_r,
        1,
        sizeof(u8x8_font_courR18_2x3_r),
        stdout);

    return 0;
}
