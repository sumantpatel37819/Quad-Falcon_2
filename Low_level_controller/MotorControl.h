// MotorControl.h
// Controls 4x DC motors via Adafruit Motor Shield L293D
// Motors: M1=Front-Left, M2=Front-Right, M3=Rear-Left, M4=Rear-Right
// ASSUMPTION: Standard Adafruit Motor Shield V1 (AFMotor library)

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <AFMotor.h>

class MotorControl {
public:
    MotorControl();
    void begin();

    // High-level movement commands
    void forward(uint8_t speed);
    void backward(uint8_t speed);
    void turnLeft(uint8_t speed);
    void turnRight(uint8_t speed);
    void stop();

    // Speed control
    void setSpeed(uint8_t speed);
    uint8_t getSpeed() const { return _currentSpeed; }

private:
    AF_DCMotor _motorFL;  // Front Left  - M1
    AF_DCMotor _motorFR;  // Front Right - M2
    AF_DCMotor _motorRL;  // Rear Left   - M3
    AF_DCMotor _motorRR;  // Rear Right  - M4

    uint8_t _currentSpeed;

    void _setAllSpeeds(uint8_t speed);
    void _runAll(uint8_t dirFL, uint8_t dirFR, uint8_t dirRL, uint8_t dirRR);
};

#endif // MOTOR_CONTROL_H
