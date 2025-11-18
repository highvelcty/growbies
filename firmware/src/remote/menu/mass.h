#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <cstring>
#include <memory>
#include <Arduino.h>

#include "base.h"
#include "measure/stack.h"
#include "nvm/nvm.h"


// -----------------------------------------------------------------------------
// MassDrawing
// -----------------------------------------------------------------------------
struct MassUnitsMenuLeaf final : BaseStrMenuLeaf {
    MassUnits units{MassUnits::GRAMS};

    explicit  MassUnitsMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 2) {
        _set_msg();
    }

    void on_down() override {
        // Convert to integer for cycling
        uint8_t next = static_cast<uint8_t>(units) + 1;

        // Wrap around if we exceed the last element
        if (next > static_cast<uint8_t>(MassUnits::POUNDS)) {
            next = static_cast<uint8_t>(MassUnits::GRAMS);
        }

        // Update the current unit
        units = static_cast<MassUnits>(next);
    }

    void on_up() override {
        // Convert to integer for cycling
        uint8_t next = static_cast<uint8_t>(units) - 1;

        // Wrap around if we exceed the first element - note the uint8 wraps to 255.
        if (next > static_cast<uint8_t>(MassUnits::POUNDS)) {
            next = static_cast<uint8_t>(MassUnits::POUNDS);
        }

        // Update the current unit
        units = static_cast<MassUnits>(next);
    }

    void on_select() override {
        identify_store->edit().payload.mass_units = units;
        identify_store->commit();
    }

    void synchronize() override {
        units = identify_store->view()->payload.mass_units;
    }

    void draw(const bool selected) override {
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void _set_msg() {
        if (units == MassUnits::GRAMS) {
            msg = "g: grams";
        }
        else if (units == MassUnits::KILOGRAMS) {
            msg = "kg: kilog.";
        }
        else if (units == MassUnits::OUNCES) {
            msg = "oz: ounces";
        }
        else {
            msg = "lb: pounds";
        }
    }
};

struct MassUnitsMenu final : BaseCfgMenu {
    explicit MassUnitsMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Units",
              1,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<MassUnitsMenuLeaf>(display_)
              }) {}
};

struct MassDrawing final : BaseTelemetryDrawing {
    MassUnits units{};
    TareIdx tare_idx{};

    MassDrawing(
        U8X8& display_,
        const TareIdx tare_idx_,
        const float grams_ = 0.0f,
        const MassUnits requested_units_ = MassUnits::GRAMS
    )
        : BaseTelemetryDrawing(
              display_,
              get_tare_name(tare_idx_),
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<MassUnitsMenu>(display_),
              }), tare_idx(tare_idx_)
    {
        _convert_units(grams_, requested_units_);
    }

    void draw(const bool selected) override {
        _set_units_str();
        BaseTelemetryDrawing::draw(selected);
    }

    void synchronize() override {
        units = identify_store->view()->payload.mass_units;
    }

    void update() override {
        const auto& stack = growbies_hf::MeasurementStack::get();
        const auto& new_value = stack.aggregate_mass().total_mass();
        const auto new_units = identify_store->view()->payload.mass_units;

        if (_convert_units(new_value, new_units)) {
            redraw();
        }
        else {
            draw_value();
        }
    }

    bool _convert_units(const float grams, const MassUnits new_units) {
        float converted_mass = grams - tare_store->payload()->tares[tare_idx].value;
        MassUnits converted_units = new_units;

        constexpr float GRAMS_PER_KG = 1000.0f;
        constexpr float GRAMS_PER_OZ = 28.3495f;
        constexpr float OUNCES_PER_LB = 16.0f;

        // ReSharper disable CppTooWideScope
        constexpr float MAX_ZERO_PRECISION   = 9999999;
        constexpr float MIN_ZERO_PRECISION   = -999999;
        constexpr float MAX_SINGLE_PRECISION = 99999.9;
        constexpr float MIN_SINGLE_PRECISION = -9999.9;
        constexpr float MAX_DOUBLE_PRECISION = 9999.99;
        constexpr float MIN_DOUBLE_PRECISION = -999.99;
        constexpr float MAX_TRIPLE_PRECISION = 99999.9;
        constexpr float MIN_TRIPLE_PRECISION = -9999.9;
        // ReSharper restore CppTooWideScope

        // Unit conversion
        switch (converted_units) {
            case MassUnits::GRAMS: break;
            case MassUnits::KILOGRAMS: converted_mass /= GRAMS_PER_KG; break;
            case MassUnits::OUNCES: converted_mass /= GRAMS_PER_OZ; break;
            case MassUnits::POUNDS: converted_mass /= (GRAMS_PER_OZ * OUNCES_PER_LB); break;
        }

        // Precision by units
        int precision = 0;
        switch (converted_units) {
            case MassUnits::GRAMS: {
                precision = 1;
                if (converted_mass > MAX_SINGLE_PRECISION ||
                    converted_mass < MIN_SINGLE_PRECISION) {
                    converted_units = MassUnits::KILOGRAMS;
                    converted_mass /= GRAMS_PER_KG;
                }
                else {
                    break;
                }
            }
            case MassUnits::OUNCES: {
                precision = 2;
                if (converted_mass > MAX_DOUBLE_PRECISION ||
                    converted_mass < MIN_DOUBLE_PRECISION) {
                    converted_units = MassUnits::POUNDS;
                    converted_mass /= OUNCES_PER_LB;
                }
                else {
                    break;
                }
            }
            case MassUnits::POUNDS:
            case MassUnits::KILOGRAMS: {
                precision = 3;
                if (converted_mass > MAX_TRIPLE_PRECISION ||
                    converted_mass < MIN_TRIPLE_PRECISION) {
                    precision = 2;
                }
                else if (converted_mass > MAX_DOUBLE_PRECISION ||
                         converted_mass < MIN_DOUBLE_PRECISION) {
                    precision = 1;
                }
                else if (converted_mass > MAX_SINGLE_PRECISION ||
                         converted_mass < MIN_SINGLE_PRECISION) {
                    precision = 0;
                    if (converted_mass > MAX_ZERO_PRECISION) {
                        converted_mass = MAX_ZERO_PRECISION;
                    }
                    else if (converted_mass < MIN_ZERO_PRECISION) {
                        converted_mass = MIN_ZERO_PRECISION;
                    }
                }
                break;
            }
        }

        dtostrf(converted_mass, VALUE_CHARS, precision, value_str);
        value_str[VALUE_CHARS] = '\0';

        bool redraw = false;
        if (units != converted_units) {
            redraw = true;
            units = converted_units;
        }

        return redraw;
    }

    void _set_units_str() {
        switch (units) {
            case MassUnits::GRAMS: strncpy(units_str, "g", UNITS_CHARS); break;
            case MassUnits::KILOGRAMS: strncpy(units_str, "kg", UNITS_CHARS); break;
            case MassUnits::OUNCES: strncpy(units_str, "oz", UNITS_CHARS); break;
            case MassUnits::POUNDS: strncpy(units_str, "lb", UNITS_CHARS); break;
        }
        units_str[UNITS_CHARS] = '\0';
    }
};

