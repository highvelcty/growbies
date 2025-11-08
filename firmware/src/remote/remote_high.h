#pragma once

#include <vector>
#include <memory>

#include "menu_items.h"
#include "remote_low.h"


class RemoteHigh {
public:
    // Delete copy/move constructors to enforce singleton
    RemoteHigh(const RemoteHigh&) = delete;
    RemoteHigh& operator=(const RemoteHigh&) = delete;
    RemoteHigh(RemoteHigh&&) = delete;
    RemoteHigh& operator=(RemoteHigh&&) = delete;
    // Access the application-wide singleton instance
    static RemoteHigh& get();

    RemoteHigh();
    void begin();

    bool service();
    void up();
    void down();
    void select();
    void render();
    void synchronize() const;
    void update() const;

    U8X8_SSD1306_128X32_UNIVISION_HW_I2C display;

private:
    RemoteLow remote;

    std::vector<size_t> menu_path{0};  // Index path down the tree
    std::vector<std::shared_ptr<BaseMenu>> menu_root;
    const std::vector<std::shared_ptr<BaseMenu>>* level_from_path() const;

    // internal singleton pointer
    static RemoteHigh* instance;
};
