// GPSReader.h
// GPS module reading via SoftwareSerial on pins 9 (RX) and 10 (TX)
// Uses TinyGPS++ library for NMEA parsing
// ASSUMPTION: GPS module outputs NMEA at 9600 baud

#ifndef GPS_READER_H
#define GPS_READER_H

#include <SoftwareSerial.h>
#include <TinyGPS++.h>

class GPSReader {
public:
    // RX=9 (connect to GPS TX), TX=10 (connect to GPS RX)
    GPSReader(uint8_t rxPin = 9, uint8_t txPin = 10);
    void begin(uint32_t baud = 9600);
    
    // Call every loop() iteration to feed NMEA data
    void update();

    bool    isValid()    const;
    double  getLat()     const;
    double  getLon()     const;
    float   getAltitude()const;
    float   getSpeed()   const;  // km/h
    uint8_t getSatCount()const;
    float   getHDOP()    const;

private:
    SoftwareSerial _serial;
    TinyGPSPlus    _gps;
};

#endif // GPS_READER_H
