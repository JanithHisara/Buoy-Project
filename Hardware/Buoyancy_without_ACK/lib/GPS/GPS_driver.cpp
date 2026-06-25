#include "GPS_driver.h"

#include <Arduino.h>

TinyGPSPlus gps;
HardwareSerial GPSserial(2);

void GPS_init()
{
    GPSserial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
}

void GPS_loop()
{
    static unsigned long last_print = 0;
    static unsigned long char_count = 0;

    while (GPSserial.available() > 0)
    {
        char c = GPSserial.read();
        gps.encode(c);
        char_count++;
    }

    if (millis() - last_print > 5000)
    {
        last_print = millis();
        if (char_count > 0)
        {
            Serial.printf("[GPS] Received %lu chars from module. Satellites: %lu, Valid Lock: %s\n",
                          char_count, (unsigned long)gps.satellites.value(), gps.location.isValid() ? "YES" : "NO");
            char_count = 0;
        }
        else
        {
            Serial.println("[GPS] WARNING: No serial data received from GPS module! Check RX/TX wiring.");
        }
    }
}

GPS_Data GPS_getData()
{
    GPS_Data data = {0};

    // Location
    if (gps.location.isValid())
    {
        data.latitude = gps.location.lat();
        data.longitude = gps.location.lng();
    }

    // Date
    if (gps.date.isValid())
    {
        data.day = gps.date.day();
        data.month = gps.date.month();
        data.year = gps.date.year();
    }

    // Time
    if (gps.time.isValid())
    {
        data.hour = gps.time.hour();
        data.minute = gps.time.minute();
        data.second = gps.time.second();
    }

    // Navigation
    if (gps.altitude.isValid())
        data.altitude_m = gps.altitude.meters();

    if (gps.speed.isValid())
        data.speed_kmph = gps.speed.kmph();

    if (gps.course.isValid())
        data.course_deg = gps.course.deg();

    // GPS Quality
    if (gps.satellites.isValid())
        data.satellites_num = gps.satellites.value();

    if (gps.hdop.isValid())
        data.hdop = gps.hdop.hdop();

    // Age
    data.location_age_ms = gps.location.age();

    return data;
}
