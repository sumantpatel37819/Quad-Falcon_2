// IMUReader.cpp
// MPU6050 + Madgwick AHRS — Arduino UNO port
//
// Ported from ESP32 version:
//   - WiFi + WiFiServer removed → data goes over Serial (to Raspberry Pi)
//   - MPU6050.h library used for clean raw reads (same as ESP32 version)
//   - Madgwick filter (same as ESP32 version, same math)
//   - Fixed variable shadowing bug: gx/gy/gz were used for BOTH gyro rates
//     AND the rotated gravity vector — renamed gravity vars to gravX/Y/Z
//   - Linear acceleration = accel_raw - gravity_rotated (via quaternion)
//
// NOTE ON SAMPLE RATE:
//   ESP32 could do 250 Hz. Arduino UNO with Serial + Motor Shield overhead
//   realistically achieves ~80-150 Hz. We use 100 Hz as the target.
//   If you change the loop delay in the main sketch, adjust sampleRateHz
//   in begin() accordingly so the Madgwick filter is tuned correctly.

#include "IMUReader.h"
#include <Arduino.h>
#include <math.h>

IMUReader::IMUReader(float sampleRateHz)
    : _sampleRateHz(sampleRateHz),
      _ready(false),
      _roll(0), _pitch(0), _yaw(0),
      _gyroX(0), _gyroY(0), _gyroZ(0),
      _linAccX(0), _linAccY(0), _linAccZ(0)
{}

// ──────────────────────────────────────────────────────────────────────────────
// begin()  — call once in setup()
// ──────────────────────────────────────────────────────────────────────────────
bool IMUReader::begin() {
    // NOTE: Wire.begin() must be called by the caller (setup()) before this.
    // Do NOT call Wire.begin() here — it resets I2C state if called twice.
    _mpu.initialize();

    if (!_mpu.testConnection()) {
        return false;  // MPU6050 not found
    }

    // Configure ranges — same as ESP32 code:
    //   Accel: ±2g  → sensitivity 16384 LSB/g
    //   Gyro:  ±250 dps → sensitivity 131 LSB/(deg/s)
    _mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
    _mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);

    // Madgwick filter — pass expected sample rate so beta is tuned correctly
    _filter.begin(_sampleRateHz);

    _ready = true;
    return true;
}

// ──────────────────────────────────────────────────────────────────────────────
// update()  — call every loop iteration
// ──────────────────────────────────────────────────────────────────────────────
void IMUReader::update() {
    if (!_ready) return;

    // ── 1. Read raw sensor values ─────────────────────────────────────────────
    int16_t rawAx, rawAy, rawAz;
    int16_t rawGx, rawGy, rawGz;
    _mpu.getMotion6(&rawAx, &rawAy, &rawAz, &rawGx, &rawGy, &rawGz);

    // ── 2. Scale to physical units ────────────────────────────────────────────
    float ax = rawAx / 16384.0f;   // g  (±2g range)
    float ay = rawAy / 16384.0f;
    float az = rawAz / 16384.0f;

    // NOTE: These are gyro rates — NOT to be confused with the gravity vector
    //       below. Original ESP32 code had a shadowing bug where local float
    //       gx/gy/gz re-declared and overwrote these values inside the scope.
    _gyroX = rawGx / 131.0f;       // deg/s  (±250 dps range)
    _gyroY = rawGy / 131.0f;
    _gyroZ = rawGz / 131.0f;

    // ── 3. Update Madgwick filter ─────────────────────────────────────────────
    // updateIMU() = accel + gyro only (no magnetometer)
    // Arguments: gyro deg/s, accel g
    _filter.updateIMU(_gyroX, _gyroY, _gyroZ, ax, ay, az);

    // ── 4. Get Euler angles ───────────────────────────────────────────────────
    _roll  = _filter.getRoll();
    _pitch = _filter.getPitch();
    _yaw   = _filter.getYaw();   // Madgwick yaw has reduced drift vs gyro integration

    // ── 5. Remove gravity using quaternion rotation ───────────────────────────
    // Quaternion components from Madgwick filter
    float q0 = _filter.q0;
    float q1 = _filter.q1;
    float q2 = _filter.q2;
    float q3 = _filter.q3;

    // Rotate gravity vector [0,0,1] from world frame into sensor frame
    // These are the gravity components in the sensor body frame:
    // (renamed to gravX/Y/Z — NOT the gyro variables)
    float gravX =  2.0f * (q1 * q3 - q0 * q2);
    float gravY =  2.0f * (q0 * q1 + q2 * q3);
    float gravZ =  q0*q0 - q1*q1 - q2*q2 + q3*q3;

    // Linear acceleration = measured accel − gravity component
    _linAccX = ax - gravX;
    _linAccY = ay - gravY;
    _linAccZ = az - gravZ;
}
