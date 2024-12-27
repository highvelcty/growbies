// The internal buffer size for each channel
#define BUF_SIZE 10
#define CHAN_SELECT_DELAY_MS 1

enum MuxChannel{
    MUX_CHANNEL_MIN = 0,
    MUX_CHANNEL_MAX = 3
};

enum ChannelSelect{
    CHAN_SELECT_MASK_0 = 0x01,
    CHAN_SELECT_MASK_1 = 0x02,
    CHAN_SELECT_MASK_2 = 0x04
};

enum ArduinoPins{
    ARDUINO_ANALOG_PIN0_TO_MUX_COMMON = 0,
    ARDUINO_DIGITAL_PIN2_TO_MUX_S0 = 2,
    ARDUINO_DIGITAL_PIN3_TO_MUX_S1 = 3,
    ARDUINO_DIGITAL_PIN4_TO_MUX_S2 = 4,
};


char serial_recv[256];
char* serial_recv_ptr = &serial_recv[0];


int channel0[BUF_SIZE];
int* channel0HeadPtr = &channel0[0];
int* channel0TailPtr = &channel0[0];

int channel1[BUF_SIZE];
int* channel1HeadPtr = &channel1[0];
int* channel1TailPtr = &channel1[0];

int channel2[BUF_SIZE];
int* channel2HeadPtr = &channel2[0];
int* channel2TailPtr = &channel2[0];

int channel3[BUF_SIZE];
int* channel3HeadPtr = &channel3[0];
int* channel3TailPtr = &channel3[0];


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
    for(int channel = MUX_CHANNEL_MIN; channel <= MUX_CHANNEL_MAX; channel++){
        selectChannel(channel);
        delay(CHAN_SELECT_DELAY_MS);
        Serial.print(analogRead(ARDUINO_ANALOG_PIN0_TO_MUX_COMMON));
        if (channel != MUX_CHANNEL_MAX){
            Serial.print(",");
        }
    }
    Serial.print("\n");
}

void loop() {
    while (!Serial.available());
    *serial_recv_ptr = Serial.read();
    if (*serial_recv_ptr == '\n'){
        *serial_recv_ptr = '\0';
        if (!strcmp("sample", serial_recv)){
            sample();
        }
        else if (!strcmp("loopback", serial_recv)) {
            Serial.print(serial_recv);
            Serial.print("\n");
        }
        else{
            Serial.print("Unrecognized command: ");
            Serial.print(serial_recv);
            Serial.print("\n");
        }
        serial_recv_ptr = &serial_recv[0];
    }
    else{
        ++serial_recv_ptr;
    }
}
