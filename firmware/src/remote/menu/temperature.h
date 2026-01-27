#pragma once

#include <U8x8lib.h>
#include <cstdio>
#include <cstring>
#include <Arduino.h>

#include "base.h"
#include "measure/stack.h"
#include "nvm/nvm.h"


// -----------------------------------------------------------------------------
// TemperatureDrawing
// -----------------------------------------------------------------------------
struct TemperatureUnitsMenuLeaf final : BaseStrMenuLeaf {
    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit TemperatureUnitsMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 2) {
        _set_msg();
    }

    void on_down() override {
        on_up();
    }

    void on_up() override {
        if (units == TemperatureUnits::CELSIUS) {
            units = TemperatureUnits::FAHRENHEIT;
        }
        else {
            units = TemperatureUnits::CELSIUS;
        }
    }

    void on_select() override {
        identify_store->edit().payload.temperature_units = units;
        identify_store->commit();
    }

    void synchronize() override {
        units = identify_store->view()->payload.temperature_units;
    }

    void draw(const bool selected) override {
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void _set_msg() {
        if (units == TemperatureUnits::FAHRENHEIT) {
            msg = "F: Fahren.";
        }
        else {
            msg = "C: Celsius";
        }
    }
};

struct TemperatureUnitsMenu final : BaseCfgMenu {
    explicit TemperatureUnitsMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Units",
              1,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<TemperatureUnitsMenuLeaf>(display_),
              }) {}
};

struct TemperatureDrawing final : BaseTelemetryDrawing {
    TemperatureUnits units{};

    TemperatureDrawing(
        U8X8& display_,
        const char* msg_,
        const float celsius_ = 0.0f,
        const TemperatureUnits requested_units_ = TemperatureUnits::CELSIUS
        )
            : BaseTelemetryDrawing(
                display_,
                msg_,
                std::vector<std::shared_ptr<BaseMenu>>{
                    std::make_shared<TemperatureUnitsMenu>(display_),
            })
    {
        _convert_units(celsius_, requested_units_);
    }

    void draw(const bool selected) override {
        _set_units_str();
        BaseTelemetryDrawing::draw(selected);
    }

    void synchronize() override {
        units = identify_store->view()->payload.temperature_units;
    }

    void update() override {
        const auto& measurement_stack = growbies_hf::MeasurementStack::get();
        measurement_stack.update();
        const auto& new_value = measurement_stack.aggregate_temp().average();
        const auto new_units = identify_store->view()->payload.temperature_units;

        if (_convert_units(new_value, new_units)) {
            redraw();
        }
        else {
            draw_value();
        }
    }

    bool _convert_units(const float celsius, const TemperatureUnits new_units) {
        float temp = celsius;
        if (new_units == TemperatureUnits::FAHRENHEIT) {
            temp = (celsius * 9.0f / 5.0f) + 32.0f;
        }

        if (temp > 999.9f) temp = 999.9f;
        if (temp < -99.9f) temp = -99.9f;

        dtostrf(temp, VALUE_CHARS, 1, value_str);
        value_str[VALUE_CHARS] = '\0';

        switch (new_units) {
            case TemperatureUnits::CELSIUS: strncpy(units_str, "*C", UNITS_CHARS); break;
            case TemperatureUnits::FAHRENHEIT: strncpy(units_str, "*F", UNITS_CHARS); break;
        }
        units_str[UNITS_CHARS] = '\0';

        bool redraw = false;
        if (units != new_units) {
            redraw = true;
            units = new_units;
        }

        return redraw;
    }

    void _set_units_str() {
        if (units == TemperatureUnits::FAHRENHEIT) {
            strncpy(units_str, "*F", UNITS_CHARS);
        }
        else {
            strncpy(units_str, "*C", UNITS_CHARS);
        }
        units_str[UNITS_CHARS] = '\0';
    }
};

