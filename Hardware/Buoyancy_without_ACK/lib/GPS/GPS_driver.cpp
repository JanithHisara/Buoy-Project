#include "GPS_driver.h"

TinyGPSPlus gps;
HardwareSerial GPSserial(1);

void GPS_init()
{
    GPSserial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
}

void GPS_loop()
{
    while (GPSserial.available() > 0)
    {
        gps.encode(GPSserial.read());
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
