#include "hx711.h"
#include <Arduino.h>

#include "build_cfg.h"
#include "constants.h"
#include "flags.h"

namespace growbies_hf {

// ---------------- HX711 ----------------
void HX711::power_off() {
    digitalWrite(HX711_SCK_PIN, HIGH);
}

void HX711::power_on() {
    digitalWrite(HX711_SCK_PIN, LOW);
}

// ---------------- MultiHX711 ----------------

void MultiHX711::begin() {
    pinMode(HX711_SCK_PIN, OUTPUT);


    for (size_t ii = 0; ii < MASS_SENSOR_COUNT; ++ii) {
        add_device(new HX711(get_HX711_dout_pin(ii)));
    }

    for (const auto device : devices) {
#if ARDUINO_ARCH_AVR
        pinMode(device->dout_pin, INPUT_PULLUP);
#elif ARDUINO_ARCH_ESP32
        gpio_config_t io_conf;
        io_conf.intr_type = GPIO_INTR_DISABLE;
        io_conf.mode = GPIO_MODE_INPUT;
        io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
        io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
        io_conf.pin_bit_mask = (1ULL << device->dout_pin);
        gpio_config(&io_conf);
#endif
    }

#if POWER_CONTROL
    power_off();
#endif
}

void MultiHX711::add_device(HX711* hx) {
    if (hx) devices.push_back(hx);
}

void MultiHX711::power_off() const {
    for (const auto* hx : devices) {
        if (hx) HX711::power_off();
    }
    delayMicroseconds(HX711_POWER_DELAY);
}

void MultiHX711::power_on() const {
    for (const auto* hx : devices) {
        if (hx) HX711::power_on();
    }
    delayMicroseconds(HX711_POWER_DELAY);
}

std::vector<int32_t> MultiHX711::sample() const{
    std::vector<int32_t> readings(devices.size(), 0);
    readings.reserve(devices.size());

#if ARDUINO_ARCH_AVR
    uint8_t gpio_in_reg = 0;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg = 0;
#endif

    // Read bit by bit in parallel. Most significant bit first.
    for (uint8_t ii = 0; ii < HX711_DAC_BITS; ++ii) {
        delayMicroseconds(HX711_BIT_BANG_DELAY);
        digitalWrite(HX711_SCK_PIN, HIGH);

        {
            // This is a time critical block
            delayMicroseconds(HX711_BIT_BANG_DELAY);
#if ARDUINO_ARCH_AVR
            // Read pins 8-13
            gpio_in_reg = PINB;
#elif ARDUINO_ARCH_ESP32
            gpio_in_reg = REG_READ(GPIO_IN_REG);
#endif
            digitalWrite(HX711_SCK_PIN, LOW);
        }

        // Shift bits into each HX711 reading
        // This time intensive task needs to happen after pulling SCK low to not perturb time
        // sensitive section when SCK is high.
        for (size_t jj = 0; jj < devices.size(); ++jj) {
            const bool a_bit = static_cast<bool>(gpio_in_reg & get_HX711_dout_port_bit(jj));
            readings[jj] = (readings[jj] << 1) | static_cast<int32_t>(a_bit);
        }

    }

    // Set gain for next reading (channel A, 128x gain)
    for (uint8_t gg = 0; gg < 3; ++gg) {
        delayMicroseconds(HX711_BIT_BANG_DELAY);
        digitalWrite(HX711_SCK_PIN, HIGH);
        delayMicroseconds(HX711_BIT_BANG_DELAY);
        digitalWrite(HX711_SCK_PIN, LOW);
    }

    return readings;
}

bool MultiHX711::wait_ready() const {
    bool ready;
#if ARDUINO_ARCH_AVR
    uint8_t gpio_in_reg;
#elif ARDUINO_ARCH_ESP32
    uint32_t gpio_in_reg;
#endif
    bool all_ready = false;
    int retry_count = 0;

    do {
        // Check for readiness from all sensors
        // Read pins 8-13
#if ARDUINO_ARCH_AVR
        gpio_in_reg = PINB;
#elif ARDUINO_ARCH_ESP32
        gpio_in_reg = REG_READ(GPIO_IN_REG);
#endif
        all_ready = true;
        for (size_t jj = 0; jj < devices.size(); ++jj) {
            ready = static_cast<bool>(gpio_in_reg & get_HX711_dout_port_bit(jj)) == LOW;
            all_ready &= ready;
        }

        if (!all_ready){
            ++retry_count;
            delay(WAIT_READY_RETRY_DELAY_MS);
        }

    } while ((retry_count <= WAIT_READY_RETRIES) && (!all_ready));

    return all_ready;
}

}  // namespace growbies_hf
