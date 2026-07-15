#ifndef DATA_TYPES_H
#define DATA_TYPES_H

typedef struct
{
    // Location
    double latitude;          // gps.location.lat()
    double longitude;         // gps.location.lng()

    // Date (UTC)
    uint8_t day;              // gps.date.day()
    uint8_t month;            // gps.date.month()
    uint16_t year;            // gps.date.year()

    // Time (UTC)
    uint8_t hour;             // gps.time.hour()
    uint8_t minute;           // gps.time.minute()
    uint8_t second;           // gps.time.second()

    // Navigation
    double altitude_m;        // gps.altitude.meters()
    double speed_kmph;        // gps.speed.kmph()
    double course_deg;        // gps.course.deg()

    // GPS Quality
    uint32_t satellites_num;  // gps.satellites.value()
    double hdop;              // gps.hdop.hdop()

    // Age of last location fix (ms)
    uint32_t location_age_ms; // gps.location.age()

} GPS_Data;

#endif