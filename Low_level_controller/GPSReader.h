// GPSReader.h
// u-blox NEO-M8N GPS reader via SoftwareSerial + TinyGPS++
//
// *** PIN ASSIGNMENT ***
// Motor Shield V1 uses Timer1 PWM on pins 9 & 10 — DO NOT use those for GPS.
// Use A0 (pin 14) and A1 (pin 15) instead.
//
// Wiring:
//   GPS TX  →  Arduino A0   (SoftwareSerial RX)
//   GPS RX  →  Arduino A1   (SoftwareSerial TX)
//   GPS VCC →  5V or 3.3V  (M8N works on both)
//   GPS GND →  GND
//
// u-blox M8N default: 9600 baud, 1Hz update, NMEA (GGA + RMC sentences)
// If gps_ok is always 0 → go outdoors and wait 30-90 sec for cold fix.

#ifndef GPS_READER_H
#define GPS_READER_H

#include <SoftwareSerial.h>
#include <TinyGPS++.h>

class GPSReader {
public:
    // A0 = pin 14 (RX ← GPS TX),  A1 = pin 15 (TX → GPS RX)
    GPSReader(uint8_t rxPin = A0, uint8_t txPin = A1);
    void begin(uint32_t baud = 9600);

    // Call every loop() iteration — feeds NMEA bytes to TinyGPS++
    void update();

    // ── Core fix data ───────────────────────────────────────────────
    bool    isValid()     const;   // true = has GPS fix
    double  getLat()      const;   // degrees
    double  getLon()      const;   // degrees
    float   getAltitude() const;   // metres above sea level
    float   getSpeed()    const;   // km/h
    uint8_t getSatCount() const;   // number of satellites
    float   getHDOP()     const;   // horizontal dilution of precision

    // ── M8N freshness helpers ───────────────────────────────────────
    uint32_t getAge()       const; // ms since last fix update
    bool     hasFreshFix()  const; // true if fix updated < 2 seconds ago

private:
    SoftwareSerial _serial;
    TinyGPSPlus    _gps;
};

#endif // GPS_READER_H
