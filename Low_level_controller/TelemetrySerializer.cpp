// TelemetrySerializer.cpp
// Sends telemetry via direct Serial.print to avoid AVR snprintf %f limitations
// AVR (Arduino UNO/Mega) does not support %f in sprintf, it outputs '?'
// We also use safe() to prevent NaN/Inf breaking JSON parsing on the Pi.

#include "TelemetrySerializer.h"

void TelemetrySerializer::sendPacket(
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
) {
    // We send directly to Serial to avoid memory allocation and sprintf limits
    Serial.print("{\"t\":");
    Serial.print(millis());
    
    Serial.print(",\"yaw\":");
    Serial.print(safe(yaw), 1);
    Serial.print(",\"pitch\":");
    Serial.print(safe(pitch), 1);
    Serial.print(",\"roll\":");
    Serial.print(safe(roll), 1);
    
    Serial.print(",\"gyro_z\":");
    Serial.print(safe(gyroZ), 2);
    
    Serial.print(",\"lin_ax\":");
    Serial.print(safe(linAccX), 3);
    Serial.print(",\"lin_ay\":");
    Serial.print(safe(linAccY), 3);
    Serial.print(",\"lin_az\":");
    Serial.print(safe(linAccZ), 3);
    
    Serial.print(",\"lat\":");
    Serial.print(safeD(lat), 6);
    Serial.print(",\"lon\":");
    Serial.print(safeD(lon), 6);
    Serial.print(",\"alt\":");
    Serial.print(safe(altitude), 1);
    
    Serial.print(",\"gps_ok\":");
    Serial.print(gpsValid ? 1 : 0);
    Serial.print(",\"sats\":");
    Serial.print(satCount);
    Serial.print(",\"hdop\":");
    Serial.print(safe(hdop), 1);
    Serial.print(",\"gps_spd\":");
    Serial.print(safe(gpsSpeedKmh), 1);
    
    Serial.print(",\"spd\":");
    Serial.print(motorSpeed);
    Serial.print(",\"cmd\":\"");
    Serial.print(lastCmd ? lastCmd : "STOP");
    Serial.print("\",\"estop\":");
    Serial.print(eStop ? 1 : 0);
    
    Serial.println("}");
}
