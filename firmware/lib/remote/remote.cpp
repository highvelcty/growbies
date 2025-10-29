#include "constants.h"
#include <nvm.h>
#include "remote.h"

// Define static instance pointer
Remote* Remote::instance = nullptr;

// Application-wide singleton accessor
Remote& Remote::get() {
    static Remote singleton;
    return singleton;
}

Remote::Remote()
    : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN)
{
    // Makes member data accessible via ISR
    instance = this;
}

void Remote::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();
    // display.clear();
    display.setFlipMode(identify_store->payload()->flip);
    display.setFont(u8x8_font_chroma48medium8_r);
    display.drawString(0,0, "emey");
    display.drawString(1, 1, "emey");
    // MassDrawing(get_tare_name(TareIdx::TARE_0), 1234.567, MassUnits::KILOGRAMS).draw(display);
    // TemperatureDrawing("Temperature 0", 50, TemperatureUnits::CELSIUS).draw(display);
    // ConfigurationDrawing().draw(display);
    // draw(TemperatureUnitsDrawing());
    menu.render();
    // Configure wake pin and attach ISR
    pinMode(BUTTON_0_PIN, INPUT);
    pinMode(BUTTON_1_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(BUTTON_0_PIN), Remote::wakeISR0, RISING);
    attachInterrupt(digitalPinToInterrupt(BUTTON_1_PIN), Remote::wakeISR1, RISING);
}

bool Remote::service() {
    bool button_pressed = false;
    if (last_button_pressed != EVENT::NONE) {
        const unsigned long now = millis();

        if (static_cast<long>(now - debounce_time) >= BUTTON_DEBOUNCE_MS) {
            display.clearDisplay();
            if (last_button_pressed == EVENT::SELECT) {
                menu.select();
            }
            else if (last_button_pressed == EVENT::DIRECTION_0) {
                if (identify_store->payload()->flip) {
                    menu.down();
                }
                else {
                    menu.up();
                }
            }
            else if (last_button_pressed == EVENT::DIRECTION_1) {
                if (identify_store->payload()->flip) {
                    menu.up();
                }
                else {
                    menu.down();
                }
            }
            button_pressed = true;
            debounce_time = now;
        }
        last_button_pressed = EVENT::NONE;
    }

    if (!digitalRead(BUTTON_0_PIN) and !digitalRead(BUTTON_1_PIN)) {
        arm_isr = true;
    }
    else {
        arm_isr = false;
    }

    return button_pressed;
}

void Remote::set_flip(const bool flip) {
    display.setFlipMode(flip);
    display.refreshDisplay();
}

void IRAM_ATTR Remote::wakeISR0() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_1_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_0_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::SELECT;
    }
}

void IRAM_ATTR Remote::wakeISR1() {
    if (instance->arm_isr) {
        if (digitalRead(BUTTON_0_PIN)) {
            instance->last_button_pressed = EVENT::DIRECTION_1;
            return;
        }
        // This loop ensures a mechanical button impulse length and quality, preventing
        // misregistration.
        for (int ii = 0; ii < BUTTON_REREAD_COUNT; ++ii) {
            if (!digitalRead(BUTTON_1_PIN)) {
                return;
            }
        }
        instance->last_button_pressed = EVENT::DIRECTION_0;
    }
}

// -----------------------------------------------------------------------------
// Menu selection
// -----------------------------------------------------------------------------
const std::vector<std::shared_ptr<MenuItem>>* Remote::Menu::level_from_path() const {
    const std::vector<std::shared_ptr<MenuItem>>* level = &menu_root;

    for (size_t i = 0; i + 1 < menu_path.size(); ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return nullptr;
        level = &(*level)[idx]->children;
    }

    return level;
}

void Remote::Menu::up() {
    if (menu_path.empty()) return;
    auto* level = level_from_path();
    if (!level) return;

    size_t& idx = menu_path.back();
    if (idx == 0) {
        idx = level->size() - 1;  // wrap around
    } else {
        --idx;
    }
    render();
}

// -----------------------------------------------------------------------------
// Move selection down
// -----------------------------------------------------------------------------
void Remote::Menu::down() {
    if (menu_path.empty()) return;
    auto* level = level_from_path();
    if (!level || level->empty()) return;

    size_t& idx = menu_path.back();

    // Wrap around to first element if we're past the last
    idx = (idx + 1) % level->size();

    render();
}


// -----------------------------------------------------------------------------
// Select / descend or execute action
// -----------------------------------------------------------------------------
void Remote::Menu::select() {
    if (menu_path.empty()) return;

    auto* level = level_from_path();
    if (!level) return;

    const size_t idx = menu_path.back();
    if (idx >= level->size()) return;

    const auto& item = (*level)[idx];
    if (!item->children.empty()) {
        menu_path.push_back(0); // descend into first child
    }else {
        if (item->action) {
            item->action(); // execute leaf
        }

        // Truncate path to the top-level menu that led to this leaf
        if (!menu_path.empty()) {
            menu_path.resize(1); // keep only first index
        }
    }

    render();
}

void Remote::Menu::render() const {
    const std::vector<std::shared_ptr<MenuItem>>* level = &menu_root;
    
    for (auto it = menu_path.begin(); it != menu_path.end(); ++it) {
        const size_t idx = *it;
        if (idx >= level->size()) return; // safety check

        const auto& item = (*level)[idx];

        // Only mark as selected if not the last element
        item->drawing->selected = (std::next(it) != menu_path.end());

        remote.draw(*item->drawing); // draw the current level's drawing
        level = &item->children;     // descend into children
    }
}




