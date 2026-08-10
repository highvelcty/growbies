Summary
=======
A feedback-control, based on networks of things and machine learning, for agriculture.

In development. 

![growbies.png](docs/source/binary/growbies.png)

Credits
=======

- https://github.com/bogde/HX711/

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
Installing [platformio udev rules](https://docs.platformio.org/en/latest/core/installation/udev-rules.html) 
made the /dev/tty* devices accessible from within a rootless podman container.

Debian Installation
===================
- `sudo apt install ./growbies*.deb`
- Add User to `growbies` group. A `growbies` group is created at package installation time. This 
  group can access the `growbies` systemd service. Add your user to this group to gain access to 
  the client:
  - `sudo usermod -aG growbies <username>`
  - Logout and back in.

Arg Complete Setup (Optional)
=============================
Growbies supports CLI tab completion via the pip package `argcomplete`. To install and configure:

- install `argcomplete` via one of the following methods
  - `sudo pip install argcomplete`
  - `sudo apt install python3-argcomplete`
- `sudo activate-global-python-argcomplete`
- `echo 'eval "$(register-python-argcomplete growbies)"' >> ~/.bashrc`
- `source ~/.bashrc`

Notes
=====
- There is a bug with matplotlib and python 3.14. 
  - https://github.com/matplotlib/matplotlib/issues/29185
  - fix at https://github.com/tacaswell/matplotlib/commit/60903f0b0cf6b50b2fdc84ce205b9d6cb9f65de7
    - thank you
