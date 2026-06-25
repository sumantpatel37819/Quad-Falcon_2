// TelemetrySerializer.h
// Serializes robot state into a JSON line for sending to Raspberry Pi
// Output format (compact JSON, newline terminated):
// {"t":ms,"yaw":45.2,"pitch":2.1,"roll":-1.5,"lat":28.61,"lon":77.20,"gps_ok":1,"sats":6,"spd":150,"cmd":"FORWARD","estop":0}

#ifndef TELEMETRY_SERIALIZER_H
#define TELEMETRY_SERIALIZER_H

#include <Arduino.h>

class TelemetrySerializer {
public:
    // Returns a pointer to an internal static buffer — use immediately or copy
    const char* buildPacket(
        float   yaw,
        float   pitch,
        float   roll,
        double  lat,
        double  lon,
        bool    gpsValid,
        uint8_t satCount,
        float   gpsSpeedKmh,
        uint8_t motorSpeed,
        const char* lastCmd,
        bool    eStop
    );

private:
    char _buf[256];
};

#endif // TELEMETRY_SERIALIZER_H
