#ifndef GPS_APP_H
#define GPS_APP_H

#include <Arduino.h>
#include "GPS_driver.h"
#include "queues.h"
#include "semaphores.h"
#include "Memory_driver.h"
#include "identification.h"

extern TaskHandle_t GPSAppHandle;

void GPS_app(void *pvParameters);


#endif