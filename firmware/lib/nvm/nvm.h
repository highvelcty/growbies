#pragma once

#include <Arduino.h>

#include "build_cfg.h"
#include "constants.h"
#include "types.h"
#include <crc.h>
#include <traits.h>

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

struct NvmHdr2 {
    Version_t version;
    uint8_t reserved0;
    Crc_t crc;
    uint16_t length;
    uint16_t reserved1;
};

struct NvmStructBase{
    NvmHdr2 hdr{};   // all derived NVM structs will have hdr

    static constexpr Version_t VERSION = 1;
};


struct Tare {
    TareValue values{};
};

struct NvmTare : NvmStructBase {
    Tare payload{};

    static constexpr Version_t VERSION = 1;
};

struct Calibration {
    MassTemperatureCoeff mass_temperature_coeff{};
    MassCoeff mass_coeff{};
};

struct NvmCalibration : NvmStructBase {
    Calibration payload{};

    static constexpr Version_t VERSION = 1;
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

struct NvmIdentify1 : NvmStructBase {
    Identify1 payload{};

    static constexpr Version_t VERSION = 1;
};

#if ARDUINO_ARCH_AVR
constexpr int PARTITION_A_OFFSET = 0;
constexpr int PARTITION_B_OFFSET = 512;
constexpr int PARTITION_C_OFFSET = 640;
constexpr int PARTITION_D_OFFSET = 768;
constexpr int PARTITION_E_OFFSET = 896;
#endif


// Templated Base classes
template <typename T>
class NvmStoreBase {
    static_assert(is_base_of<NvmStructBase, T>::value,
                  "NvmStoreBase can only be instantiated with types derived from NvmStructBase");
public:
    virtual void begin() = 0;
    virtual void init() {
        put(T{});
    }

    virtual void migrate() {
        _migrate();
    }

    virtual void put(const T& value) {
        this->value_storage = value;
        migrate();
    }

    virtual void update() {
        const Crc_t crc = this->value_storage.hdr.crc;
        migrate();
        if (this->value_storage.hdr.crc != crc) {
            put(this->value_storage);
        }
    }

    // Accessors
    const decltype(T::hdr)* hdr() const { return &value_storage.hdr; }
    const decltype(T::payload)* payload() const { return &value_storage.payload; }
    const T* view() const { return &value_storage; }

    virtual ~NvmStoreBase() = default;

protected:
    T value_storage{};

    void _migrate() {
                this->value_storage.hdr.version = this->value_storage.VERSION;
        this->value_storage.hdr.crc = crc_ccitt16(
            reinterpret_cast<const uint8_t*>(&this->value_storage.payload),
            sizeof(this->value_storage.payload)
        );
        this->value_storage.hdr.length = sizeof(this->value_storage.payload);
    }
};

// Templated concrete classes

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
    }

    void put(const T& value) override {
        NvmStoreBase<T>::put(value);

        EEPROM.put(partition_offset, NvmHdr{});
        EEPROM.put(partition_offset + sizeof(NvmHdr), value);
    }

private:
    int partition_offset;

    void update() override {
        EEPROM.get(partition_offset + sizeof(NvmHdr), this->value_storage);
        NvmStoreBase<T>::update();
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
    }

    void init() override {
        this->prefs.begin(this->ns, false);
        this->prefs.remove(this->ns_key);
        this->prefs.end();
        NvmStoreBase<T>::init();
    }

    void put(const T& value) override {
        NvmStoreBase<T>::put(value);

        this->prefs.begin(this->ns, false);
        // Ignoring the boolean return indicating success.
        // meyere, fix this
        this->prefs.putBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;

    void update() override {
        this->prefs.begin(this->ns, false);
        // Ignoring the return value which is the number of bytes read.
        // meyere, fix this.
        this->prefs.getBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();

        NvmStoreBase<T>::update();
    }
};

#endif


// Type specializations
template <>
inline void NvmStoreBase<NvmIdentify1>::migrate() {
    if (strncmp(value_storage.payload.firmware_version, FIRMWARE_VERSION,
                sizeof(value_storage.payload.firmware_version)) != 0) {
        snprintf(value_storage.payload.firmware_version,
                 sizeof(value_storage.payload.firmware_version),
                 "%s",
                 FIRMWARE_VERSION);
    }
    _migrate();
}

#if ARDUINO_ARCH_AVR
using CalibrationStore = AvrNvmStore<NvmCalibration>;
using IdentifyStore    = AvrNvmStore<NvmIdentify1>;
using TareStore        = AvrNvmStore<NvmTare>;
#elif ARDUINO_ARCH_ESP32
using CalibrationStore = Esp32NvmStore<NvmCalibration>;
using IdentifyStore = Esp32NvmStore<NvmIdentify1>;
using TareStore = Esp32NvmStore<NvmTare>;
#endif

extern CalibrationStore* calibration_store;
extern IdentifyStore* identify_store;
extern TareStore* tare_store;
