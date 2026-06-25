// MotorControl.cpp
// Implementation of 4-motor differential drive control via Adafruit Motor Shield L293D

#include "MotorControl.h"

MotorControl::MotorControl()
    : _motorFL(1),   // M1
      _motorFR(2),   // M2
      _motorRL(3),   // M3
      _motorRR(4),   // M4
      _currentSpeed(150)
{}

void MotorControl::begin() {
    _setAllSpeeds(_currentSpeed);
    stop();
}

void MotorControl::setSpeed(uint8_t speed) {
    _currentSpeed = speed;
    _setAllSpeeds(speed);
}

void MotorControl::forward(uint8_t speed) {
    _currentSpeed = speed;
    _setAllSpeeds(speed);
    _runAll(FORWARD, FORWARD, FORWARD, FORWARD);
}

void MotorControl::backward(uint8_t speed) {
    _currentSpeed = speed;
    _setAllSpeeds(speed);
    _runAll(BACKWARD, BACKWARD, BACKWARD, BACKWARD);
}

void MotorControl::turnLeft(uint8_t speed) {
    _currentSpeed = speed;
    _setAllSpeeds(speed);
    // Left side backward, right side forward → spin left in place
    _runAll(BACKWARD, FORWARD, BACKWARD, FORWARD);
}

void MotorControl::turnRight(uint8_t speed) {
    _currentSpeed = speed;
    _setAllSpeeds(speed);
    // Left side forward, right side backward → spin right in place
    _runAll(FORWARD, BACKWARD, FORWARD, BACKWARD);
}

void MotorControl::stop() {
    _runAll(RELEASE, RELEASE, RELEASE, RELEASE);
}

// ---------- Private Helpers ----------

void MotorControl::_setAllSpeeds(uint8_t speed) {
    _motorFL.setSpeed(speed);
    _motorFR.setSpeed(speed);
    _motorRL.setSpeed(speed);
    _motorRR.setSpeed(speed);
}

void MotorControl::_runAll(uint8_t dirFL, uint8_t dirFR,
                            uint8_t dirRL, uint8_t dirRR) {
    _motorFL.run(dirFL);
    _motorFR.run(dirFR);
    _motorRL.run(dirRL);
    _motorRR.run(dirRR);
}
