#pragma once

#include <U8x8lib.h>
#include <memory>
#include <Arduino.h>

#include "base.h"
#include "scale/measure/stack.h"
#include "common/system_state.h"
#include "scale/nvm/nvm.h"

// -----------------------------------------------------------------------------
// Temperature data formatting
// -----------------------------------------------------------------------------
struct BaseMassDataFormatting {
    BaseTelemetryDrawing& telemetry_drawing;
    static constexpr int PRECISION{1};

    explicit BaseMassDataFormatting(
        BaseTelemetryDrawing& telemetry_drawing_)
        : telemetry_drawing(telemetry_drawing_)
    {}

    void synchronize() const {
        telemetry_drawing.state.units =
            static_cast<uint8_t>(identify_store->view()->payload.mass_units);
    }

    bool _set_state(const Measurement measurement, const float tare_val) const {
        bool redraw = false;
        const auto new_units =
            identify_store->view()->payload.mass_units;

        float tare_mass =measurement.value - tare_val;

        const MassUnits converted_units = new_units;

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
        constexpr float MAX_TRIPLE_PRECISION = 999.999;
        constexpr float MIN_TRIPLE_PRECISION = -99.999;
        // ReSharper restore CppTooWideScope

        // Unit conversion
        switch (converted_units) {
            case MassUnits::GRAMS:
                break;

            case MassUnits::KILOGRAMS:
                tare_mass /= GRAMS_PER_KG;
                break;

            case MassUnits::OUNCES:
                tare_mass /= GRAMS_PER_OZ;
                break;

            case MassUnits::POUNDS:
                tare_mass /= (GRAMS_PER_OZ * OUNCES_PER_LB);
                break;
        }

        // Precision by units
        int precision = 0;

        switch (converted_units) {
            case MassUnits::GRAMS: {
                precision = 0;

                if (tare_mass > MAX_SINGLE_PRECISION ||
                    tare_mass < MIN_SINGLE_PRECISION) {
                    tare_mass /= GRAMS_PER_KG;
                }

                break;
            }

            case MassUnits::OUNCES: {
                precision = 2;

                if (tare_mass > MAX_DOUBLE_PRECISION ||
                    tare_mass < MIN_DOUBLE_PRECISION) {
                    tare_mass /= OUNCES_PER_LB;
                }

                break;
            }

            case MassUnits::POUNDS:
            case MassUnits::KILOGRAMS: {
                precision = 3;

                if (tare_mass > MAX_TRIPLE_PRECISION ||
                    tare_mass < MIN_TRIPLE_PRECISION) {
                    precision = 2;
                }
                else if (tare_mass > MAX_DOUBLE_PRECISION ||
                         tare_mass < MIN_DOUBLE_PRECISION) {
                    precision = 1;
                }
                else if (tare_mass > MAX_SINGLE_PRECISION ||
                         tare_mass < MIN_SINGLE_PRECISION) {
                    precision = 0;

                    if (tare_mass > MAX_ZERO_PRECISION) {
                        tare_mass = MAX_ZERO_PRECISION;
                    }
                    else if (tare_mass < MIN_ZERO_PRECISION) {
                        tare_mass = MIN_ZERO_PRECISION;
                    }
                }

                break;
            }
        }

        telemetry_drawing.state.value = tare_mass;

        if (static_cast<uint8_t>(new_units) != telemetry_drawing.state.units) {
            redraw = true;
            telemetry_drawing.state.units = static_cast<uint8_t>(new_units);
        }

        if (measurement.error != telemetry_drawing.state.error) {
            redraw = true;
            telemetry_drawing.state.error = measurement.error;
        }
        if (precision != telemetry_drawing.state.precision) {
            redraw = true;
            telemetry_drawing.state.precision = precision;
        }

        telemetry_drawing.state.units_type = UnitsType::MASS;

        return redraw;
    }
};

// -----------------------------------------------------------------------------
// MassDrawing
// -----------------------------------------------------------------------------
struct TareZeroLeaf final : BaseStrMenuLeaf {
    constexpr static int TARE_SAMPLE_DELAY = 2000;
    TareIdx tare_idx;

    explicit TareZeroLeaf(
        U8X8& display_,
        const TareIdx tare_idx_)
        : BaseStrMenuLeaf(display_, 2),
          tare_idx(tare_idx_)
    {
        msg = "zero";
    }

    void on_up() override {
        ;
    }

    void on_down() override {
        ;
    }

    void on_select() override {
        static const char* dots[] = {
            ".",
            "..",
            "...",
            "....",
            ".....",
            "......",
            ".......",
            "........"
        };

        static const char* back_dots[] = {
            "....... ",
            "......  ",
            ".....   ",
            "....    ",
            "...     ",
            "..      ",
            ".       ",
            "        "
        };

        const auto& stack = MeasurementStack::get();
        constexpr size_t dots_len = sizeof(dots) / sizeof(dots[0]);

        stack.reset();

        for (const char* s : dots) {
            msg = s;
            draw(true);
            delay(TARE_SAMPLE_DELAY / dots_len);
        }

        for (const char* s : back_dots) {
            stack.update();
            msg = s;
            draw(true);
        }

        Measurement measurement =
            stack.aggregate_mass().conditioned_total();

        tare_store->edit().payload.tares[tare_idx].value =
            measurement.value;

        tare_store->commit();

        msg = "zero";
    }

    void synchronize() override {
        ;
    }
};


struct TareCancelLeaf final : BaseStrMenuLeaf {
    explicit TareCancelLeaf(U8X8& display_)
        : BaseStrMenuLeaf(display_, 2)
    {
        msg = "cancel";
    }
};


struct TareMenu final : BaseCfgMenu {
    explicit TareMenu(
        U8X8& display,
        TareIdx tare_idx)
        : BaseCfgMenu(
            display,
            "Tare",
            1,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<TareZeroLeaf>(display, tare_idx),
                std::make_shared<TareCancelLeaf>(display)
            })
    {}
};


struct MassUnitsMenuLeaf final : BaseStrMenuLeaf {
    MassUnits units{MassUnits::GRAMS};

    explicit MassUnitsMenuLeaf(U8X8& display_) :
        BaseStrMenuLeaf(display_, 2)
    {}

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

        // Wrap around if we exceed the first element.
        // Note that the uint8 wraps to 255.
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
        set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void set_msg() override {
        if (units == MassUnits::GRAMS) {
            msg = "g: grams";
        }
        else if (units == MassUnits::KILOGRAMS) {
            msg = "kg: "
                  "kilog.";
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
              })
    {}
};

struct MassSensorDrawing final : BaseSensorTelemetryDrawing {
    const uint8_t sensor;
    BaseMassDataFormatting mass_data;

    MassSensorDrawing(
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
          mass_data(*this)
    {}

    void update(const bool selected) override {
        if (!selected) {
            return;
        }

        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        const auto measurement =
            measurement_stack.aggregate_mass().sensor_measurements()[sensor];

        // ReSharper disable once CppExpressionWithoutSideEffects
        mass_data._set_state(measurement, 0.0f);
        draw(selected);
    }

    char get_selected_char(bool selected) const override {
        return LEAF_CHAR;
    }
};

struct MassSensorMenu final : BaseCfgMenu {
    MassSensorDrawing leaf;

    static const char* name(const uint8_t sensor_) {
        switch (sensor_) {
            case 0: return "Load Cell 0";
            case 1: return "Load Cell 1";
            case 2: return "Load Cell 2";
            default: return "Load Cell";
        }
    }

    explicit MassSensorMenu(
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

    void update(const bool selected) override {
        BaseCfgMenu::update(selected);
        leaf.update(selected);
    }

    void draw(const bool selected) override {
        BaseCfgMenu::draw(true);
        leaf.draw(selected);
    }
};

struct MassDrawing final : BaseAggregateTelemetryDrawing {
    BaseMassDataFormatting telemetry_drawing;
    TareIdx tare_idx{};
    SystemState& system_state = SystemState::get();

    MassDrawing(
        U8X8& display_,
        const TareIdx tare_idx_)
        : BaseAggregateTelemetryDrawing(
              display_,
              get_tare_name(tare_idx_),
              0,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<TareMenu>(display_, tare_idx_),
                  std::make_shared<MassUnitsMenu>(display_),
                  std::make_shared<MassSensorMenu>(display_, 0),
                  std::make_shared<MassSensorMenu>(display_, 1),
                  std::make_shared<MassSensorMenu>(display_, 2),
              }),
            telemetry_drawing(*this),
            tare_idx(tare_idx_)
    {}

    void update(const bool selected) override {
        if (!selected) {
            return;
        }

        const auto& measurement_stack = MeasurementStack::get();
        measurement_stack.update();

        if (measurement_stack.aggregate_mass().is_event_tripped()) {
            system_state.notify_activity(millis());
        }

        const Measurement measurement =
            measurement_stack.aggregate_mass().conditioned_total();


        const bool needs_redraw =
            telemetry_drawing._set_state(measurement, tare_store->payload()->tares[tare_idx].value);

        if (needs_redraw) {
            redraw();
        }
        else {
            draw_fast();
        }
    }
};

