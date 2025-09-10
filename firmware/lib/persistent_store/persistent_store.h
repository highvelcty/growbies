#ifndef persistent_store_h
#define persistent_store_h

#if ARDUINO_ARCH_AVR
#include <stdio.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include <Arduino.h>
#include "build_cfg.h"
#include "constants.h"

typedef float MassTemperatureCoeff[MASS_SENSOR_COUNT][COEFF_COUNT];
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
    NvmHdr hdr;
    MassTemperatureCoeff mass_temperature_coeff{};
    MassCoeff mass_coeff{};
    Tare tare{};
};

struct Identify0 {
    NvmHdr hdr{};
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
    uint16_t mass_sensor_count{};
    uint16_t mass_sensor_type{};
    uint16_t temperature_sensor_count{};
    uint16_t temperature_sensor_type{};

    // Hardware configuration
    uint16_t pcba{};
    uint16_t wireless{};
    uint16_t battery{};
    uint16_t display{};
    uint16_t led{};
    uint16_t frame{};
    uint16_t foot{};
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
    virtual void get() = 0;
    virtual void put(const T& value) = 0;


    // Read-only accessor: returns const pointer
    const T* view() const {
        return &value_storage;
    }

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
        assert(sizeof(T) < EEPROM.length());
        NvmHdr hdr{};
        EEPROM.get(partition_offset, this->value_storage);

        if (!this->value_storage.hdr.is_initialized()) {
            this->value_storage = T{};
            EEPROM.put(partition_offset, this->value_storage);
        }
    }

    void put(const T& value) override {
        if (!value.hdr.is_initialized()) {
            this->value_storage = T{};
            EEPROM.put(partition_offset, this->value_storage);
        }
        else {
            EEPROM.put(partition_offset, value);
        }
        this->get();
    }

private:
    int partition_offset;

    void get() override {
        EEPROM.get(partition_offset, this->value_storage);
    }
};

#elif ARDUINO_ARCH_ESP32

template <typename T>
class Esp32NvmStore final : public NvmStoreBase<T> {
public:
    explicit Esp32NvmStore(const char* key) : ns_key(key) {}

    void begin() override {
        this->prefs.begin(this->ns, false);

        if (!this->prefs.isKey(this->ns_key)) {
            this->value_storage = T{};
            this->prefs.putBytes(this->ns_key, &this->value_storage,
                sizeof(this->value_storage));
        }
        this->prefs.end();
    }

    void put(const T& value) override {
        this->prefs.begin(this->ns, false);
        if (!value.hdr.is_initialized()) {
            this->value_storage = T{};
        }
        else {
            this->value_storage = value;
        }
        this->prefs.putBytes(this->ns_key, &this->value_storage,
            sizeof(this->value_storage));
        this->prefs.end();
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;

    void get() override {
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

#endif /* persistent_store_h */