#pragma once

#include <Arduino.h>
#include <vector>

#include "constants.h"

namespace growbies_hf {

    constexpr int HX711_DAC_BITS = 24;
    constexpr int HX711_BIT_BANG_DELAY = 3;

    // The specification says 64uS with SCK high will power down. Double this to be sure.
    //
    // Additional`ly, this is used for power on delay to allow for settling of in rush current
    constexpr int HX711_POWER_DELAY = 64 * 2;
    constexpr int WAIT_READY_RETRY_DELAY_MS = 10;
    constexpr int WAIT_READY_RETRIES = 10;


    /// HX711 driver for a single load cell
    class HX711 {
    public:
        explicit HX711(const uint8_t pd_sck_pin, const uint8_t dout_pin)
            : dout_pin(dout_pin), sck_pin_(pd_sck_pin) {}

        // Power down the HX711
        void power_off() const;

        // Power up the HX711
        void power_on() const;

        uint8_t dout_pin;

    private:
        uint8_t sck_pin_;
    };


    // Multiple HX711s
    class MultiHX711 {
    public:
        // Initialize the devices
        void begin() const;

        void add_hx711(HX711* hx);

        // Power off all devices
        void power_off() const;

        // Power on all devices
        void power_on() const;

        // Read all HX711s and return vector of raw values
        std::vector<int32_t> sample() const;

        std::vector<HX711*> devices;
    private:
        // Internal method to wait until DOUT goes low
        bool wait_ready() const;

        int sck_pin_ = HX711_SCK_PIN;
    };

}  // namespace growbies_hf
