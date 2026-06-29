// TelemetrySerializer.h
// Builds JSON telemetry for Arduino UNO (AVR)
//
// WHY NOT snprintf with %f?
// AVR-libc strips float support from snprintf/printf to save flash memory.
// Using %.1f in snprintf outputs '?' on Arduino UNO/Nano/Mega.
// This class uses dtostrf() for floats and strcat/ultoa for integers — 
// both work correctly on all AVR Arduinos.

#ifndef TELEMETRY_SERIALIZER_H
#define TELEMETRY_SERIALIZER_H

#include <Arduino.h>
#include <math.h>    // isnan(), isinf()

class TelemetrySerializer {
public:
    // Writes one complete JSON line directly to Serial.
    // Returns number of characters written.
    static void sendPacket(
        float   yaw,
        float   pitch,
        float   roll,
        float   gyroZ,
        float   linAccX,
        float   linAccY,
        float   linAccZ,
        double  lat,
        double  lon,
        float   altitude,
        bool    gpsValid,
        uint8_t satCount,
        float   hdop,
        float   gpsSpeedKmh,
        uint8_t motorSpeed,
        const char* lastCmd,
        bool    eStop
    );

private:
    // Guard against NaN/Inf — return 0.0 if invalid float
    static float safe(float v) {
        return (isnan(v) || isinf(v)) ? 0.0f : v;
    }
    static double safeD(double v) {
        return (isnan(v) || isinf(v)) ? 0.0 : v;
    }
};

#endif // TELEMETRY_SERIALIZER_H
