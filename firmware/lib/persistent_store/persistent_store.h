#ifndef persistent_store_h
#define persistent_store_h

#if ARDUINO_ARCH_AVR
#include <stdio.h>
#include <EEPROM.h>
#elif ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#include "build_cfg.h"
#include "constants.h"

typedef float MassTemperatureCoeff[MASS_SENSOR_COUNT][COEFF_COUNT];
typedef float MassCoeff[COEFF_COUNT];
typedef float Tare[TARE_COUNT];

#pragma pack(1)

constexpr uint16_t MAGIC = 0x7A3F;
struct NvmHeader {
    uint16_t magic = MAGIC;
    uint16_t version = 0;

    explicit NvmHeader(const uint16_t v = 0) : version(v) {}

    bool is_initialized() const {
        return this->magic == MAGIC;
    }
};

struct Calibration {
    NvmHeader header;
    MassTemperatureCoeff mass_temperature_coeff{};
    MassCoeff mass_coeff{};
    Tare tare{};

    explicit Calibration(const uint16_t version = 1) : header(version) {}
};

struct Identify0 {
    // Meta-data that does not affect ABI
    static constexpr uint8_t VERSION = 0;

    NvmHeader header{};
    char firmware_version[32]{};    // <major>.<minor>.<micro>+<short git hash>

    // Constructor with version parameter
    explicit Identify0(const uint16_t version = 0) : header(version) {
        snprintf(this->firmware_version, sizeof(this->firmware_version), "%s", FIRMWARE_VERSION);
    }
};

struct Identify1 : Identify0 {
    static constexpr uint8_t VERSION = 1;

    char serial_number[64]{};
    char model_number[64]{};
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

    // Constructor with version parameter
    explicit Identify1(const uint16_t version = 1) : Identify0(version) {}
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
    virtual void put(const T& value) = 0;


    // Read-only accessor: returns const pointer
    const T* view() const {
        return heap_value;
    }

    virtual ~NvmStoreBase() = default;

protected:
    T* heap_value{nullptr};

private:
    virtual void get(T& value) = 0;

    // Load struct into heap and expose pointer
    T* load() {
        if (!heap_value) {
            heap_value = new T{};
            get(*heap_value);
        }
        return heap_value;
    }
};

#if ARDUINO_ARCH_AVR

template <typename T>
class AvrNvmStore final : public NvmStoreBase<T> {
public:
    explicit AvrNvmStore(const int offset) : partition_offset(offset) {}

    void begin() override {
        assert(sizeof(T) < EEPROM.length());
        T value;
        EEPROM.get(partition_offset, value);

        if (!value.header.is_initialized()) {
            // zero entire struct
            for (size_t offset = 0; offset < sizeof(T); ++offset) {
                EEPROM.update(partition_offset + offset, 0);
            }
            // initialize default
            value = T{};
            EEPROM.put(partition_offset, value);
        }
        this->load();
    }

    void put(const T& value) override {
        EEPROM.put(partition_offset, value);
    }

private:
    int partition_offset;

    void get(T& value) override {
        EEPROM.get(partition_offset, value);
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
            T value{};
            this->prefs.putBytes(this->ns_key, &value, sizeof(value));
        }

        this->prefs.end();

        this->load();
    }

    void put(const T& value) override {
        this->prefs.begin(this->ns, false);
        this->prefs.putBytes(this->ns_key, &value, sizeof(value));
        this->prefs.end();
    }

private:
    Preferences prefs;
    const char* ns_key;
    const char* ns = APPNAME;

    void get(T& value) override {
        this->prefs.begin(this->ns, true);
        this->prefs.getBytes(this->ns_key, &value, sizeof(value));
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