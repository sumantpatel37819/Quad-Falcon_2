// CommandParser.h
// Parses text commands received over Serial from Raspberry Pi
// Protocol: one command per line, terminated by '\n'
//
// *** IMPORTANT ***
// AFMotor.h defines these as raw C preprocessor macros:
//   #define FORWARD  1
//   #define BACKWARD 2
//   #define BRAKE    3
//   #define RELEASE  4
// Our enum uses CMD_ prefix on all values to avoid the macro clash.
//
// Supported commands (as text strings from Pi):
//   FORWARD <speed>      Move forward at given speed (0-255)
//   BACKWARD <speed>     Move backward
//   LEFT <speed>         Turn left (spin in place)
//   RIGHT <speed>        Turn right (spin in place)
//   STOP                 Stop all motors (soft stop)
//   ESTOP                Emergency stop (immediate, sets e-stop flag)
//   SET_SPEED <value>    Set default speed without moving
//   PING                 Pi heartbeat — responds with PONG

#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

#include <Arduino.h>

// All values prefixed with CMD_ to avoid collision with AFMotor.h macros
// (AFMotor.h: #define FORWARD 1, #define BACKWARD 2, etc.)
enum class RobotCmd {
    CMD_NONE,
    CMD_FORWARD,
    CMD_BACKWARD,
    CMD_TURN_LEFT,
    CMD_TURN_RIGHT,
    CMD_STOP,
    CMD_ESTOP,
    CMD_SET_SPEED,
    CMD_PING
};

struct ParsedCommand {
    RobotCmd cmd;
    uint8_t  speed;   // 0-255, valid for FORWARD/BACKWARD/LEFT/RIGHT/SET_SPEED
};

class CommandParser {
public:
    CommandParser();

    // Feed incoming Serial byte; returns true when a full command is ready
    bool feed(char c);

    // Get the last parsed command (call after feed() returns true)
    ParsedCommand getCommand() const { return _parsed; }

    // Reset internal buffer
    void reset();

private:
    static const uint8_t BUF_SIZE = 64;
    char _buf[BUF_SIZE];
    uint8_t _idx;
    ParsedCommand _parsed;

    bool _parse();
};

#endif // COMMAND_PARSER_H
