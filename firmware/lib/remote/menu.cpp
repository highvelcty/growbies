#include "menu.h"
#include "remote.h"
#include "drawing.h"

// -----------------------------------------------------------------------------
// Menu selection
// -----------------------------------------------------------------------------
const std::vector<std::shared_ptr<MenuItem>>* Menu::level_from_path() const {
    const std::vector<std::shared_ptr<MenuItem>>* level = &menu_root;

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
    }
    else {
        item->on_select();
        // if (item->action) {
        //     item->action(); // execute leaf
        // }

        // Truncate path to the top-level menu that led to this leaf
        if (!menu_path.empty()) {
            menu_path.resize(1); // keep only first index
        }
    }

    render();
}

void Menu::render() const {
    const std::vector<std::shared_ptr<MenuItem>>* level = &menu_root;
    remote.display.clear();

    for (auto it = menu_path.begin(); it != menu_path.end(); ++it) {
        const size_t idx = *it;
        if (idx >= level->size()) return; // safety check

        const auto& item = (*level)[idx];

        item->drawing->draw(remote.display, (std::next(it) != menu_path.end()));
        level = &item->children;     // descend into children
    }
}


// -----------------------------------------------------------------------------
// Menu Tree
// -----------------------------------------------------------------------------
struct FlipMenuItem final : MenuItem {
    using MenuItem::MenuItem;

    size_t on_descent() const override {
        return identify_store->view()->payload.flip ? 1 : 0;
    }
};

struct FlipTrueItem final : MenuItem {
    explicit FlipTrueItem() : MenuItem(std::make_shared<FlipTrueDrawing>()) {}

    void on_select() const override {
        Remote::get().flip(true);
    }
};

struct FlipFalseItem final : MenuItem {
    explicit FlipFalseItem() : MenuItem(std::make_shared<FlipFalseDrawing>()) {}
    void on_select() const override {
        Remote::get().flip(false);
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
            std::make_shared<MenuItem>(
                std::make_shared<MassUnitsDrawing>(),
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<MenuItem>(std::make_shared<MassUnitsGramsDrawing>()),
                    std::make_shared<MenuItem>(std::make_shared<MassUnitsKilogramsDrawing>()),
                    std::make_shared<MenuItem>(std::make_shared<MassUnitsOuncesDrawing>()),
                    std::make_shared<MenuItem>(std::make_shared<MassUnitsPoundsDrawing>()),
                }
            ),
            std::make_shared<MenuItem>(
                std::make_shared<TemperatureUnitsDrawing>(),
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<MenuItem>(std::make_shared<TemperatureUnitsCDrawing>()),
                    std::make_shared<MenuItem>(std::make_shared<TemperatureUnitsFDrawing>())
                }
            ),
            std::make_shared<FlipMenuItem>(
                std::make_shared<FlipDrawing>(),
                std::vector<std::shared_ptr<MenuItem>>{
                    std::make_shared<FlipFalseItem>(),
                    std::make_shared<FlipTrueItem>()
                }
            ),
        }
    )
};

