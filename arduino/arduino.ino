// The internal buffer size for each channel
#define BUF_SIZE 10

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
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  digitalWrite(2, HIGH);
  digitalWrite(3, LOW);
  digitalWrite(4, LOW);
}

void sample(int channel=0){
  Serial.print(analogRead(channel));
  Serial.print("\n");
}

void loop() {
    while (!Serial.available());
    *serial_recv_ptr = Serial.read();
    if (*serial_recv_ptr == '\n'){
        *serial_recv_ptr = '\0';
        if (!strcmp("sample", serial_recv)){
            sample(0);
        }
        else if (!strcmp("loopback", serial_recv))  {
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

