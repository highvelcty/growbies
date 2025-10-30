#pragma once

#include <vector>
#include <memory>

#include "drawing.h"
#include "menu.h"
#include "nvm.h"
#include "remote.h"
#include "utils.h"

// -----------------------------------------------------------------------------
// Menu Tree
// -----------------------------------------------------------------------------
struct MenuItem {
    std::shared_ptr<Drawing> drawing;
    std::vector<std::shared_ptr<MenuItem>> children;
    std::function<void()> action;

    explicit MenuItem(std::shared_ptr<Drawing> d,
             std::vector<std::shared_ptr<MenuItem>> c = {})
        : drawing(std::move(d)), children(std::move(c)) {}

    virtual size_t on_descent() const {
        return 0;
    }

    virtual void on_select() const {
        // It is the responsibility of any overrides to call render if necessary
        Remote::get().menu->render();
    }

    virtual ~MenuItem() = default;
};

struct MassUnitsMenuItem final : MenuItem {
    explicit MassUnitsMenuItem(std::vector<std::shared_ptr<MenuItem>> _children) :
        MenuItem(std::make_unique<MassUnitsMenuDrawing>(), std::move(_children)) {}

    size_t on_descent() const override {
        // Return an index based on the current MassUnits in the payload
        switch (identify_store->view()->payload.mass_units) {
            case MassUnits::GRAMS:      return 0;
            case MassUnits::KILOGRAMS:  return 1;
            case MassUnits::OUNCES:     return 2;
            case MassUnits::POUNDS:     return 3;
        }
        return 0; // fallback
    }
};

struct MassUnitsItem final : MenuItem {
    MassUnits units;

    explicit MassUnitsItem(const MassUnits _units)
        : MenuItem(std::make_shared<MassUnitsDrawing>(_units)), units(_units) {}

    void on_select() const override {
        identify_store->edit().payload.mass_units = units;
        identify_store->commit();
        Remote::get().menu->render();
    }
};


struct TempUnitsMenuItem final : MenuItem {
    explicit TempUnitsMenuItem(std::vector<std::shared_ptr<MenuItem>> _children) :
        MenuItem(std::make_unique<TemperatureUnitsMenuDrawing>(), std::move(_children)) {}

    size_t on_descent() const override {
        if (identify_store->view()->payload.temperature_units == TemperatureUnits::CELSIUS) {
            return 0;
        }
        return 1;
    }
};
struct TempUnitsItem final: MenuItem {
    TemperatureUnits units;

    explicit TempUnitsItem(const TemperatureUnits _units)
        : MenuItem(std::make_shared<TemperatureUnitsDrawing>(_units)), units(_units) {}

    void on_select() const override {
        identify_store->edit().payload.temperature_units = units;
        identify_store->commit();
        Remote::get().menu->render();
    }
};

struct FlipMenuItem final : MenuItem {
    explicit FlipMenuItem(std::vector<std::shared_ptr<MenuItem>> _children) :
        MenuItem(std::make_unique<FlipMenuDrawing>(), std::move(_children)) {}
    size_t on_descent() const override {
        return identify_store->view()->payload.flip ? 1 : 0;
    }
};
struct FlipItem final : MenuItem {
    bool flip{false};

    explicit FlipItem(const bool flip)
        : MenuItem(std::make_shared<FlipDrawing>(flip)), flip(flip) {}

    void on_select() const override {
        identify_store->edit().payload.flip = flip;
        identify_store->commit();
        Remote::get().flip(flip);
    }
};

const std::vector<std::shared_ptr<MenuItem>> menu_root {
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::TARE_0))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::TARE_1))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::AUTO_0))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::AUTO_1))),
    std::make_shared<MenuItem>(
        std::make_shared<ConfigurationDrawing>(),
        std::vector<std::shared_ptr<MenuItem>>{
            std::make_shared<MassUnitsMenuItem>(
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<MassUnitsItem>(MassUnits::GRAMS),
                    std::make_shared<MassUnitsItem>(MassUnits::KILOGRAMS),
                    std::make_shared<MassUnitsItem>(MassUnits::OUNCES),
                    std::make_shared<MassUnitsItem>(MassUnits::POUNDS),
                }
            ),
            std::make_shared<TempUnitsMenuItem>(
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<TempUnitsItem>(TemperatureUnits::CELSIUS),
                    std::make_shared<TempUnitsItem>(TemperatureUnits::FAHRENHEIT),
                }
            ),
            std::make_shared<FlipMenuItem>(
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<FlipItem>(false),
                    std::make_shared<FlipItem>(true)
                }
            ),
        }
    )
};