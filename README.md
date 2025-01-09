Python Virtual Environment
==========================
Create a virtual environment with:

```
$ python3 -m venv <path_to_venv>
```

Activate the virtual environment with:

```
$ source <path_to_venv>/bin/activate
```

There are required and optional dependencies. To install all required and optional dependencies:
```
$ pip install -e .[ALL]
```

See [setup.cfg](setup.cfg) for other optional dependencies.

Other Setup
===========
To allow non-root access to the serial port, add the user to the `dialout` group. Be sure to 
logout/login for the changes to take effect.

Arduino Setup
=============
- Install [arduino-cli](https://arduino.github.io/arduino-cli/1.1/installation/)
- Install arduino uno board platform `./arduino-cli core install arduino:avr`

RPM Dependencies
================
- opensuse
  - python3<xx>
  - python3<xx>-tk
- ubuntu 20.04
  - add-apt-repository ppa:deadsnakes/ppa 
  - python3<xx>
  - python3<xx>-tk
  - python3<xx>-venv

Notes
=====
- There is a bug with matplotlib and python 3.14
  - https://github.com/matplotlib/matplotlib/issues/29185