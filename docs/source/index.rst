Gateway Documentation
=====================
The gateway is written in python for Linux. It is currently built as a debian package, with plans
to release via RPM in the near future.

Features
--------
- systemd process
- Executed as ``growbies:growbies`` without root privileges.
- user space communication via ``/run/growbies/``
- postgres database
- A python thread per connected device
- logging to ``/var/log/growbies/growbies.log``
- configuration at ``/etc/growbies/growbies.cfg``

Communication Protocol
----------------------
.. code-block:: text

                 Command or Response
        +-----------------------------------+
        |                                   |
        |  +--------+------+---------+      |
        |  |  Type  |  ID  | Version |      |
        |  +--------+------+---------+      |
        |  |          Payload          |    |
        |  +---------------------------+    |
        |                                   |
        +-----------------------------------+
                         |
                         v
                      Packet
        +-----------------------------------+
        |          Command / Response       |
        |  +--------+------+---------+      |
        |  |  Type  |  ID  | Version |      |
        |  +--------+------+---------+      |
        |  |          Payload          |    |
        |  +---------------------------+    |
        |  |       CRC-CCITT-16        |    |
        |  +---------------------------+    |
        +-----------------------------------+
                         |
                         v
                    SLIP Frame
        +-----------------------------------+
        |          SLIP-encoded             |
        |             Packet                |
        |                                   |
        |      SLIP delimiters / escaping   |
        +-----------------------------------+

Growbies devices use a command-response transactional model. Retry commands on error. Use the ``ID``
field in the packet header to synchronize.

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
