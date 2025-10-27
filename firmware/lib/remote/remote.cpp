#include "constants.h"
#include <nvm.h>
#include "remote.h"

// Define static instance pointer
Remote* Remote::instance = nullptr;

// Application-wide singleton accessor
Remote& Remote::get() {
    static Remote singleton;
    return singleton;
}

Remote::Remote()
    : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN)
{
    // Makes member data accessible via ISR
    instance = this;
}

void Remote::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();

    // Configure wake pin and attach ISR
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), Remote::wakeISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), Remote::wakeISR1, RISING);

    display.clear();
    display.setFlipMode(identify_store->payload()->flip);
    display.setFont(u8x8_font_chroma48medium8_r);
    display.drawString(0, 0, "emey emey emey");

    // display.drawString(0, 0, "emey emey emey");


    // draw(ConfigurationDrawing{});

}

void Remote::draw(const Drawing& drawing) {
    constexpr size_t num_bytes = sizeof(drawing);
    auto* ptr = reinterpret_cast<const uint8_t*>(&drawing);
    auto* base_ptr = ptr;


    display.setFont(u8x8_font_chroma48medium8_r);

    while (ptr - base_ptr <= num_bytes) {
        auto* hdr = reinterpret_cast<const DrawingHdr*>(ptr);

        ptr += sizeof(*hdr);

        // Resolve drawing method
        std::function<void(uint8_t, uint8_t, const char*)> draw_func;
        if (hdr->width == 1 and hdr->height == 2) {
            draw_func = [&](const uint8_t x, const uint8_t y, const char* msg) {
                display.draw1x2String(x, y, msg);
            };
        }
        else {
            draw_func = [&](const uint8_t x, const uint8_t y, const char* msg) {
                display.drawString(x, y, msg);
            };
        }

        // Resolve font
        if (hdr->width == 2) {
            display.setFont(u8x8_font_px437wyse700a_2x2_r);
        }
        else if (hdr->width == 3) {
            display.setFont(u8x8_font_courR18_2x3_r);
        }
        else {
            display.setFont(u8x8_font_chroma48medium8_r);
        }

        // Draw
        display.clear();
        if (hdr->type == DrawType::TEXT) {
            const auto msg = *reinterpret_cast<const char* const*>(ptr);
            ptr += strlen(msg) + 1;
            draw_func(hdr->x, hdr->y, msg);
        }
        else if (hdr->type == DrawType::FLOAT) {
            const auto grams = *reinterpret_cast<const float*>(ptr);
            ptr += sizeof(grams);
            const auto mass_display = format_mass(grams, MassUnits::GRAMS);
            draw_func(hdr->x, hdr->y, mass_display.str);
            if (mass_display.units == MassUnits::GRAMS) {
                display.drawString(15, 3, "g");
            }
            else if (mass_display.units == MassUnits::KILOGRAMS) {
                display.drawString(15, 3, "kg");
            }
            else if (mass_display.units == MassUnits::OUNCES) {
                display.drawString(15, 3, "oz");
            }
            else if (mass_display.units == MassUnits::POUNDS) {
                display.drawString(15, 3, "lb");
            }
        }
    }
}

void Remote::draw_mass(const float grams, const TareIdx tare_idx) {
    const auto mass_display = format_mass(grams, MassUnits::GRAMS);
    if (mass_display.units == MassUnits::GRAMS) {
        display.drawString(15, 3, "g");
    }
    else if (mass_display.units == MassUnits::KILOGRAMS) {
        display.drawString(15, 3, "kg");
    }
    else if (mass_display.units == MassUnits::OUNCES) {
        display.drawString(15, 3, "oz");
    }
    else if (mass_display.units == MassUnits::POUNDS) {
        display.drawString(15, 3, "lb");
    }
    // auto drawing = TelemetryDrawing(get_tare_name(tare_idx), grams, )

}

void Remote::print_mass(const float mass) {
    char buf[8];
    dtostrf(mass, 6, 1, buf);
    this->display.setFont(u8x8_font_px437wyse700a_2x2_r);
    this->display.draw1x2String(0, 0, buf);
    this->display.setFont(u8x8_font_chroma48medium8_r);
    this->display.draw1x2String(15, 2, "g");
}

bool Remote::service() {
    bool button_pressed = false;
    if (last_button_pressed != EVENT::NONE) {
        const unsigned long now = millis();

        if (now - debounce_time >= BUTTON_DEBOUNCE_MS) {
            display.clearDisplay();
            if (last_button_pressed == EVENT::SELECT) {
                display.draw1x2String(0, 0, "Select");
            }
            else if (last_button_pressed == EVENT::DIRECTION_0) {
                display.draw1x2String(0, 0, "Direction 0");
            }
            else if (last_button_pressed == EVENT::DIRECTION_1) {
                display.draw1x2String(0, 0, "Direction 1");
            }
            button_pressed = true;
            debounce_time = now;
            last_button_pressed = EVENT::NONE;
        }
    }

    if (!digitalRead(BUTTON_0_PIN) and !digitalRead(BUTTON_1_PIN)) {
        arm_isr = true;
    }
    else {
        arm_isr = false;
    }

    return button_pressed;
}

void Remote::set_flip(const bool flip) {
    display.setFlipMode(flip);
    display.refreshDisplay();
}

void IRAM_ATTR Remote::wakeISR0() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_1_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_0_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::SELECT;
    }
}

void IRAM_ATTR Remote::wakeISR1() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_0_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_1_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::DIRECTION_0;
    }
}