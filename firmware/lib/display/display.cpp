#include "display.h"

Display* display = new Display();

void Display::begin() {
    this->u8x8.begin();
    this->u8x8.setContrast(this->default_contrast);
}

void Display::print_mass(const float mass) {
    char buf[8];
    dtostrf(mass, 6, 1, buf);
    this->u8x8.setFont(u8x8_font_px437wyse700a_2x2_r);
    this->u8x8.draw1x2String(0, 0, buf);
    this->u8x8.setFont(u8x8_font_chroma48medium8_r);
    this->u8x8.draw1x2String(15, 2, "g");
}
