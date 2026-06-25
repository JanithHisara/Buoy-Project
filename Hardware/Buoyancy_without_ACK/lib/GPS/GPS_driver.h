#ifndef GPS_DRIVER_H
#define GPS_DRIVER_H

#include "GPS_hal.h"

#include <TinyGPS++.h>
#include "data_types.h"

void GPS_init();
void GPS_loop();
GPS_Data GPS_getData();

#endif