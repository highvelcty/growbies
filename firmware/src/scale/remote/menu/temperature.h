#pragma once

#include <U8x8lib.h>
#include <cstring>
#include <Arduino.h>

#include "base.h"
#include "scale/measure/stack.h"
#include "scale/nvm/nvm.h"


struct TemperatureUnitsMenuLeaf final : BaseStrMenuLeaf {
    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit TemperatureUnitsMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 2) {}

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
        set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void set_msg() override {
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

struct BaseTemperatureDrawing : BaseTelemetryDrawing {
    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit BaseTemperatureDrawing(
        U8X8& display_,
        const char* msg_,
        const TelemetryDrawingFormat format_ =
            TelemetryDrawingFormat::STANDARD,
        std::vector<std::shared_ptr<BaseMenu>> _children = {}
    )
        : BaseTelemetryDrawing(
            display_,
            msg_,
            format_,
            std::move(_children))
    {}

    void draw(const bool selected) override {
        _set_units_str();
        BaseTelemetryDrawing::draw(selected);
    }

    void synchronize() override {
        units = identify_store->view()->payload.temperature_units;
    }

    bool set_temperature(const float celsius) {
        const auto new_units = identify_store->view()->payload.temperature_units;
        return _convert_units(celsius, new_units);
    }

    bool _convert_units(
        const float celsius,
        const TemperatureUnits new_units
    ) {
        float temp = celsius;

        if (new_units == TemperatureUnits::FAHRENHEIT) {
            temp = (celsius * 9.0f / 5.0f) + 32.0f;
        }

        if (temp > 999.9f) temp = 999.9f;
        if (temp < -99.9f) temp = -99.9f;

        dtostrf(temp, VALUE_CHARS, 1, value_str);
        value_str[VALUE_CHARS] = '\0';

        switch (new_units) {
            case TemperatureUnits::CELSIUS:
                strncpy(units_str, "*C", UNITS_CHARS);
                break;

            case TemperatureUnits::FAHRENHEIT:
                strncpy(units_str, "*F", UNITS_CHARS);
                break;
        }

        units_str[UNITS_CHARS] = '\0';

        bool redraw = false;

        if (units != new_units) {
            units = new_units;
            redraw = true;
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

struct ThermistorDrawing final : BaseTemperatureDrawing {
    const uint8_t sensor;

    ThermistorDrawing(
        U8X8& display_,
        const char* msg_,
        const uint8_t sensor_,
        const float celsius_ = 0.0f,
        const TemperatureUnits requested_units_ =
            TemperatureUnits::CELSIUS
    )
        : BaseTemperatureDrawing(
            display_,
            msg_,
            TelemetryDrawingFormat::BOTTOM_TWO_LINES,
            std::vector<std::shared_ptr<BaseMenu>>{})
        , sensor(sensor_)
    {
        _convert_units(celsius_, requested_units_);
    }

    void update() override {
        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const auto new_value =
            measurement_stack.aggregate_temp().sensor_temperatures()[sensor];

        set_temperature(new_value);
        draw_value();
    }
};


struct ThermistorMenu final : BaseCfgMenu {
    ThermistorDrawing leaf;

    static const char* name(const uint8_t sensor_) {
        switch (sensor_) {
            case 0: return "Thermistor 0";
            case 1: return "Thermistor 1";
            case 2: return "Thermistor 2";
            default: return "Thermistor";
        }
    }

    explicit ThermistorMenu(
        U8X8& display_,
        const uint8_t sensor_
    )
        : BaseCfgMenu(
            display_,
            name(sensor_),
            1,
            std::vector<std::shared_ptr<BaseMenu>>{}
        ),
        leaf(
            display_,
            "",
            sensor_
        )
    {}

    void update() override {
        leaf.update();
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);
        leaf.draw(false);
    }
};

struct TemperatureDrawing final : BaseTemperatureDrawing {
    TemperatureDrawing(
        U8X8& display_,
        const char* msg_,
        const float celsius_ = 0.0f,
        const TemperatureUnits requested_units_ =
            TemperatureUnits::CELSIUS
    )
        : BaseTemperatureDrawing(
            display_,
            msg_,
            TelemetryDrawingFormat::STANDARD,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<TemperatureUnitsMenu>(display_),
                std::make_shared<ThermistorMenu>(display_, 0),
                std::make_shared<ThermistorMenu>(display_, 1),
                std::make_shared<ThermistorMenu>(display_, 2),
            })
    {
        _convert_units(celsius_, requested_units_);
    }

    void update() override {
        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const Measurement measurement = measurement_stack.aggregate_temp().conditioned_total();

        if (set_temperature(measurement.value)) {
            redraw();
        }
        else {
            draw_value();
        }
    }
};