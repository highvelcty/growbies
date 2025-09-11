#pragma once

#include <Arduino.h>

#include "build_cfg.h"
#include "constants.h"
#include "types.h"

#if ARDUINO_ARCH_AVR
#include <stdio.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

typedef float MassTemperatureCoeff[MAX_MASS_SENSOR_COUNT][COEFF_COUNT];
typedef float MassCoeff[COEFF_COUNT];
typedef float Tare[TARE_COUNT];

#pragma pack(1)

constexpr uint16_t MAGIC = 0x7A3F;
struct NvmHdr {
    uint16_t magic = MAGIC;

    bool is_initialized() const {
        return this->magic == MAGIC;
    }
};

struct Calibration {
    MassTemperatureCoeff mass_temperature_coeff{};
    MassCoeff mass_coeff{};
    Tare tare{};
};

struct Identify0 {
    char firmware_version[32]{};    // <major>.<minor>.<micro>+<short git hash>

    // Constructor with version parameter
    explicit Identify0() {
        snprintf(this->firmware_version, sizeof(this->firmware_version), "%s", FIRMWARE_VERSION);
    }
};

struct Identify1 : Identify0 {
    char serial_number[32]{};
    char model_number[32]{};
    float manufacture_date{};       // seconds since epoch

    // Sensor configuration
    uint8_t mass_sensor_type{};
    SensorIdx_t mass_sensor_count{};
    uint8_t temperature_sensor_type{};
    SensorIdx_t temperature_sensor_count{};

    // Hardware configuration
    uint8_t pcba{};
    uint8_t wireless{};
    uint8_t battery{};
    uint8_t display{};
    uint8_t led{};
    uint8_t frame{};
    uint8_t foot{};
};

#if ARDUINO_ARCH_AVR
constexpr int PARTITION_A_OFFSET = 0;
constexpr int PARTITION_B_OFFSET = 512;
constexpr int PARTITION_C_OFFSET = 640;
constexpr int PARTITION_D_OFFSET = 768;
constexpr int PARTITION_E_OFFSET = 896;
#endif



template <typename T>
class NvmStoreBase {
public:
    virtual void begin() = 0;
    virtual void update() = 0;
    virtual void init() {
        put(T{});
    }

    virtual void put(const T& value) = 0;


    // Read-only accessor: returns const pointer
    const T* view() const {
        return &value_storage;
    }

    virtual ~NvmStoreBase() = default;

    template<typename U = T>
    typename std::enable_if<std::is_same<U, Identify1>::value>::type
    set_firmware_version() {
        snprintf(this->value_storage.firmware_version,
                 sizeof(this->value_storage.firmware_version),
                 "%s",
                 FIRMWARE_VERSION);
    }

    template<typename U = T>
    typename std::enable_if<!std::is_same<U, Identify1>::value>::type
    set_firmware_version() {
        // do nothing
    }

protected:
    T value_storage{};
};

#if ARDUINO_ARCH_AVR

template <typename T>
class AvrNvmStore final : public NvmStoreBase<T> {
public:
    explicit AvrNvmStore(const int offset) : partition_offset(offset) {}

    void begin() override {
        assert(partition_offset + sizeof(T) < EEPROM.length());
        NvmHdr hdr{};
        EEPROM.get(partition_offset, hdr);

        if (!hdr.is_initialized()) {
            init();
        }
        update();

        this->set_firmware_version();
        put(this->value_storage);
    }

    void put(const T& value) override {
        this->value_storage = value;
        EEPROM.put(partition_offset, NvmHdr{});
        EEPROM.put(partition_offset + sizeof(NvmHdr), value);
    }

private:
    int partition_offset;

    void update() override {
        EEPROM.get(partition_offset + sizeof(NvmHdr), this->value_storage);
    }
};

#elif ARDUINO_ARCH_ESP32

template <typename T>
class Esp32NvmStore final : public NvmStoreBase<T> {
public:
    explicit Esp32NvmStore(const char* key) : ns_key(key) {}

    void begin() override {
        bool do_init = false;

        this->prefs.begin(this->ns, false);

        if (!this->prefs.isKey(this->ns_key)) {
            do_init = true;
        }
        this->prefs.end();

        if (do_init) {
            init();
        }

        update();

        this->set_firmware_version();
        // Warning, putting this into set_firmware_version causes a crash
        put(this->value_storage);
    }

    void put(const T& value) override {
        this->prefs.begin(this->ns, false);
        this->value_storage = value;
        this->prefs.putBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;

    void update() override {
        this->prefs.begin(this->ns, false);
        this->prefs.getBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }
};

#endif


#if ARDUINO_ARCH_AVR
using CalibrationStore = AvrNvmStore<Calibration>;
using IdentifyStore    = AvrNvmStore<Identify1>;
#elif ARDUINO_ARCH_ESP32
using CalibrationStore = Esp32NvmStore<Calibration>;
using IdentifyStore    = Esp32NvmStore<Identify1>;
#endif

extern CalibrationStore* calibration_store;
extern IdentifyStore* identify_store;
