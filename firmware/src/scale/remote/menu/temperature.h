#pragma once

#include <U8x8lib.h>

#include "base.h"
#include "scale/measure/stack.h"
#include "scale/nvm/nvm.h"


struct TemperatureUnitsMenuLeaf final : BaseStrMenuLeaf {
    TemperatureUnits units{TemperatureUnits::CELSIUS};

    explicit TemperatureUnitsMenuLeaf(U8X8& display_) :
        BaseStrMenuLeaf(display_, 2)
    {}

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
              })
    {}
};


struct ThermistorDrawing final : BaseSensorTelemetryDrawing {
    const uint8_t sensor;
    BaseTemperatureDrawing temperature;

    ThermistorDrawing(
        U8X8& display_,
        const char* msg_,
        const uint8_t sensor_
    )
        : BaseSensorTelemetryDrawing(
            display_,
            msg_,
            2,
            std::vector<std::shared_ptr<BaseMenu>>{}),
          sensor(sensor_),
          temperature(*this)
    {}

    void update(const bool selected) override {
        if (!selected) {
            return;
        }

        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const auto measurement =
            measurement_stack.aggregate_temp().sensor_temperatures()[sensor];

        temperature._set_state(measurement);
        draw(selected);
    }

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
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
            std::vector<std::shared_ptr<BaseMenu>>{}),
          leaf(
              display_,
              "",
              sensor_)
    {}

    void update(const bool current) override {
        if (current) {
            leaf.update(true);
        }
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);

        if (!selected) {
            leaf.draw(false);
        }
    }
};


struct TemperatureDrawing final : BaseAggregateTelemetryDrawing {
    BaseTemperatureDrawing temperature;

    TemperatureDrawing(
        U8X8& display_,
        const char* msg_)
        : BaseAggregateTelemetryDrawing(
            display_,
            msg_,
            0,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<TemperatureUnitsMenu>(display_),
                std::make_shared<ThermistorMenu>(display_, 0),
                std::make_shared<ThermistorMenu>(display_, 1),
                std::make_shared<ThermistorMenu>(display_, 2),
            }),
          temperature(*this)
    {}

    void update(const bool current) override {
        if (!current) {
            return;
        }

        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const Measurement measurement =
            measurement_stack.aggregate_temp().conditioned_total();

        const bool needs_redraw =
            temperature._set_state(measurement);

        if (needs_redraw) {
            redraw();
        }
        else {
            draw_fast();
        }
    }
};