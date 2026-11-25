Issues and Resolutions
======================

Ubuntu 26.04 wifi bug
---------------------
See https://bugs.launchpad.net/ubuntu/+source/network-manager/+bug/2172161 .

With poor connections, wifi retry paths are more likely to be executed. One of those is when the
wifi access point tells the gateway that secrets are incorrect. The gateway's NetworkManager
then goes to registered secrets agents to request _new_credentials from the user. This is observed
with NetworkManager 1.54.3 and observed fixed in 1.58.1 .

With NetworkManager 1.58.1, the following setting causes the NetworkManager to assume that the
provided credentials are correct and that the error was in the communication with the wifi
access point, as opposed to asking for user input.

`sudo nmcli connection modify "Ogallala Guest" connection.auth-retries 0`

