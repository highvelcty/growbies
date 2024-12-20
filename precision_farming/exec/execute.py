from typing import Union

from precision_farming.arduino.arduino import arduino_serial

def main():
    while True:
        try:
            cmd = input("Enter command: ")
            print(arduino_serial.execute(cmd))
        except KeyboardInterrupt:
            break
