#pragma once

#include <Arduino.h>

#include "build_cfg.h"
#include "constants.h"
#include "types.h"
#include "utils/crc.h"

#if ARDUINO_ARCH_AVR
#include <stdio.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif


#pragma pack(1)

constexpr int DEFAULT_CONTRAST = 16;
constexpr float DEFAULT_TELEMETRY_INTERVAL_SEC = 5.0;
constexpr float DEFAULT_SLEEP_TO_SEC = 15.0;
constexpr float DEFAULT_AUTO_WAKE_INTERVAL_SEC = 2.0;

constexpr int MAX_MASS_SENSOR_COUNT = 5;
constexpr uint8_t MAX_COEFF_COUNT = 7;
constexpr uint8_t COEFF_COUNT = 7;
constexpr uint8_t TARE_COUNT = 8;
constexpr float REF_TEMPERATURE = 22.0;

typedef float MassTemperatureCoeffRaw[MAX_MASS_SENSOR_COUNT][MAX_COEFF_COUNT];
typedef float MassCoeffRaw[MAX_COEFF_COUNT];
typedef float TareValue[TARE_COUNT];

enum TareIdx : int {
    TARE_0 = 0,
    TARE_1 = 1,
    TARE_2 = 2,
    GLOBAL = 7,
};

const char* get_tare_name(TareIdx idx);

enum class MassUnits: uint8_t {
    GRAMS = 0,
    KILOGRAMS = 1,
    OUNCES = 2,
    POUNDS = 3,
};

enum class TemperatureUnits: uint8_t {
    CELSIUS = 0,
    FAHRENHEIT = 1,
};

struct NvmHdr {
    Version_t version;
    uint8_t reserved0;
    Crc_t crc;
    uint16_t length;
    uint16_t reserved1;
};

struct NvmStructBase{
    NvmHdr hdr{};   // all derived NVM structs will have hdr

    static constexpr Version_t VERSION = 1;
};

struct Tare {
    float value{0};
    MassUnits display_units{MassUnits::GRAMS};
    uint8_t Reserved[3]{};
    Elapsed_t timestamp{0};
};
static_assert(12 == sizeof(Tare), "unexpected struct size");

struct Tares {
    Tare tares[TARE_COUNT]{};
};

struct NvmTare : NvmStructBase {
    Tares payload{};

    static constexpr Version_t VERSION = 2;
};
static_assert(sizeof(NvmTare) == 104, "unexpected structure size");

struct CalibrationHdr {
    uint8_t mass_sensor_count{MASS_SENSOR_COUNT};
    uint8_t coeff_count{COEFF_COUNT};
    float ref_temperature{REF_TEMPERATURE};
    uint16_t reserved{};
};
static_assert(sizeof(CalibrationHdr) == 8, "unexpected structure size");

struct Coeffs {
    float mass_offset{};
    float mass_slope{};
    float mass_quadratic{};
    float temperature_offset{};
    float temperature_slope{};
    float temperature_quadratic{};
    float thermistor_offset{};
};
static_assert(sizeof(Coeffs) == 28, "unexpected structure size");

union SensorUnion {
    Coeffs coeffs{};
    float raw[MAX_COEFF_COUNT];
};
static_assert(sizeof(SensorUnion) == (sizeof(float) * MAX_COEFF_COUNT), "unexpected struct size");

struct Calibration {
    CalibrationHdr hdr{};
    SensorUnion sensor[MAX_MASS_SENSOR_COUNT]{};
};
static_assert(sizeof(Calibration) ==
    sizeof(CalibrationHdr) + (sizeof(SensorUnion) * MAX_MASS_SENSOR_COUNT),
    "unexpected structure size");

struct NvmCalibration : NvmStructBase {
    Calibration payload{};

    static constexpr Version_t VERSION = 1;
};
static_assert(156 == sizeof(NvmCalibration), "unexpected structure size");


struct Identify {
    char firmware_version[32]{};    // <major>.<minor>.<micro>+<short git hash>
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

    // User configuration
    bool flip{};
    MassUnits mass_units{};
    TemperatureUnits temperature_units{};
    uint8_t contrast{DEFAULT_CONTRAST};
    float telemetry_interval{DEFAULT_TELEMETRY_INTERVAL_SEC};
    float sleep_timeout{DEFAULT_SLEEP_TO_SEC};
    float auto_wake_interval{DEFAULT_AUTO_WAKE_INTERVAL_SEC};

    // Constructor with version parameter
    explicit Identify() {
        snprintf(this->firmware_version, sizeof(this->firmware_version), "%s", FIRMWARE_VERSION);
        this->mass_sensor_count = MASS_SENSOR_COUNT;
        this->temperature_sensor_count = TEMPERATURE_SENSOR_COUNT;
    }

    static uint32_t float_to_uint32_t(const float value) {
        if (value <= 0.0f) {
            return 0;  // telemetry disabled
        }
        constexpr auto max_ms = static_cast<float>(UINT32_MAX);
        const float ms = value * 1000.0f;
        if (ms > max_ms) {
            return UINT32_MAX;
        }
        return static_cast<uint32_t>(ms);
    }

    uint32_t telemetry_interval_ms() const {
        return float_to_uint32_t(telemetry_interval);
    }

    uint32_t sleep_timeout_ms() const {
        return float_to_uint32_t(sleep_timeout);
    }

    uint32_t auto_wake_interval_ms() const {
        return float_to_uint32_t(auto_wake_interval);
    }
};
static_assert(sizeof(Identify) == 127, "unexpected structure size");

struct NvmIdentify : NvmStructBase {
    Identify payload{};

    static constexpr Version_t VERSION = 7;
};
static_assert(sizeof(NvmIdentify) == 135, "unexpected structure size");

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
public:
    virtual void begin() {
        _get();
        migrate();
    }

    void commit() {
        // For committing RAM structure changes to persistent store.
        migrate();
    }

    virtual void init() {
        put(T{});
    }

    virtual void put(const T& value) {
        this->value_storage = value;
        migrate();
    }

    // Accessors
    const decltype(T::hdr)* hdr() const { return &value_storage.hdr; }
    const decltype(T::payload)* payload() const { return &value_storage.payload; }
    T& edit() { return value_storage; } // Mutable reference that can then be committed to store.
    const T* view() const { return &value_storage; }

    virtual ~NvmStoreBase() = default;

protected:
    T value_storage{};

    virtual void migrate() {
        _migrate();
    }

    void _migrate() {
        this->value_storage.hdr.version = this->value_storage.VERSION;
        this->value_storage.hdr.crc = calc_crc();
        this->value_storage.hdr.length = sizeof(this->value_storage.payload);
        _put(value_storage);
    }

    Crc_t calc_crc() {
        return crc_ccitt16(
            reinterpret_cast<const uint8_t*>(&this->value_storage.payload),
            sizeof(this->value_storage.payload)
        );
    }

    virtual void _get() = 0;
    virtual void _put(const T& value) = 0;
};

// Templated concrete classes
#if ARDUINO_ARCH_AVR

template <typename T>
class AvrNvmStore final : public NvmStoreBase<T> {
public:
    explicit AvrNvmStore(const int offset) : partition_offset(offset) {}

    void begin() override {
        EEPROM.get(partition_offset, this->value_storage);
        NvmStoreBase<T>::begin();
    }

    void put(const T& value) override {
        NvmStoreBase<T>::put(value);
        EEPROM.put(partition_offset, value);
    }

protected:
    void _get() override {
        EEPROM.get(partition_offset, this->value_storage);
    }

    void _put(const T& value) override {
        EEPROM.put(partition_offset, value);
    }

private:
    int partition_offset;
};

#elif ARDUINO_ARCH_ESP32

template <typename T>
class Esp32NvmStore final : public NvmStoreBase<T> {
public:
    explicit Esp32NvmStore(const char* key) : ns_key(key) {}

    void init() override {
        this->prefs.begin(this->ns, false);
        this->prefs.remove(this->ns_key);
        this->prefs.end();

        NvmStoreBase<T>::init();
    }

protected:
    void _get() override {
        this->prefs.begin(this->ns, false);
        // Ignoring the return value which is the number of bytes read.
        // meyere, fix this.
        this->prefs.getBytes(this->ns_key, &this->value_storage, sizeof(this->value_storage));
        this->prefs.end();
    }

    void _put(const T& value) override {
        this->prefs.begin(this->ns, false);
        // Ignoring the boolean return indicating success.
        // meyere, fix this
        this->prefs.putBytes(this->ns_key, &value, sizeof(value));
        this->prefs.end();
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;
};

#endif


// Type specializations
template <>
inline void NvmStoreBase<NvmIdentify>::migrate() {
    if (strncmp(value_storage.payload.firmware_version, FIRMWARE_VERSION,
                sizeof(value_storage.payload.firmware_version)) != 0) {
        snprintf(value_storage.payload.firmware_version,
                 sizeof(value_storage.payload.firmware_version),
                 "%s",
                 FIRMWARE_VERSION);
    }

    value_storage.payload.mass_sensor_count = MASS_SENSOR_COUNT;
    value_storage.payload.temperature_sensor_count = TEMPERATURE_SENSOR_COUNT;

    if (value_storage.hdr.version < 2) {
        value_storage.payload.mass_units = MassUnits::GRAMS;
        value_storage.payload.temperature_units = TemperatureUnits::FAHRENHEIT;
    }

    if (value_storage.hdr.version < 3) {
        value_storage.payload.contrast = DEFAULT_CONTRAST;
    }

    if (value_storage.hdr.version < 5) {
        value_storage.payload.telemetry_interval = DEFAULT_TELEMETRY_INTERVAL_SEC;
    }

    if (value_storage.hdr.version < 6) {
        value_storage.payload.sleep_timeout = DEFAULT_SLEEP_TO_SEC;
    }

    if (value_storage.hdr.version < 7) {
        value_storage.payload.auto_wake_interval = DEFAULT_AUTO_WAKE_INTERVAL_SEC;
    }

    _migrate();
}

template <>
inline void NvmStoreBase<NvmCalibration>::migrate() {
    value_storage.payload.hdr.coeff_count = COEFF_COUNT;
    _migrate();
}

#if ARDUINO_ARCH_AVR
using CalibrationStore = AvrNvmStore<NvmCalibration>;
using IdentifyStore    = AvrNvmStore<NvmIdentify>;
using TareStore        = AvrNvmStore<NvmTare>;
#elif ARDUINO_ARCH_ESP32
using CalibrationStore = Esp32NvmStore<NvmCalibration>;
using IdentifyStore = Esp32NvmStore<NvmIdentify>;
using TareStore = Esp32NvmStore<NvmTare>;
#endif

extern CalibrationStore* calibration_store;
extern IdentifyStore* identify_store;
extern TareStore* tare_store;

#pragma pack()