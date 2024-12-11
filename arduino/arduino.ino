char serial_recv[1024];
char* serial_recv_ptr = &serial_recv[0];

void setup() {
  Serial.begin(115200);
  memset(serial_recv, 0, sizeof(serial_recv));
}

void loop() {
    while (!Serial.available());
    *serial_recv_ptr = Serial.read();
    if (*serial_recv_ptr == '\n'){
        ++serial_recv_ptr;
        *serial_recv_ptr = '\0';
        Serial.print("Command: ");
        Serial.print(serial_recv);
        serial_recv_ptr = &serial_recv[0];
    }
    else{
        ++serial_recv_ptr;
    }
}

void Sample(){
  Serial.print("value: ");
  Serial.print(analogRead(0));
  Serial.print("\n");
}