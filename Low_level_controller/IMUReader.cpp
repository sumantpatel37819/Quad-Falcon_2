// IMUReader.cpp
// MPU6050 I2C reading with complementary filter for pitch/roll/yaw
// Yaw is integrated from gyro Z (drifts over time — acceptable for short-range navigation)

#include "IMUReader.h"
#include <math.h>

IMUReader::IMUReader()
    : _ax(0), _ay(0), _az(0), _gx(0), _gy(0), _gz(0),
      _gyroOffsetX(0), _gyroOffsetY(0), _gyroOffsetZ(0),
      _pitch(0), _roll(0), _yaw(0),
      _lastUpdateMs(0), _ready(false)
{}

bool IMUReader::begin() {
    Wire.begin();
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x6B);  // PWR_MGMT_1
    Wire.write(0x00);  // Wake up MPU6050
    uint8_t err = Wire.endTransmission(true);
    if (err != 0) return false;

    // Set accelerometer range ±2g
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x1C);
    Wire.write(0x00);
    Wire.endTransmission(true);

    // Set gyro range ±250 deg/s
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x1B);
    Wire.write(0x00);
    Wire.endTransmission(true);

    _lastUpdateMs = millis();
    _ready = true;
    return true;
}

void IMUReader::calibrate(uint16_t samples) {
    float sumX = 0, sumY = 0, sumZ = 0;
    for (uint16_t i = 0; i < samples; i++) {
        _readRaw();
        sumX += _gx;
        sumY += _gy;
        sumZ += _gz;
        delay(5);
    }
    _gyroOffsetX = sumX / samples;
    _gyroOffsetY = sumY / samples;
    _gyroOffsetZ = sumZ / samples;
}

void IMUReader::update() {
    if (!_ready) return;
    if (!_readRaw()) return;

    unsigned long now = millis();
    float dt = (now - _lastUpdateMs) / 1000.0f;
    _lastUpdateMs = now;
    if (dt <= 0 || dt > 0.5f) return;  // Sanity check

    // Scale factors: accel = raw/16384 [g], gyro = raw/131 [deg/s] for ±2g/±250dps
    float ax = _ax / 16384.0f;
    float ay = _ay / 16384.0f;
    float az = _az / 16384.0f;

    float gx = (_gx - _gyroOffsetX) / 131.0f;  // deg/s
    float gy = (_gy - _gyroOffsetY) / 131.0f;
    float gz = (_gz - _gyroOffsetZ) / 131.0f;

    // Accelerometer-based pitch and roll (degrees)
    float accelPitch = atan2(ay, sqrt(ax * ax + az * az)) * 180.0f / M_PI;
    float accelRoll  = atan2(-ax, az) * 180.0f / M_PI;

    // Complementary filter: fuse gyro integration with accel correction
    _pitch = ALPHA * (_pitch + gy * dt) + (1.0f - ALPHA) * accelPitch;
    _roll  = ALPHA * (_roll  + gx * dt) + (1.0f - ALPHA) * accelRoll;

    // Yaw from gyro integration only (no magnetometer available)
    _yaw += gz * dt;

    // Normalize yaw to [-180, 180]
    if (_yaw >  180.0f) _yaw -= 360.0f;
    if (_yaw < -180.0f) _yaw += 360.0f;
}

bool IMUReader::_readRaw() {
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B);  // Start at ACCEL_XOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, (uint8_t)14, (uint8_t)true);

    if (Wire.available() < 14) return false;

    _ax = (Wire.read() << 8) | Wire.read();
    _ay = (Wire.read() << 8) | Wire.read();
    _az = (Wire.read() << 8) | Wire.read();
    Wire.read(); Wire.read();  // Temperature — skip
    _gx = (Wire.read() << 8) | Wire.read();
    _gy = (Wire.read() << 8) | Wire.read();
    _gz = (Wire.read() << 8) | Wire.read();

    return true;
}
