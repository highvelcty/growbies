#include "remote_out.h"
#include "system_state.h"

// initialize static singleton pointer
RemoteOut* RemoteOut::instance = nullptr;

// Initialize persistent data
// Note: this assignment happens only once and then is persisted thereafter
static constexpr size_t MENU_PATH_MAX_DEPTH = 4;
RTC_DATA_ATTR bool menu_path_initialized = false;
RTC_DATA_ATTR size_t menu_path[MENU_PATH_MAX_DEPTH];
RTC_DATA_ATTR size_t menu_path_depth = 1;

RemoteOut& RemoteOut::get() {
    if (!instance) {
        instance = new RemoteOut();
    }
    return *instance;
}

RemoteOut::RemoteOut()
    : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN)
{
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_0));
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_1));
    menu_root.push_back(std::make_shared<MassDrawing>(display, TareIdx::TARE_2));
    menu_root.push_back(std::make_shared<TemperatureDrawing>(display, "Temperature"));
    menu_root.push_back(std::make_shared<ConfigurationMenu>(display));

    initialize();
}

void RemoteOut::initialize() {
    if (!menu_path_initialized || menu_path_depth > MENU_PATH_MAX_DEPTH || menu_path_depth <= 0) {
        menu_path_initialized = true;
        menu_path[0] = 0;
        menu_path_depth = 1;
    }
}

void RemoteOut::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();
    synchronize();
    render();

    // Attaching interrupts
    RemoteIn::begin();
}

bool RemoteOut::service(const BUTTON button_pressed) {
    if (button_pressed == BUTTON::NONE) {
        return false;
    }

    auto& system_state = SystemState::get();

    if (system_state.state() != PowerState::ACTIVE) {
        system_state.set_next_state(PowerState::ACTIVE);
        return true;
    }

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

void RemoteOut::display_power_save(const bool on_off) {
    display.setPowerSave(on_off);
}

// -----------------------------------------------------------------------------
// Menu selection
// -----------------------------------------------------------------------------
const std::vector<std::shared_ptr<BaseMenu>>* RemoteOut::level_from_path() const {
    const std::vector<std::shared_ptr<BaseMenu>>* level = &menu_root;

    for (size_t i = 0; i + 1 < menu_path_depth; ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return nullptr;
        level = &(*level)[idx]->children;
    }

    return level;
}

void RemoteOut::up() {
    auto* level = level_from_path();
    if (!level) return;

    size_t& idx = menu_path[menu_path_depth - 1];

    // Up with wrapping
    if (idx == 0) {
        idx = level->size() - 1;
    } else {
        --idx;
    }

    const auto& item = (*level)[idx];
    item->on_up();
    render();
}

void RemoteOut::down() {
    auto* level = level_from_path();
    if (!level) return;

    size_t& idx = menu_path[menu_path_depth - 1];

    // Down with wrapping
    idx = (idx + 1) % level->size();

    const auto& item = (*level)[idx];
    item->on_down();
    render();
}

void RemoteOut::select() {
    auto* level = level_from_path();
    if (!level) return;

    const size_t idx = menu_path[menu_path_depth - 1];
    if (idx >= level->size()) return;

    const auto& item = (*level)[idx];

    if (item->children.empty()) {
        // Truncate path to the top-level menu that led to this leaf
        menu_path_depth = 1;
        item->on_select();
    }
    else {
        menu_path[menu_path_depth] = 0;
        ++menu_path_depth;
    }

    render();
}

void RemoteOut::render() {
    const std::vector<std::shared_ptr<BaseMenu>>* level = &menu_root;
    display.clear();

    for (size_t i = 0; i < menu_path_depth; ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return;

        const auto& item = (*level)[idx];

        item->draw((i + 1 < menu_path_depth));
        level = &item->children;
    }
}

void RemoteOut::synchronize() const {
    std::vector<std::shared_ptr<BaseMenu>> stack;

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

    for (size_t i = 0; i < menu_path_depth; ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return;

        const auto& item = (*level)[idx];

        item->update();
        level = &item->children;
    }
}
