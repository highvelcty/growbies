from growbies.arduino.arduino import ArduinoSerial

def main():
    while True:
        arduino_serial = ArduinoSerial()
        try:
            cmd = input("Enter command: ")
            print(arduino_serial.execute(cmd))
        except KeyboardInterrupt:
            break
