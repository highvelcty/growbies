from growbies.arduino.arduino import Arduino

def main():
    while True:
        arduino_serial = Arduino()
        try:
            cmd = input("Enter command: ")
            print(arduino_serial.execute(cmd))
        except KeyboardInterrupt:
            break
