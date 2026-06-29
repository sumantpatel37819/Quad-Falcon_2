// CommandParser.cpp
// Incremental line-based command parser for Serial commands from Raspberry Pi
// Uses CMD_ prefixed enum values to avoid AFMotor.h macro collisions

#include "CommandParser.h"
#include <string.h>
#include <stdlib.h>

CommandParser::CommandParser() : _idx(0) {
    memset(_buf, 0, sizeof(_buf));
    _parsed = {RobotCmd::CMD_NONE, 0};
}

bool CommandParser::feed(char c) {
    if (c == '\r') return false;  // Ignore carriage returns

    if (c == '\n') {
        _buf[_idx] = '\0';
        bool result = _parse();
        reset();
        return result;
    }

    if (_idx < BUF_SIZE - 1) {
        _buf[_idx++] = c;
    }
    return false;
}

void CommandParser::reset() {
    _idx = 0;
    memset(_buf, 0, sizeof(_buf));
}

bool CommandParser::_parse() {
    if (_idx == 0) return false;

    // Tokenize: command is first word, optional second word is speed
    char* token = strtok(_buf, " ");
    if (!token) return false;

    char cmdStr[32];
    strncpy(cmdStr, token, sizeof(cmdStr) - 1);
    cmdStr[sizeof(cmdStr) - 1] = '\0';

    char* speedToken = strtok(nullptr, " ");
    uint8_t speedVal = 0;
    if (speedToken) {
        int v = atoi(speedToken);
        speedVal = (uint8_t)constrain(v, 0, 255);
    }

    _parsed.speed = speedVal;

    // Map command string to enum (CMD_ prefixed to avoid AFMotor macro clash)
    if (strcmp(cmdStr, "FORWARD") == 0) {
        _parsed.cmd = RobotCmd::CMD_FORWARD;
    } else if (strcmp(cmdStr, "BACKWARD") == 0) {
        _parsed.cmd = RobotCmd::CMD_BACKWARD;
    } else if (strcmp(cmdStr, "LEFT") == 0) {
        _parsed.cmd = RobotCmd::CMD_TURN_LEFT;
    } else if (strcmp(cmdStr, "RIGHT") == 0) {
        _parsed.cmd = RobotCmd::CMD_TURN_RIGHT;
    } else if (strcmp(cmdStr, "STOP") == 0) {
        _parsed.cmd = RobotCmd::CMD_STOP;
        _parsed.speed = 0;
    } else if (strcmp(cmdStr, "ESTOP") == 0) {
        _parsed.cmd = RobotCmd::CMD_ESTOP;
        _parsed.speed = 0;
    } else if (strcmp(cmdStr, "SET_SPEED") == 0) {
        _parsed.cmd = RobotCmd::CMD_SET_SPEED;
    } else if (strcmp(cmdStr, "PING") == 0) {
        _parsed.cmd = RobotCmd::CMD_PING;
    } else {
        _parsed.cmd = RobotCmd::CMD_NONE;
        return false;
    }

    return true;
}
