// GPSReader.cpp
// GPS NMEA parsing via TinyGPS++ on SoftwareSerial

#include "GPSReader.h"

GPSReader::GPSReader(uint8_t rxPin, uint8_t txPin)
    : _serial(rxPin, txPin)
{}

void GPSReader::begin(uint32_t baud) {
    _serial.begin(baud);
}

void GPSReader::update() {
    // Feed all available bytes into TinyGPS++ parser
    while (_serial.available() > 0) {
        _gps.encode(_serial.read());
    }
}

bool GPSReader::isValid() const {
    return _gps.location.isValid() && _gps.location.isUpdated();
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
    return _gps.hdop.isValid() ? (float)_gps.hdop.hdop() : 99.9f;
}
