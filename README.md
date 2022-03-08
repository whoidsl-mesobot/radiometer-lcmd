Radiometer LCM Daemon
=====================

Prerequisites
-------------

- Install python3 and python3-pip.

- Install LCM with python3 bindings.

Install
-------

```shell
lcm-gen --python --ppath radiometer_lcmtypes radiometer_lcmtypes/*.lcm
python3 -m pip install . # to install the lcmtypes under `PYTHONPATH`
```

Troubleshoot
------------

The radiometer serial communications are currently wired to ttyUSB1 on the tx2 (after passing through the offboard communications isolation circuit on the LCB).

To test raw communications, stop the dæmon and use `picocom`:

```shell
mesobot@tx2 $ sudo systemctl stop radiometer-lcmd.service
mesobot@tx2 $ picocom -b38400 /dev/ttyUSB1
```

The radiometer should be streaming binary data (it will look garbled in `picocom`).

To power cycle the radiometer, use a different terminal session, this time on the mb3:

```shell
root@mb3 # bot restart radiometer
```

This turns off power, isolates the LCB, and restores power *after a delay of several seconds*. The delay is important for the radiometer circuitry, so if you use `bot stop radiometer` followed by `bot start radiometer` be sure to give it at least ten seconds between the commands.

Once you have confirmed the radiometer streams binary data when powered on (so the wiring is all correct, etc.) you can restart the dæmon on the tx2:

```shell
mesobot@tx2 $ sudo systemctl restart radiometer-lcmd.service
mesobot@tx2 $ systemctl status radiometer-lcmd.service
mesobot@tx2 $ journalctl -fu radiometer-lcmd.service
```

If the dæmon somehow gets disabled at startup, enable it with:

```shell
mesobot@tx2 $ sudo systemctl enable radiometer-lcmd.service
```

When the radiometer is streaming and the dæmon is running, you should see LCM messages published on channel RAD1t & RAD1p. If the realtime filters are enabled as well, you should also see LCM messages on additional channels like RAD1u.