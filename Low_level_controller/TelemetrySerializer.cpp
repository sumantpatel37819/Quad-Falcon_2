// TelemetrySerializer.cpp
// Builds compact JSON telemetry packet

#include "TelemetrySerializer.h"
#include <stdio.h>

const char* TelemetrySerializer::buildPacket(
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
) {
    // Use snprintf to build JSON — safe and bounded
    // lat/lon use %.6f for ~11cm accuracy
    snprintf(_buf, sizeof(_buf),
        "{\"t\":%lu,\"yaw\":%.1f,\"pitch\":%.1f,\"roll\":%.1f,"
        "\"lat\":%.6f,\"lon\":%.6f,\"gps_ok\":%d,\"sats\":%d,"
        "\"gps_spd\":%.1f,\"spd\":%d,\"cmd\":\"%s\",\"estop\":%d}",
        millis(),
        yaw, pitch, roll,
        lat, lon,
        gpsValid ? 1 : 0,
        (int)satCount,
        gpsSpeedKmh,
        (int)motorSpeed,
        lastCmd ? lastCmd : "STOP",
        eStop ? 1 : 0
    );
    return _buf;
}
