# CoolPi

CoolPi controls a Raspberry Pi fan based on the current CPU temperature. It aims to keep the device cool while avoiding unnecessary fan noise.

## Features

* Simple fan control using GPIO
* Configuration file for thresholds and intervals
* Console logging using Python's `logging` module
* Systemd service file for automatic start on boot

## Version

`0.0.1`

## Installation

Run the setup script and follow the prompts to configure the fan controller.

```bash
sudo ./setup.sh
```

The script installs the Python requirements, writes `config/coolpi.conf` with
your answers (or the defaults if you simply press enter) and installs the
systemd service so the controller starts automatically on boot.

## Configuration

`coolpi.conf` contains the following options:

```
[console]
loglevel = 1

[fan]
active = 1        # 1 to enable fan control
temphigh = 50.0   # temperature to switch fan on
templow  = 45.0   # temperature to switch fan off
interval = 5      # measurement interval in seconds
gpio     = 13     # BCM GPIO pin connected to the fan
```

`loglevel` maps to the standard logging levels (0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL).

## Usage

Run the controller manually:

```bash
python3 src/coolpi.py
```

You will see log messages similar to:

```
[2025-06-04 20:00:00] INFO: Fan turned on at 65.3°C
[2025-06-04 20:03:00] INFO: Fan turned off at 49.8°C
```

## License

See `LICENSE` for license information.
