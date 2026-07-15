# ifndef QUEUES_H
# define QUEUES_H

#include <Arduino.h>

extern QueueHandle_t AT_to_LoRa_Queue;
extern QueueHandle_t LoRa_to_AT_Queue;

extern QueueHandle_t AT_to_GPS_Queue;
extern QueueHandle_t GPS_to_AT_Queue;

# endif // QUEUES_H