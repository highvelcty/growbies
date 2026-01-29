#pragma once

#include <Arduino.h>
#include <cstdio>
#include <memory>
#include <U8x8lib.h>
#include "esp_sleep.h"

#include "base.h"
#include "constants.h"
#include "measure/battery.h"
#include "nvm/nvm.h"

struct ContrastMenuLeaf final : BaseIntMenuLeaf {
    static constexpr uint8_t INC = 15;
    explicit ContrastMenuLeaf(U8X8& display_) : BaseIntMenuLeaf(display_, 3) {}

    void on_up() override {
        if (value == UINT8_MAX) {
            value = 0;
        }
        else {
            value = min(value + INC, UINT8_MAX);
        }
        display.setContrast(value);
    }

    void on_down() override {

        if (value == 0) {
            value = UINT8_MAX;
        }
        else {
            value = max(value - INC, 0);
        }

        display.setContrast(value);
    }

    void on_select() override {
        identify_store->edit().payload.contrast = value;
        identify_store->commit();
    }

    void synchronize() override {
        value = identify_store->view()->payload.contrast;
        display.setContrast(value);
    }
};

struct ContrastMenu final : BaseCfgMenu {
    explicit ContrastMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Contrast",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<ContrastMenuLeaf>(display_),
              }) {}
};

struct FlipMenuLeaf final : BaseStrMenuLeaf {
    bool flip{false};

    explicit FlipMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        _set_msg();
    }

    void draw(const bool selected) override {
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void on_up() override {
        flip = !flip;
    }

    void on_down() override {
        on_up();
    }

    void on_select() override {
        display.setFlipMode(flip);
        identify_store->edit().payload.flip = flip;
        identify_store->commit();
    }

    void synchronize() override {
        flip = identify_store->view()->payload.flip;
        display.setFlipMode(flip);
    }

    void _set_msg() {
        if (flip) {
            msg = "True";
        }
        else {
            msg = "False";
        }
    }
};

struct FlipMenu final : BaseCfgMenu {
    explicit FlipMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Flip",
              2,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<FlipMenuLeaf>(display_)
              }) {}
};

struct SleepTimeoutMenuLeaf final : BaseIntMenuLeaf {
    static constexpr size_t values_len = 17;
    static const int* values() {
        static constexpr int v[values_len] = {
            0, 1, 2, 3, 5, 8, 15, 20, 30,
            60, 90, 120, 240, 360, 480, 600, 1200
        };
        return v;
    }
    static constexpr int default_idx = 6;
    int idx{default_idx};

    explicit SleepTimeoutMenuLeaf(U8X8& display_) : BaseIntMenuLeaf(display_, 3) {
        value = values()[idx];
    }

    void on_up() override {
        if (idx == values_len - 1) {
            idx = 0;
        }
        else {
            ++idx;
        }
        value = values()[idx];
    }

    void on_down() override {

        if (idx == 0) {
            idx = values_len - 1;
        }
        else {
            --idx;
        }
        value = values()[idx];
    }

    void on_select() override {
        identify_store->edit().payload.sleep_timeout = static_cast<float>(value);
        identify_store->commit();
    }

    void synchronize() override {
        const int stored =
            static_cast<int>(identify_store->view()->payload.sleep_timeout);

        // Default to the first element
        size_t new_idx = 0;

        for (size_t i = 0; i < values_len; ++i) {
            if (values()[i] <= stored) {
                new_idx = i;   // candidate
            } else {
                break;        // table is sorted, so we’re done
            }
        }

        idx = static_cast<int>(new_idx);
        value = static_cast<int>(stored);
    }
};

struct SleepTimeoutMenu final : BaseCfgMenu {
    explicit SleepTimeoutMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Sleep TO (s)",
            2,
            std::vector<std::shared_ptr<BaseMenu>>{
                    std::make_shared<SleepTimeoutMenuLeaf>(display_)
            }) {}
};

struct SleepMenuLeaf final : BaseStrMenuLeaf {
    bool doit{true};

    explicit SleepMenuLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        _set_msg();
    }

    void draw(const bool selected) override {
        _set_msg();
        BaseStrMenuLeaf::draw(selected);
    }

    void on_up() override {
        doit = !doit;
    }

    void on_down() override {
        on_up();
    }

    void on_select() override {
        if (doit) {
            display.setPowerSave(true);

            // wait for buttons released and debounce
            for (int i = 0; i < 10; ++i) {
                if (digitalRead(BUTTON_0_PIN) == LOW && digitalRead(BUTTON_1_PIN) == LOW) {
                    break;
                }
                delay(10);
            }
            delay(BUTTON_DEBOUNCE_MS);

            esp_deep_sleep_start();
        }
    }

    void _set_msg() {
        if (doit) {
            msg = "True";
        }
        else {
            msg = "False";
        }
    }
};

struct SleepMenu final : BaseCfgMenu {
    explicit SleepMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Sleep",
            2,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<SleepMenuLeaf>(display_)
            }) {}
};

struct BatteryLeaf final : BaseStrMenuLeaf {
    constexpr static size_t MSG_BUF_LEN = 16;
    // Space pad messages out to the maximum message length of 11 characters so that shorter lines
    // overwriting longer lines clear crufty characters.
    const char* fmt_str = "%-11s";
    char msg_buf[MSG_BUF_LEN]{};
    Battery battery;
    int test_val{0};

    explicit BatteryLeaf(U8X8& display_) : BaseStrMenuLeaf(display_, 3) {
        msg = msg_buf;
        _set_msg();
    }

    void draw(const bool selected) override {
        _set_msg();                 // refresh each draw
        BaseStrMenuLeaf::draw(selected);
    }

    void update() override {
        draw(cached_selected);
    }

    void _set_msg() {
        if (battery.is_charging()) {
            snprintf(msg_buf, MSG_BUF_LEN, "charging");
            snprintf(msg_buf, MSG_BUF_LEN, fmt_str, msg_buf);


        }
        else {
            snprintf(
                msg_buf,
                MSG_BUF_LEN,
                "%d%% (%.1fV)", // 100% (4.2V)
                battery.percentage(),
                battery.voltage()
            );
        }
    }
};

struct BatteryMenu final : BaseCfgMenu {
    explicit BatteryMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Battery",
            2,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<BatteryLeaf>(display_)
            }) {}
};

struct DisplayMenu final : BaseCfgMenu {
    explicit DisplayMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Display",
            1,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<FlipMenu>(display_),
                std::make_shared<ContrastMenu>(display_),
            }) {}
};

struct PowerMenu final : BaseCfgMenu {
    explicit PowerMenu(U8X8& display_)
        : BaseCfgMenu(
            display_,
            "Power",
            1,
            std::vector<std::shared_ptr<BaseMenu>>{
                std::make_shared<SleepMenu>(display_),
                std::make_shared<SleepTimeoutMenu>(display_),
                std::make_shared<BatteryMenu>(display_),
            }) {}
};

struct ConfigurationMenu final : BaseCfgMenu {
    explicit ConfigurationMenu(U8X8& display_)
        : BaseCfgMenu(
              display_,
              "Configuration",
              0,
              std::vector<std::shared_ptr<BaseMenu>>{
                  std::make_shared<PowerMenu>(display_),
                  std::make_shared<DisplayMenu>(display_),
              }) {}
};
