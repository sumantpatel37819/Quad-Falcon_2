// GPSReader.cpp
// u-blox NEO-M8N GPS via TinyGPS++ on SoftwareSerial (A0/A1 pins)
//
// u-blox M8N key facts:
//   - Default baud: 9600 (factory default — but some vendors ship at 38400)
//   - Default NMEA sentences: GGA, GLL, GSA, GSV, RMC, VTG
//   - Default update rate: 1 Hz (can be increased to 10 Hz via UBX config)
//   - TinyGPS++ parses: RMC (lat/lon/speed) + GGA (altitude/sats/hdop)
//   - Fix indicator: module LED blinks once per second when fix acquired
//
// TROUBLESHOOTING — if gps_ok always 0:
//   1. Place module near window / outdoors (needs sky view)
//   2. Wait 30-90 seconds for first cold fix
//   3. If no NMEA data at all — try 38400 baud instead of 9600
//   4. Confirm wiring: GPS TX → A0, GPS RX → A1

#include "GPSReader.h"

GPSReader::GPSReader(uint8_t rxPin, uint8_t txPin)
    : _serial(rxPin, txPin)
{}

void GPSReader::begin(uint32_t baud) {
    _serial.begin(baud);
    // SoftwareSerial listen() needed when there are multiple SoftwareSerial objects
    _serial.listen();
}

void GPSReader::update() {
    // Feed ALL available bytes into TinyGPS++ parser every call
    // IMPORTANT: Call this as often as possible in loop() — not just
    // in the 10Hz telemetry timer — otherwise NMEA sentences get lost
    while (_serial.available() > 0) {
        char c = (char)_serial.read();
        _gps.encode(c);
    }
}

bool GPSReader::isValid() const {
    // isUpdated() resets after first read — use isValid() for persistent check
    return _gps.location.isValid();
}

double GPSReader::getLat() const {
    return _gps.location.isValid() ? _gps.location.lat() : 0.0;
}

double GPSReader::getLon() const {
    return _gps.location.isValid() ? _gps.location.lng() : 0.0;
}

float GPSReader::getAltitude() const {
    return _gps.altitude.isValid() ? (float)_gps.altitude.meters() : 0.0f;
}

float GPSReader::getSpeed() const {
    return _gps.speed.isValid() ? (float)_gps.speed.kmph() : 0.0f;
}

uint8_t GPSReader::getSatCount() const {
    return _gps.satellites.isValid() ? (uint8_t)_gps.satellites.value() : 0;
}

float GPSReader::getHDOP() const {
    // HDOP < 1.0 = excellent, < 2.0 = good, > 5.0 = poor
    return _gps.hdop.isValid() ? (float)_gps.hdop.hdop() : 99.9f;
}

// Additional M8N-specific helpers
uint32_t GPSReader::getAge() const {
    // Milliseconds since last valid fix — useful for staleness check
    return _gps.location.isValid() ? _gps.location.age() : 0xFFFFFFFF;
}

bool GPSReader::hasFreshFix() const {
    // Fix is "fresh" if updated in last 2 seconds
    return isValid() && (getAge() < 2000);
}
