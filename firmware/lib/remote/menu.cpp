#include "menu.h"
#include "remote.h"
#include "drawing.h"

// initialize static singleton pointer
Menu* Menu::instance = nullptr;

Menu& Menu::get() {
    if (!instance) {
        instance = new Menu();
    }
    return *instance;
}

Menu::Menu() : display(U8X8_PIN_NONE, HW_I2C_SCL_PIN, HW_I2C_SDA_PIN) {
    menu_root.push_back(std::make_shared<MassDrawing>(
        display, get_tare_name(TareIdx::TARE_0)));
    menu_root.push_back(std::make_shared<MassDrawing>(
        display, get_tare_name(TareIdx::TARE_1)));
    menu_root.push_back(std::make_shared<MassDrawing>(
        display, get_tare_name(TareIdx::AUTO_0)));
    menu_root.push_back(std::make_shared<MassDrawing>(
        display, get_tare_name(TareIdx::AUTO_1)));
    menu_root.push_back(std::make_shared<ConfigurationDrawing>(display));
}

void Menu::begin() {
    // Order is important, the display must be initialized before attaching interrupts.
    display.begin();
    display.setFlipMode(identify_store->payload()->flip);
    display.setContrast(identify_store->payload()->contrast);
    render();

    Remote::begin();
}

bool Menu::service() {
    const BUTTON button_pressed = remote.service();
    if (button_pressed == BUTTON::DOWN) {
        down();
    }
    else if (button_pressed == BUTTON::UP) {
        up();
    }
    else if (button_pressed == BUTTON::SELECT) {
        select();
    }
    else {
        return false;
    }
    return true;
}

// -----------------------------------------------------------------------------
// Menu selection
// -----------------------------------------------------------------------------
// const std::vector<std::shared_ptr<MenuDrawing>>* Menu::level_from_path() const {
const std::vector<std::shared_ptr<MenuDrawing>>* Menu::level_from_path() const {
    const std::vector<std::shared_ptr<MenuDrawing>>* level = &menu_root;


    for (size_t i = 0; i + 1 < menu_path.size(); ++i) {
        const size_t idx = menu_path[i];
        if (idx >= level->size()) return nullptr;
        level = &(*level)[idx]->children;
    }

    return level;
}

void Menu::up() {
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
void Menu::down() {
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
void Menu::select() {
    if (menu_path.empty()) return;

    auto* level = level_from_path();
    if (!level) return;

    const size_t idx = menu_path.back();
    if (idx >= level->size()) return;

    const auto& item = (*level)[idx];
    if (!item->children.empty()) {
        menu_path.push_back(item->on_descent()); // descend into first child
        render();
    }
    else {
        // Truncate path to the top-level menu that led to this leaf
        if (!menu_path.empty()) {
            menu_path.resize(1); // keep only first index
        }
        item->on_select();
        render();
    }
}

void Menu::render() {
    const std::vector<std::shared_ptr<MenuDrawing>>* level = &menu_root;
    display.clear();

    for (auto it = menu_path.begin(); it != menu_path.end(); ++it) {
        const size_t idx = *it;
        if (idx >= level->size()) return; // safety check

        const auto& item = (*level)[idx];

        item->draw((std::next(it) != menu_path.end()));
        level = &item->children;     // descend into children
    }
}

void Menu::update() const {
    if (menu_root.empty()) return;

    std::vector<std::shared_ptr<MenuDrawing>> stack;

    // Start with the root nodes
    for (const auto& node : menu_root) {
        if (node) stack.push_back(node);
    }

    while (!stack.empty()) {
        const auto node = stack.back();
        stack.pop_back();

        node->update();

        for (const auto& child : node->children) {
            if (child) stack.push_back(child);
        }
    }
}

