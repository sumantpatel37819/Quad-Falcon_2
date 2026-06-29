/*
 * Low_level_controller.ino
 * ========================
 * Quad Falcon 2 — Arduino UNO Low-Level Controller
 *
 * HARDWARE:
 *   - Arduino UNO
 *   - Adafruit Motor Shield L293D (AFMotor library)
 *   - MPU6050 on I2C (SDA=A4, SCL=A5)
 *   - GPS module on SoftwareSerial pins 9(RX) / 10(TX) at 9600 baud
 *   - Raspberry Pi connected via USB Serial at 115200 baud
 *
 * SERIAL PROTOCOL:
 *   Baud: 115200
 *   Commands FROM Pi  (newline terminated): FORWARD <spd>, BACKWARD <spd>,
 *                                           LEFT <spd>, RIGHT <spd>, STOP,
 *                                           ESTOP, SET_SPEED <spd>, PING
 *   Telemetry TO Pi   (~10Hz, JSON lines): {"t":ms,"yaw":...,"lat":...,...}
 *
 * SAFETY:
 *   - Command timeout: if no command received in CMD_TIMEOUT_MS, motors stop
 *   - ESTOP: latching e-stop clears only on STOP command
 *   - IMU calibration during startup (keep robot still for 1 second)
 *
 * LIBRARIES REQUIRED (install via Arduino Library Manager):
 *   - Adafruit Motor Shield Library (v1 - "AFMotor")
 *   - TinyGPS++
 *   - Wire (built-in)
 *   - SoftwareSerial (built-in)
 */

#include <Arduino.h>
#include "MotorControl.h"
#include "IMUReader.h"
#include "GPSReader.h"
#include "CommandParser.h"
#include "TelemetrySerializer.h"

// ======================== CONFIGURATION ========================
static const uint32_t SERIAL_BAUD       = 115200;
static const uint32_t TELEMETRY_INTERVAL_MS = 100;   // 10 Hz
static const uint32_t CMD_TIMEOUT_MS    = 2000;       // 2 second watchdog
static const uint8_t  DEFAULT_SPEED     = 150;

// ======================== GLOBALS ==============================
MotorControl      motors;
IMUReader         imu;
GPSReader         gps;
CommandParser     parser;
// TelemetrySerializer is now fully static, no instance needed

// State tracking
bool       eStopActive       = false;
uint8_t    currentSpeed      = DEFAULT_SPEED;
char       lastCmdStr[16]    = "STOP";
unsigned long lastCmdTime    = 0;
unsigned long lastTelemetryTime = 0;

// ======================== SETUP ================================
void setup() {
    Serial.begin(SERIAL_BAUD);

    // Motor shield init
    motors.begin();
    motors.setSpeed(DEFAULT_SPEED);
    motors.stop();

    // IMU init
    // Wire.begin() MUST be called here in setup before imu.begin().
    // imu.begin() also calls Wire.begin() internally — calling twice is safe.
    Wire.begin();
    delay(500);   // Wait for MPU6050 to power up (important after motor shield init)
    if (!imu.begin()) {
        // If you see this error:
        //   1. Check SDA→A4, SCL→A5 wiring
        //   2. Check MPU6050 VCC is 3.3V or 5V (both work)
        //   3. Check AD0 pin — if HIGH, address is 0x69 (change in MPU6050.h)
        Serial.println("{\"err\":\"IMU_INIT_FAIL\",\"hint\":\"Check SDA=A4 SCL=A5 wiring\"}");
    } else {
        Serial.println("{\"status\":\"IMU_READY\"}");
    }

    // GPS init
    gps.begin(9600);
    Serial.println("{\"status\":\"GPS_INIT\"}");

    // Ready marker for Raspberry Pi
    Serial.println("{\"status\":\"ARDUINO_READY\"}");

    lastCmdTime = millis();
}

// ======================== HELPERS ==============================

void executeCommand(const ParsedCommand& cmd) {
    if (eStopActive && cmd.cmd != RobotCmd::CMD_STOP && cmd.cmd != RobotCmd::CMD_ESTOP) {
        // Reject all motion commands during e-stop
        return;
    }

    switch (cmd.cmd) {
        case RobotCmd::CMD_FORWARD:
            motors.forward(cmd.speed > 0 ? cmd.speed : currentSpeed);
            strncpy(lastCmdStr, "FORWARD", sizeof(lastCmdStr));
            currentSpeed = cmd.speed > 0 ? cmd.speed : currentSpeed;
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_BACKWARD:
            motors.backward(cmd.speed > 0 ? cmd.speed : currentSpeed);
            strncpy(lastCmdStr, "BACKWARD", sizeof(lastCmdStr));
            currentSpeed = cmd.speed > 0 ? cmd.speed : currentSpeed;
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_TURN_LEFT:
            motors.turnLeft(cmd.speed > 0 ? cmd.speed : currentSpeed);
            strncpy(lastCmdStr, "LEFT", sizeof(lastCmdStr));
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_TURN_RIGHT:
            motors.turnRight(cmd.speed > 0 ? cmd.speed : currentSpeed);
            strncpy(lastCmdStr, "RIGHT", sizeof(lastCmdStr));
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_STOP:
            motors.stop();
            strncpy(lastCmdStr, "STOP", sizeof(lastCmdStr));
            eStopActive = false;  // STOP also clears e-stop latch
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_ESTOP:
            motors.stop();
            eStopActive = true;
            strncpy(lastCmdStr, "ESTOP", sizeof(lastCmdStr));
            Serial.println("{\"estop\":1,\"msg\":\"EMERGENCY_STOP\"}");
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_SET_SPEED:
            currentSpeed = cmd.speed;
            motors.setSpeed(currentSpeed);
            strncpy(lastCmdStr, "SET_SPEED", sizeof(lastCmdStr));
            lastCmdTime = millis();
            break;

        case RobotCmd::CMD_PING:
            Serial.println("{\"pong\":1}");
            lastCmdTime = millis();
            break;

        default:
            break;
    }
}

void checkCommandTimeout() {
    if (millis() - lastCmdTime > CMD_TIMEOUT_MS) {
        if (strcmp(lastCmdStr, "STOP") != 0 && strcmp(lastCmdStr, "ESTOP") != 0) {
            motors.stop();
            strncpy(lastCmdStr, "STOP", sizeof(lastCmdStr));
            Serial.println("{\"warn\":\"CMD_TIMEOUT_STOP\"}");
            lastCmdTime = millis();
        }
    }
}

void sendTelemetry() {
    imu.update();
    gps.update();

    TelemetrySerializer::sendPacket(
        imu.getYaw(),
        imu.getPitch(),
        imu.getRoll(),
        imu.getGyroZ(),      // Yaw rate (deg/s)
        imu.getLinAccX(),    // Linear accel X (gravity removed)
        imu.getLinAccY(),
        imu.getLinAccZ(),
        gps.getLat(),
        gps.getLon(),
        gps.getAltitude(),   // Altitude in metres (M8N provides this)
        gps.isValid(),
        gps.getSatCount(),
        gps.getHDOP(),       // M8N HDOP — accuracy indicator
        gps.getSpeed(),
        currentSpeed,
        lastCmdStr,
        eStopActive
    );
}

// ======================== MAIN LOOP ============================
void loop() {
    // 1. Read incoming serial commands character by character
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (parser.feed(c)) {
            executeCommand(parser.getCommand());
        }
    }

    // 2. Command timeout watchdog
    checkCommandTimeout();

    // 3. Update GPS continuously (SoftwareSerial needs regular feeding)
    gps.update();

    // 4. Send telemetry at TELEMETRY_INTERVAL_MS rate
    unsigned long now = millis();
    if (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryTime = now;
        sendTelemetry();
    }
}
