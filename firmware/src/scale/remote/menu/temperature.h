#pragma once

#include <U8x8lib.h>

#include "base.h"
#include "scale/measure/stack.h"
#include "scale/nvm/nvm.h"

// -----------------------------------------------------------------------------
// Temperature data formatting
// -----------------------------------------------------------------------------
struct BaseTemperatureDataFormatting {
    BaseTelemetryDrawing& telemetry_drawing;
    static constexpr int PRECISION{1};

    explicit BaseTemperatureDataFormatting(
        BaseTelemetryDrawing& telemetry_drawing_)
        : telemetry_drawing(telemetry_drawing_)
    {}

    void synchronize() const {
        telemetry_drawing.state.units =
            static_cast<uint8_t>(
                identify_store->view()->payload.temperature_units);
    }

    void _set_state(const Measurement measurement) const {
        telemetry_drawing.state.needs_full_redraw = false;

        const auto new_units =
            identify_store->view()->payload.temperature_units;

        float temperature = measurement.value;

        if (new_units == TemperatureUnits::FAHRENHEIT) {
            temperature = (measurement.value * 9.0f / 5.0f) + 32.0f;
        }

        if (temperature > 999.9f)
            temperature = 999.9f;

        if (temperature < -99.9f)
            temperature = -99.9f;

        if (temperature != telemetry_drawing.state.value) {
            telemetry_drawing.state.value = temperature;
        }

        if (static_cast<uint8_t>(new_units) != telemetry_drawing.state.units) {
            telemetry_drawing.state.needs_full_redraw = true;
            telemetry_drawing.state.units = static_cast<uint8_t>(new_units);
        }

        if (measurement.error != telemetry_drawing.state.error) {
            telemetry_drawing.state.needs_full_redraw = true;
            telemetry_drawing.state.error = measurement.error;
        }

        telemetry_drawing.state.units_type = UnitsType::TEMPERATURE;
        telemetry_drawing.state.precision = PRECISION;
    }
};


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


struct TemperatureErrorDrawing final : BaseErrorDrawing {
    TemperatureErrorDrawing(
        U8X8& display_,
        const char* msg_)
        : BaseErrorDrawing(display_, msg_)
    {}

    Measurement get_measurement(
        const MeasurementStack& measurement_stack) const override
    {
        return measurement_stack.aggregate_temp().conditioned_total();
    }
};


struct TemperatureErrorMenu final : BaseCfgMenu {
    TemperatureErrorDrawing leaf;

    explicit TemperatureErrorMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Error",
            1,
            std::vector<std::shared_ptr<BaseMenu>>{}),
          leaf(
              display_,
              "")
    {}

    void update() override {
        BaseCfgMenu::update();
        leaf.update();
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(selected);
        leaf.draw(selected);
    }

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
    }
};


struct ThermistorDrawing final : BaseSensorTelemetryDrawing {
    const uint8_t sensor;
    BaseTemperatureDataFormatting temperature_data;

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
          temperature_data(*this)
    {}

    void update() override {
        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const auto measurement =
            measurement_stack.aggregate_temp().sensor_temperatures()[sensor];

        // ReSharper disable once CppExpressionWithoutSideEffects
        temperature_data._set_state(measurement);
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

    void update() override {
        BaseCfgMenu::update();
        leaf.update();
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(true);
        leaf.draw(selected);
    }
};


struct TemperatureDrawing final : BaseAggregateTelemetryDrawing {
    BaseTemperatureDataFormatting telemetry_drawing;

    TemperatureDrawing(
        U8X8& display_,
        const char* msg_)
        : BaseAggregateTelemetryDrawing(
            display_,
            msg_,
            0,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<TemperatureUnitsMenu>(display_),
                std::make_shared<TemperatureErrorMenu>(display_),
                std::make_shared<ThermistorMenu>(display_, 0),
                std::make_shared<ThermistorMenu>(display_, 1),
                std::make_shared<ThermistorMenu>(display_, 2),
            }),
          telemetry_drawing(*this)
    {}

    void update() override {
        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const Measurement measurement =
            measurement_stack.aggregate_temp().conditioned_total();

        telemetry_drawing._set_state(measurement);
    }
};

