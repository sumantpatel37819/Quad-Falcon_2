// IMUReader.h
// MPU6050 + Madgwick AHRS filter for Arduino UNO
//
// Uses:
//   - MPU6050 library (Jeff Rowberg / i2cdevlib) for raw sensor reads
//   - MadgwickAHRS library for quaternion-based attitude estimation
//
// Provides:
//   - Roll, Pitch, Yaw (degrees)
//   - Linear acceleration (gravity removed) in X, Y, Z
//   - Raw gyro rates (deg/s)
//
// REQUIRED LIBRARIES (install via Arduino Library Manager):
//   1. "MPU6050" by Electronic Cats  OR  i2cdevlib MPU6050
//   2. "MadgwickAHRS" by x-io Technologies
//
// ASSUMPTION: MPU6050 at I2C address 0x68 (AD0 low)

#ifndef IMU_READER_H
#define IMU_READER_H

#include <Arduino.h>
#include <Wire.h>
#include <MPU6050.h>
#include <MadgwickAHRS.h>

class IMUReader {
public:
    // sampleRateHz: expected loop call rate (used to init Madgwick beta)
    // Recommended: 100 for Arduino UNO (250 is too fast with serial overhead)
    explicit IMUReader(float sampleRateHz = 100.0f);

    // Call once in setup(). Returns false if MPU6050 not found.
    bool begin();

    // Call every loop iteration — reads sensor + updates filter
    void update();

    // ── Euler angles (degrees) ──────────────────────────────────────
    float getRoll()  const { return _roll;  }
    float getPitch() const { return _pitch; }
    float getYaw()   const { return _yaw;   }

    // ── Gyro rates (degrees / second) ───────────────────────────────
    float getGyroX() const { return _gyroX; }
    float getGyroY() const { return _gyroY; }
    float getGyroZ() const { return _gyroZ; }

    // ── Linear acceleration (gravity removed, in g units) ───────────
    float getLinAccX() const { return _linAccX; }
    float getLinAccY() const { return _linAccY; }
    float getLinAccZ() const { return _linAccZ; }

    bool isReady() const { return _ready; }

private:
    MPU6050  _mpu;
    Madgwick _filter;
    float    _sampleRateHz;
    bool     _ready;

    // Processed values
    float _roll,  _pitch, _yaw;
    float _gyroX, _gyroY, _gyroZ;     // Gyro rates (deg/s)
    float _linAccX, _linAccY, _linAccZ; // Linear accel (gravity removed)
};

#endif // IMU_READER_H
