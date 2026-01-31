#include "remote_out.h"
#include "system_state.h"

// initialize static singleton pointer
RemoteOut* RemoteOut::instance = nullptr;

RemoteOut& RemoteOut::get() {
    if (!instance) {
        instance = new RemoteOut();
    }
    return *instance;
}

RemoteOut::RemoteOut() : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN) {
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_0));
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_1));
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_2));
    menu_root.push_back(std::make_shared<TemperatureDrawing>(display, "Temperature"));
    menu_root.push_back(std::make_shared<ConfigurationMenu>(display));
    menu_path = {0};  // Select first top-level item
}

void RemoteOut::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();
    synchronize();
    render();

    // Attaching interrupts
    RemoteIn::begin();
}

void RemoteOut::display_power_save(const bool on_off) {
    display.setPowerSave(on_off);
}

bool RemoteOut::service(const BUTTON button_pressed) {
    if (button_pressed == BUTTON::NONE) {
        return false;
    }

    auto& system_state = SystemState::get();

    // Wake
    if (system_state.state() != PowerState::ACTIVE) {
        system_state.set_next_state(PowerState::ACTIVE);
        return true;
    }

    // Execute
    if (button_pressed == BUTTON::DOWN) {
        down();
    }
    else if (button_pressed == BUTTON::UP) {
        up();
    }
    else if (button_pressed == BUTTON::SELECT) {
        select();
    }

    system_state.notify_activity(millis());

    return true;
}

// -----------------------------------------------------------------------------
// Menu selection
// -----------------------------------------------------------------------------
const std::vector<std::shared_ptr<BaseMenu>>* RemoteOut::level_from_path() const {
    const std::vector<std::shared_ptr<BaseMenu>>* level = &menu_root;


    for (size_t i = 0; i + 1 < menu_path.size(); ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return nullptr;
        level = &(*level)[idx]->children;
    }

    return level;
}

void RemoteOut::up() {
    if (menu_path.empty()) return;
    auto* level = level_from_path();
    if (!level) return;

    size_t& idx = menu_path.back();

    if (idx == 0) {
        idx = level->size() - 1;  // wrap around
    } else {
        --idx;
    }

    const auto& item = (*level)[idx];
    item->on_up();
    render();
}

// -----------------------------------------------------------------------------
// Move selection down
// -----------------------------------------------------------------------------
void RemoteOut::down() {
    if (menu_path.empty()) return;
    auto* level = level_from_path();
    if (!level || level->empty()) return;

    size_t& idx = menu_path.back();

    // Wrap around to first element if we're past the last
    idx = (idx + 1) % level->size();

    const auto& item = (*level)[idx];
    item->on_down();
    render();
}

// -----------------------------------------------------------------------------
// Select / descend or execute action
// -----------------------------------------------------------------------------
void RemoteOut::select() {
    if (menu_path.empty()) return;

    auto* level = level_from_path();
    if (!level) return;

    const size_t idx = menu_path.back();
    if (idx >= level->size()) return;

    const auto& item = (*level)[idx];
    if (item->children.empty()) {
        // Truncate path to the top-level menu that led to this leaf
        if (!menu_path.empty()) {
            menu_path.resize(1); // keep only first index
        }
        item->on_select();
    }
    else {
        menu_path.push_back(0);
    }
    render();
}

void RemoteOut::render() {
    const std::vector<std::shared_ptr<BaseMenu>>* level = &menu_root;
    display.clear();

    for (auto it = menu_path.begin(); it != menu_path.end(); ++it) {
        const size_t idx = *it;
        if (idx >= level->size()) return; // safety check

        const auto& item = (*level)[idx];

        item->draw((std::next(it) != menu_path.end()));
        level = &item->children;     // descend into children
    }
}

void RemoteOut::synchronize() const {
    std::vector<std::shared_ptr<BaseMenu>> stack;

    // Start with the root nodes
    for (const auto& node : menu_root) {
        if (node) stack.push_back(node);
    }

    while (!stack.empty()) {
        const auto node = stack.back();
        stack.pop_back();

        node->synchronize();

        for (const auto& child : node->children) {
            if (child) stack.push_back(child);
        }
    }
}

void RemoteOut::update() const {
    const std::vector<std::shared_ptr<BaseMenu>>* level = &menu_root;

    for (const unsigned int idx : menu_path) {
        if (idx >= level->size()) return; // safety check

        const auto& item = (*level)[idx];

        item->update();
        level = &item->children;     // descend into children
    }
}
