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

There are required and optional dependencies.

To install all required and optional dependencies:

```
$ pip install -e .[BUILD,TESTS]
```

To install required dependencies:

```
$ pip install -e .
```

To install optional `BUILD` dependencies:

```
$ pip install -e .[BUILD]
```

To install optional `TESTS` dependencies:

```
$ pip install -e .[TESTS]
```

Other Setup
===========
To allow non-root access to the serial port, add the user to the `dialout` group. Be sure to 
logout/login for the changes to take effect.

Arduino Setup
=============
- Install [arduino-cli](https://arduino.github.io/arduino-cli/1.1/installation/)
- Install arduino uno board platform `./arduino-cli core install arduino:avr`