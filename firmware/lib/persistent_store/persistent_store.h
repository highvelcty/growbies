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
    NvmHeader header{};
    char firmware_version[32]{};    // <major>.<minor>.<micro>+<short git hash>

    // Constructor with version parameter
    explicit Identify0(const uint16_t version = 0) : header(version) {
        this->header = NvmHeader{};
        snprintf(this->firmware_version, sizeof(this->firmware_version), "%s", VERSION);
    }
};

struct Identify1 : public Identify0 {
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

class PersistentStore {
    public:
        void begin();

    protected:
    #if ARDUINO_ARCH_ESP32
        Preferences prefs;
        const char* ns = "growbies";
    #endif
};

// Templated generic NVM store
template <typename T>
class NvmStore : public PersistentStore {
public:
#if ARDUINO_ARCH_AVR
    explicit NvmStore(const int offset) : partition_offset(offset) {}
#elif ARDUINO_ARCH_ESP32
    explicit NvmStore(const char* key) : ns_key(key) {}
#endif
    void begin() {
        PersistentStore::begin();

#if ARDUINO_ARCH_AVR
        Identify0 id_struct;
        EEPROM.get(this->partition_offset, id_struct);

        if (!id_struct.header.is_initialized()) {
            id_struct = Identify0{}; // reinitialize using default constructor

            // Write back to EEPROM
            EEPROM.put(this->partition_offset, id_struct);
        }

#elif ARDUINO_ARCH_ESP32
        this->prefs.begin(this->ns, false);

        // Initialize if the key does not exist
        if (!this->prefs.isKey(this->ns_key)) {
            Identify0 id_struct;
            this->prefs.putBytes(this->ns_key, &id_struct, sizeof(id_struct));
        }
        this->prefs.end();
#endif
    }

    void get(T& value) {
#if ARDUINO_ARCH_AVR
        EEPROM.get(this->partition_offset, value);
#elif ARDUINO_ARCH_ESP32
        this->prefs.begin(this->ns, true);
        this->prefs.getBytes(this->ns_key, &value, sizeof(value));
        this->prefs.end();
#endif
    }

    void put(const T& value) {
#if ARDUINO_ARCH_AVR
        EEPROM.put(this->partition_offset, value);
#elif ARDUINO_ARCH_ESP32
        this->prefs.begin(this->ns, false);
        this->prefs.putBytes(this->ns_key, &value, sizeof(value));
        this->prefs.end();
#endif
    }

private:
#if ARDUINO_ARCH_AVR
    int partition_offset;
#elif ARDUINO_ARCH_ESP32
    const char* ns_key;
#endif
};


using CalibrationStore = NvmStore<Calibration>;
using IdentifyStore = NvmStore<Identify1>;

extern CalibrationStore* calibration_store;
extern IdentifyStore* identify_store;

#endif /* persistent_store_h */