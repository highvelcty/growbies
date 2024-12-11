import time

import serial


arduino = serial.Serial(port='/dev/ttyACM0',  baudrate=115200, timeout=10)


def write_read(data):
    data = data + '\n'
    arduino.write(data.encode())
    data = arduino.readline()
    return  data


while True:
    num = input("Enter a number: ")
    value  = write_read(num)
    print(value)


# def main():
    # ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
    # ser.write('hello'.encode())
    # time.sleep(.05)
    # data = ser.readline(256)
    # print(f'received: {data}')
