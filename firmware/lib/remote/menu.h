#pragma once

#include <vector>
#include <memory>

#include "menu_items.h"
#include "remote.h"


class Menu {
public:
    // Delete copy/move constructors to enforce singleton
    Menu(const Menu&) = delete;
    Menu& operator=(const Menu&) = delete;
    Menu(Menu&&) = delete;
    Menu& operator=(Menu&&) = delete;
    // Access the application-wide singleton instance
    static Menu& get();

    Menu();
    void begin();

    bool service();
    void up();
    void down();
    void select();
    void render();
    void update() const;

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

private:
    Remote remote;

    std::vector<size_t> menu_path{0};  // Index path down the tree
    std::vector<std::shared_ptr<BaseMenu>> menu_root;
    const std::vector<std::shared_ptr<BaseMenu>>* level_from_path() const;

    // internal singleton pointer
    static Menu* instance;
};
