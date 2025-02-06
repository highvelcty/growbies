#define CHAN_SELECT_DELAY_MS 1
#define MAIN_POLLING_LOOP_INTERVAL_MS 1
#define SLIP_END '\xc0'


enum MuxChannel{
    MUX_CHANNEL_MIN = 0,
    MUX_CHANNEL_MAX = 7
};

enum ChannelSelect{
    CHAN_SELECT_MASK_0 = 0x01,
    CHAN_SELECT_MASK_1 = 0x02,
    CHAN_SELECT_MASK_2 = 0x04,
};

enum ArduinoPins{
    ARDUINO_ANALOG_PIN0_TO_MUX_COMMON = 0,
    ARDUINO_DIGITAL_PIN2_TO_MUX_S0 = 2,
    ARDUINO_DIGITAL_PIN3_TO_MUX_S1 = 3,
    ARDUINO_DIGITAL_PIN4_TO_MUX_S2 = 4,
};

struct OutData{
    int data[MUX_CHANNEL_MAX + 1];
};

char serial_recv[64];
char* serial_recv_ptr = &serial_recv[0];


void setup() {
  analogReference(EXTERNAL);
  Serial.begin(115200);
  memset(serial_recv, 0, sizeof(serial_recv));
  pinMode(ARDUINO_DIGITAL_PIN2_TO_MUX_S0, OUTPUT);
  pinMode(ARDUINO_DIGITAL_PIN3_TO_MUX_S1, OUTPUT);
  pinMode(ARDUINO_DIGITAL_PIN4_TO_MUX_S2, OUTPUT);
}

void selectChannel(int channel){
    digitalWrite(ARDUINO_DIGITAL_PIN2_TO_MUX_S0, channel & CHAN_SELECT_MASK_0);
    digitalWrite(ARDUINO_DIGITAL_PIN3_TO_MUX_S1, channel & CHAN_SELECT_MASK_1);
    digitalWrite(ARDUINO_DIGITAL_PIN4_TO_MUX_S2, channel & CHAN_SELECT_MASK_2);
}

void sample(){
    OutData outData;
    for(int channel = MUX_CHANNEL_MIN; channel <= MUX_CHANNEL_MAX; channel++){
        selectChannel(channel);
        delay(CHAN_SELECT_DELAY_MS);
        outData.data[channel] = analogRead(ARDUINO_ANALOG_PIN0_TO_MUX_COMMON);
    }
    Serial.write((byte*)&outData, sizeof(outData));
    Serial.write(SLIP_END);
}

void loop() {
    while (!Serial.available()){
        delay(MAIN_POLLING_LOOP_INTERVAL_MS);
    }
    *serial_recv_ptr = Serial.read();
    if (*serial_recv_ptr == SLIP_END){
        *serial_recv_ptr = '\0';
        if (!strcmp("sample", serial_recv)){
            sample();
        }
        else if (!strcmp("loopback", serial_recv)) {
            Serial.print(serial_recv);
            Serial.write(SLIP_END);
        }
        else{
            Serial.print("Unrecognized cmd: ");
            Serial.print(serial_recv);
            Serial.write(SLIP_END);
        }
        serial_recv_ptr = &serial_recv[0];
    }
    else{
        ++serial_recv_ptr;
    }
}
