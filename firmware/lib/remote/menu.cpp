#include "menu.h"
#include "menu_tree.h"
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
        render();
    }
    else {
        // Truncate path to the top-level menu that led to this leaf
        if (!menu_path.empty()) {
            menu_path.resize(1); // keep only first index
        }

        item->on_select();
    }
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
