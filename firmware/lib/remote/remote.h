#pragma once

#include <vector>
#include <memory>
#include <functional>
#include <U8x8lib.h>

#include "drawing.h"


constexpr int DEFAULT_CONTRAST = 16;


enum class EVENT: int8_t {
    NONE = -1,
    SELECT = 0,
    DIRECTION_0 = 1,
    DIRECTION_1 = 2,
};

// -----------------------------------------------------------------------------
// Menu item definition
// -----------------------------------------------------------------------------
struct MenuItem {
    std::shared_ptr<Drawing> drawing;
    std::vector<std::shared_ptr<MenuItem>> children;
    std::function<void()> action;

    explicit MenuItem(std::shared_ptr<Drawing> d,
             std::vector<std::shared_ptr<MenuItem>> c = {},
             std::function<void()> a = {})
        : drawing(std::move(d)), children(std::move(c)), action(std::move(a)) {}
};

// -----------------------------------------------------------------------------
// Menu Tree
// -----------------------------------------------------------------------------
static const std::vector<std::shared_ptr<MenuItem>> menu_root {
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::TARE_0))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::TARE_1))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::AUTO_0))),
    std::make_shared<MenuItem>(std::make_shared<MassDrawing>(get_tare_name(TareIdx::AUTO_1))),
    std::make_shared<MenuItem>(
        std::make_shared<ConfigurationDrawing>(),
        std::vector<std::shared_ptr<MenuItem>>{
            std::make_shared<MenuItem>(
                std::make_shared<TemperatureUnitsDrawing>(),
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<MenuItem>(std::make_shared<TemperatureUnitsCDrawing>()),
                    std::make_shared<MenuItem>(std::make_shared<TemperatureUnitsFDrawing>())
                }
            )
        }
    )
};

class Remote {
public:
    // Enforce singleton
    Remote();
    Remote(const Remote&) = delete;
    Remote& operator=(const Remote&) = delete;
    Remote(Remote&&) = delete;
    Remote& operator=(Remote&&) = delete;

    // Access the application-wide singleton instance
    static Remote& get();
    // Initialize wake-on-interrupt configuration previously done by enable_delay_wake
    void begin();
    bool service();

    void set_flip(bool flip);

    void draw(const Drawing& d) {
        // Clone the drawing for safe storage
        cached_drawing = d.clone();

        // Render immediately
        cached_drawing->draw(display);
    }

    // Redraw last cached Drawing (useful after display flip)
    void redraw() {
        if (cached_drawing) {
            cached_drawing->draw(display);
        }
    }

    class Menu {
    public:
        explicit Menu(Remote& r) : remote(r) {}

        void up();
        void down();
        void select();
        void render() const;

    private:
        const std::vector<std::shared_ptr<MenuItem>>* level_from_path() const;

        std::vector<size_t> menu_path{0};  // Index path down the tree
        Remote& remote;                    // Reference to enclosing Remote
    };
    Menu menu{*this};

private:
    // Pointer used by ISR to touch the singleton
    static Remote* instance;

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

    unsigned long debounce_time = 0;

    std::unique_ptr<Drawing> cached_drawing;

    // volatile make this ISR-safe
    volatile EVENT last_button_pressed = EVENT::NONE;
    volatile bool arm_isr = true;

    static void wakeISR0();
    static void wakeISR1();
};

