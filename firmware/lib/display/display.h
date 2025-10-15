#ifndef display_h
#define display_h

#include <U8x8lib.h>
#include "constants.h"

class Display {

    public:
        Display():u8x8(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN) {};
        void begin();

        void print_mass(float mass);
		void set_power_save(bool state);

    private:
        static constexpr int default_contrast = 16;

        U8X8_SSD1306_128X32_UNIVISION_HW_I2C u8x8;
};

extern Display* display;

#endif /* display_h */