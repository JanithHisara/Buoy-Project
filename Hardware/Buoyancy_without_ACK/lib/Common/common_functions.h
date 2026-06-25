#ifndef COMMON_FUNCTIONS_H
#define COMMON_FUNCTIONS_H

#include <Arduino.h>

#define TURNON_LED() digitalWrite(2, HIGH)
#define TURNOFF_LED() digitalWrite(2, LOW)

void clean_buffer(char *buf);
void getChipID(char *buffer, size_t bufferSize);

#endif