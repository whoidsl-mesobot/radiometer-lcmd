Radiometer LCM Daemon
=====================

Prerequisites
-------------

- Install python3 and python3-pip.

- Install LCM with python3 bindings.

Install
-------

```shell
lcm-gen --python --ppath src/radiometer_lcmd/lcmtypes src/radiometer_lcmd/lcmtypes/*.lcm
python3 -m pip install .
# ^ to install the daemons and lcmtypes under `PYTHONPATH`
```

### TO-DO ###

- [ ] revise the `pip install` sources to run `lcm-gen` automagically

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

Replay or Simulate
------------------

If you want to use the photon flux density transform as it was recorded in an existing log, but tinker with the ambient downwelling photon flux estimator (de-spiking filter), the only downstream radiometer process you need to run is the ambient estimator. If you also want to apply a calibration to the raw data to transform it into a photon flux, you need to start both downstream processes.

N.B.* You can find the command line for each of the radiometer processes in the `systemd` service files under `systemd/system`. If you have a user & group for mesobot on your development machine, you can install those service files and start the processes with `systemctl` the same way we do on the `tx2`.

You can replay the existing log with `lcm-logplayer` or `lcm-logplayer-gui`, depending on your preferences. I recommend only replaying channels you actually need.

### Ambient Estimator Only ###

- In one terminal, start the process for the ambient downwelling photon flux estimator
  ```
  /usr/bin/env python -m radiometer_lcmd.ambient_downwelling_photon_flux_estimator -w 200 -s u -c RAD1fd
  ```

- In another terminal, start the logger (so you can unpack and analyze the data later in `python` or `matlab`).
  ```
  lcm-logger replay.lcmlog
  ```

- In another terminal, replay the log, but only the channels you need (at least `RAD1fd`).
  ```
  lcm-logplayer -e "(DQo)|(RAD1t)|(RAD1fd)" mesobot045.lcmlog
  ```

- Watch using `mesobot-spy` and you will see `RAD1u` at 20 Hz, once it has collected enough history.

### Transform & Ambient Estimator ###

- Do the first and second steps above for the ambient estimator only.

- In another terminal, start the process for the photon flux transform:
  ```
  /usr/bin/env python3 -m radiometer_lcmd.photon_flux_transform -c RAD1t
  ```

- Do the last step above for the ambient estimator only, but do not let `lcm-logplayer` publish `RAD1fd` because now you have the transform process publishing it instead.
  ```
  lcm-logplayer -e "(DQo)|(RAD1t)" mesobot045.lcmlog
  ```
