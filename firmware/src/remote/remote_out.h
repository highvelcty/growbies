#pragma once

#include <vector>
#include <memory>

#include "menu/menu.h"
#include "remote_in.h"


class RemoteOut {
public:
    // Delete copy/move constructors to enforce singleton
    RemoteOut(const RemoteOut&) = delete;
    RemoteOut& operator=(const RemoteOut&) = delete;
    RemoteOut(RemoteOut&&) = delete;
    RemoteOut& operator=(RemoteOut&&) = delete;
    // Access the application-wide singleton instance
    static RemoteOut& get();

    RemoteOut();
    void begin();

    void display_power_save(bool on_off);
    bool service(BUTTON button_pressed);
    void up();
    void down();
    void select();
    void render();
    void synchronize() const;
    void update() const;

private:
    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

    std::vector<size_t> menu_path{0};  // Index path up the tree
    std::vector<std::shared_ptr<BaseMenu>> menu_root;
    const std::vector<std::shared_ptr<BaseMenu>>* level_from_path() const;

    // internal singleton pointer
    static RemoteOut* instance;
};
