#pragma once

#include <Arduino.h>

#include "build_cfg.h"
#include "constants.h"
#include "types.h"
#include <crc.h>

#if ARDUINO_ARCH_AVR
#include <stdio.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

typedef float MassTemperatureCoeff[MAX_MASS_SENSOR_COUNT][COEFF_COUNT];
typedef float MassCoeff[COEFF_COUNT];
typedef float TareValue[TARE_COUNT];

#pragma pack(1)

constexpr uint16_t MAGIC = 0x7A3F;
struct NvmHdr {
    uint16_t magic = MAGIC;

    bool is_initialized() const {
        return this->magic == MAGIC;
    }
};

struct Tare {
    TareValue values{};
    uint16_t crc{};
};

struct Calibration {
    MassTemperatureCoeff mass_temperature_coeff{};
    MassCoeff mass_coeff{};
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

    void init_fields() {};

    virtual ~NvmStoreBase() = default;

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

        this->init_fields();
    }

    void put(T& value) override {
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
        this->prefs.begin(this->ns, false);
        const bool do_init = !this->prefs.isKey(this->ns_key);
        this->prefs.end();

        if (do_init) {
            init();
        }

        update();

        this->init_fields();
    }

    void init() override {
        this->prefs.begin(this->ns, false);
        this->prefs.remove(this->ns_key);
        this->prefs.end();
        NvmStoreBase<T>::init();
    }

    void put(const T& value) override {
        this->_put(value);
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;

    void _put(const T& value) {
        this->value_storage = value;
        this->prefs.begin(this->ns, false);
        // Ignoring the boolean return indicating success.
        // meyere, fix this
        this->prefs.putBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }

    void update() override {
        _update();
    }

    void _update() {
        this->value_storage = T{};
        this->prefs.begin(this->ns, false);
        // Ignoring the return value which is the number of bytes read.
        // meyere, fix this.
        this->prefs.getBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }
};

#endif

// Specialization for Tare
template <>
inline void Esp32NvmStore<Tare>::put(const Tare& value) {
    this->value_storage = value;
    this->value_storage.crc = crc_ccitt16(reinterpret_cast<const uint8_t*>(&this->value_storage),
        offsetof(Tare, crc));
    _put(this->value_storage);
}

template <>
inline void Esp32NvmStore<Tare>::update() {
    _update();

    const uint16_t crc = crc_ccitt16(reinterpret_cast<const uint8_t*>(&this->value_storage),
        offsetof(Tare, crc));

    if (crc != this->value_storage.crc) {
        this->value_storage.crc = crc;
    }
}

// Specialization for Identify1
template <>
inline void NvmStoreBase<Identify1>::init_fields() {
    snprintf(this->value_storage.firmware_version,
             sizeof(this->value_storage.firmware_version),
             "%s",
             FIRMWARE_VERSION);
    this->put(this->value_storage);
}

#if ARDUINO_ARCH_AVR
using CalibrationStore = AvrNvmStore<Calibration>;
using IdentifyStore    = AvrNvmStore<Identify1>;
using TareStore        = AvrNvmStore<Tare>;
#elif ARDUINO_ARCH_ESP32
using CalibrationStore = Esp32NvmStore<Calibration>;
using IdentifyStore = Esp32NvmStore<Identify1>;
using TareStore = Esp32NvmStore<Tare>;
#endif

extern CalibrationStore* calibration_store;
extern IdentifyStore* identify_store;
extern TareStore* tare_store;
