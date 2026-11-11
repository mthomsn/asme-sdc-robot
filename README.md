# ASME Student Design Competition 2026: color-sorting robot (team UR@DC)

Control software for our team's entry in the ASME Student Design Competition. The
robot runs on a Raspberry Pi Zero W and is driven with an Xbox controller over Bluetooth.
It identifies the color of game objects with a TCS34725 sensor and sorts them with a
flipper mechanism, alongside lift and servo mechanisms.

## Hardware

- Raspberry Pi Zero W
- Four TT gear motors for the drive, controlled by PWM through motor drivers
- TT lift motor, N20 motor, flipper (sorting) motor and a hobby servo for the mechanisms
- TCS34725 RGB color sensor on I²C
  ([datasheet](https://cdn-shop.adafruit.com/datasheets/TCS34725.pdf))
- Xbox wireless controller over Bluetooth

## Software

| Path | What it does |
| --- | --- |
| `src/combined.py` | Main program: drive, mechanisms and color sorting, run together on threads |
| `src/joystick.py` | Reads controller input (via `jstest`) and maps sticks and buttons to commands |
| `src/color.py` | Reads the TCS34725 and classifies color from normalized RGB and clear-channel readings |
| `src/startup.sh` | Boot script: waits for Bluetooth, connects the controller, counts down, starts the robot |
| `src/combined2.py`, `combined-m.py`, `interval.py`, `slow.py` | Variants tuned during testing (motor mapping, timing, speed) |
| `archive/` | Earlier experiments: keyboard and Xbox control, 3-wheel omni drive, camera-based detection |

Run on the Pi:

```bash
CONTROLLER_MAC=XX:XX:XX:XX:XX:XX ./src/startup.sh
```

## My part

I'm Matt Thomsen. I wrote:

- **Controller input**: reading the Xbox controller over Bluetooth, the joystick
  mapping, and debugging the raw `/dev/input` data until we switched to `jstest`
- **Drive control**: motor control for the drive, including the early 3-wheel
  omnidirectional drive
- **Color detection and sorting**: the TCS34725 color-classification algorithm,
  tuned for accuracy on the competition colors, and tying it to the sorting motor
- **Startup**: the boot script that auto-connects the controller

## Team

Built with Leigh Arriane Buendia ([@leigharriane](https://github.com/leigharriane)),
Jules Castel ([@JulesCastel](https://github.com/JulesCastel)) and other UR@DC teammates.
The original repo was [JulesCastel/SDC-UR-DC](https://github.com/JulesCastel/SDC-UR-DC).
The full commit history is preserved, so `git log` shows who wrote what.
