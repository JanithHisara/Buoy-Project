#ifndef MEMORY_DRIVER_H
#define MEMORY_DRIVER_H

#include <Arduino.h>
#include "Preferences.h"

#define NAMESPACE "NAMESPACE"

void saveString(const char *key, const char *value);
void loadString(const char *key, char *buffer, size_t size, const char *defaultValue);

void saveBool(const char *key, bool value);
bool loadBool(const char *key, bool defaultValue);

#endif