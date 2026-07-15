#ifndef GPS_APP_H
#define GPS_APP_H

#include <Arduino.h>
#include "GPS_driver.h"
#include "queues.h"
#include "semaphores.h"
#include "Memory_driver.h"
#include "identification.h"

extern TaskHandle_t GPSAppHandle;
extern SemaphoreHandle_t GPS_Background_Lock_Semaphore;

// Struct to store up to 5 history points
typedef struct {
    GPS_Data records[5];
    uint8_t count;
} GPS_History_Data;

void GPS_app(void *pvParameters);

#endif