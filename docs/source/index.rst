Gateway Documentation
=====================
The gateway is written in python for Linux. It is currently built as a debian package, with plans
to release via RPM in the near future.

- The gateway is a systemd process.
- User's communicate with it via files at ``/run/growbies/``.
- A postgres database provides data storage.
- There is a python thread (worker) per connected device.
- USB protocol
    - `SLIP <https://en.wikipedia.org/wiki/Serial_Line_Internet_Protocol>`_ payload
    - payload within CRC protected packet
    - packet number in command / response
- logging to ``/var/log/growbies/growbies.log``
- configuration at ``/etc/growbies/growbies.cfg``

Building
--------
Debian
~~~~~~
1. Go to the ``pkg/deb`` directory
2. ``make``
3. The output will be at ``pkg/deb/dist/growbies_<version>_all.deb``

Links
-----
- `Source Repository <https://github.com/highvelcty/growbies/>`_
