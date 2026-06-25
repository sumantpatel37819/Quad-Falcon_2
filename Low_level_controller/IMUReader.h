// IMUReader.h
// MPU6050 IMU reading via I2C (Wire library)
// Provides yaw, pitch, roll using complementary filter
// ASSUMPTION: MPU6050 at default I2C address 0x68

#ifndef IMU_READER_H
#define IMU_READER_H

#include <Wire.h>

class IMUReader {
public:
    IMUReader();
    bool begin();
    void update();

    float getYaw()   const { return _yaw; }
    float getPitch() const { return _pitch; }
    float getRoll()  const { return _roll; }
    bool  isReady()  const { return _ready; }

    // Calibrate gyro offsets (call during setup, keep robot still)
    void calibrate(uint16_t samples = 200);

private:
    static const uint8_t MPU_ADDR = 0x68;

    // Raw sensor data
    int16_t _ax, _ay, _az;
    int16_t _gx, _gy, _gz;

    // Calibration offsets
    float _gyroOffsetX, _gyroOffsetY, _gyroOffsetZ;

    // Filtered angles
    float _pitch, _roll, _yaw;

    unsigned long _lastUpdateMs;
    bool _ready;

    // Complementary filter coefficient
    static constexpr float ALPHA = 0.96f;

    bool _readRaw();
};

#endif // IMU_READER_H
