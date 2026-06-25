# Quad Falcon 2 — Robot Control System

A complete 3-layer autonomous mobile robot system.

## Architecture

```
[Laptop Dashboard]  ←WebSocket/REST→  [Raspberry Pi 3B]  ←USB Serial 115200→  [Arduino UNO]
  React + Vite                          FastAPI + Python                          Motors + Sensors
  TypeScript + Tailwind                 OpenCV + asyncio                          MPU6050 + GPS
  Zustand state                         Camera + ORB                              Motor Shield L293D
```

---

## Quick Start

### 1. Arduino (Low_level_controller/)

**Required Libraries** (install via Arduino Library Manager):
- `AFMotor` (Adafruit Motor Shield Library V1)
- `TinyGPS++`
- `Wire` (built-in)
- `SoftwareSerial` (built-in)

**Steps:**
1. Open `Low_level_controller.ino` in Arduino IDE
2. Select board: **Arduino UNO**
3. Upload to Arduino
4. Keep robot still for ~1 second after power-on (IMU calibration)

---

### 2. Raspberry Pi Backend (high_level_controller/)

**Setup on Raspberry Pi 3B:**

```bash
# Install Python 3 dependencies
cd high_level_controller
pip3 install -r requirements.txt

# Enable camera
sudo raspi-config  → Interface Options → Camera → Enable

# Find Arduino serial port
ls /dev/ttyUSB* /dev/ttyACM*   # Usually /dev/ttyACM0 or /dev/ttyUSB0

# Set port if different from default
export SERIAL_PORT=/dev/ttyACM0

# Run the brain
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Or run in background:**
```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > robot.log 2>&1 &
```

**Configuration** — edit `config.py`:
- `SERIAL_PORT` — Arduino USB serial device
- `CAMERA_INDEX` — Camera device index (0 for Pi camera via V4L2)
- `PI_URL` etc.

---

### 3. Laptop Dashboard (DashBoard/)

**Setup:**

```bash
cd DashBoard

# Edit .env to point to your Pi's IP
# Change raspberrypi.local to your Pi's IP if mDNS doesn't work
echo "VITE_PI_URL=http://192.168.x.x:8000" > .env
echo "VITE_PI_WS_URL=ws://192.168.x.x:8000/ws" >> .env

# Install dependencies
npm install

# Start dashboard
npm run dev
```

Open: **http://localhost:5173**

---

## Serial Protocol Reference

### Commands: Laptop/Pi → Arduino (newline terminated)
| Command | Description |
|---|---|
| `FORWARD <speed>` | Move forward at speed (0-255) |
| `BACKWARD <speed>` | Move backward |
| `LEFT <speed>` | Turn left (spin in place) |
| `RIGHT <speed>` | Turn right (spin in place) |
| `STOP` | Soft stop all motors |
| `ESTOP` | Emergency stop (latching) |
| `SET_SPEED <value>` | Set default speed |
| `PING` | Heartbeat check |

### Telemetry: Arduino → Pi (~10 Hz JSON lines)
```json
{"t":45231,"yaw":45.2,"pitch":2.1,"roll":-1.5,"lat":28.613939,"lon":77.209023,"gps_ok":1,"sats":6,"gps_spd":0.0,"spd":150,"cmd":"FORWARD","estop":0}
```

---

## REST API Reference (Pi Backend)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/control/command` | Send motor command |
| POST | `/control/mode` | Change mode (IDLE/MANUAL/AUTONOMOUS/RETURN_HOME) |
| POST | `/control/return_home` | Trigger return to home |
| POST | `/control/estop` | Emergency stop |
| POST | `/control/speed` | Set motor speed |
| GET | `/control/status` | Full status snapshot |
| GET | `/control/path` | Recorded waypoints |
| POST | `/control/path/reset` | Clear path |
| GET | `/video/stream` | MJPEG camera stream |
| WS | `/ws` | WebSocket telemetry |
| GET | `/health` | Health check |

---

## Hardware Wiring

```
Arduino UNO:
  SDA (A4)  ── MPU6050 SDA
  SCL (A5)  ── MPU6050 SCL
  Pin 9     ── GPS TX (RX pin for SoftwareSerial)
  Pin 10    ── GPS RX (TX pin for SoftwareSerial)
  USB       ── Raspberry Pi USB port

Adafruit Motor Shield (stacked on UNO):
  M1        ── Front Left Motor
  M2        ── Front Right Motor
  M3        ── Rear Left Motor
  M4        ── Rear Right Motor
```

---

## Assumptions & Limitations

1. **IMU Yaw Drift**: MPU6050 without magnetometer — yaw drifts over time. For long missions, add a HMC5883L magnetometer.
2. **ORB Odometry**: Provides relative motion cues only, not metric scale. Used as supplementary data.
3. **GPS Indoors**: GPS won't work indoors. System falls back to dead-reckoning automatically.
4. **Camera**: Tested with Pi Camera via V4L2 (index 0). USB webcam also works.
5. **Return Home**: Accuracy depends on GPS quality or dead-reckoning drift over distance.
6. **AFMotor**: Uses AFMotor V1 library. If using Motor Shield V2, switch to `Adafruit_MotorShield` V2 library.

---

## Future Upgrades

- Add magnetometer (HMC5883L) for drift-free yaw
- Add ultrasonic sensors (HC-SR04) as backup obstacle detection
- Implement PID controller for heading hold during autonomous mode
- Add ROS2 bridge for full nav-stack compatibility
- Add WebRTC for lower-latency video
- Implement SLAM using ORB-SLAM3 on a more powerful host
- Add LCD status display via I2C on Pi
