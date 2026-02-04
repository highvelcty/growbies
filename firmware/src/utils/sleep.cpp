#include "esp_sleep.h"

#include "constants.h"
#include "remote/remote_out.h"

void go_to_sleep() {
    RemoteOut& remote_out = RemoteOut::get();
    HX711::power_off();
    remote_out.display_power_save(true);
    esp_deep_sleep_enable_gpio_wakeup(1ULL << digitalPinToGPIONumber(BUTTON_0_PIN) |
                  1ULL << digitalPinToGPIONumber(BUTTON_1_PIN),
                  ESP_GPIO_WAKEUP_GPIO_HIGH);
    gpio_hold_en(static_cast<gpio_num_t>(HX711_SCK_PIN));
    gpio_deep_sleep_hold_en();
    esp_deep_sleep_start();
}

void go_to_deep_sleep() {
    // 2026_01_30 meyere: I did not find disabling the wakeup by timer source only toc be effective.
    //
    // esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);

    // Wait for buttons to be released
    int low_samples = 0;
    for (int ii = 0; ii < 10; ++ii) {
        if (digitalRead(BUTTON_0_PIN) == LOW and digitalRead(BUTTON_1_PIN) == LOW) {
            ++low_samples;
        }
        if (low_samples >= 2) {
            break;
        }
        delay(100);
    }
    delay(100);

    go_to_sleep();
}
void go_to_wakeful_sleep() {
    esp_sleep_enable_timer_wakeup(identify_store->payload()->auto_wake_interval_ms() * 1000ULL);
    go_to_sleep();
}
