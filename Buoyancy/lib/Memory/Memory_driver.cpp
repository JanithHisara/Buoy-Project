#include "Memory_driver.h"

#include "Memory_driver.h"

Preferences preferences;

// Save a boolean safely
void saveBool(const char *key, bool value)
{
    if (!preferences.begin(NAMESPACE, false))
    {
        Serial.println("Failed to open preferences for writing");
        return;
    }

    // Only write if value changed
    bool current = preferences.getBool(key, !value);
    if (current != value)
    {
        preferences.putBool(key, value);
        Serial.printf("Saved key: %s, value: %s\n", key, value ? "true" : "false");
    }

    preferences.end();
}

// Load a boolean
bool loadBool(const char *key, bool defaultValue)
{
    if (!preferences.begin(NAMESPACE, true))
    {
        Serial.println("Failed to open preferences for reading");
        return defaultValue;
    }

    bool value;
    if (preferences.isKey(key))
    {
        value = preferences.getBool(key, defaultValue);
    }
    else
    {
        preferences.putBool(key, defaultValue);
        value = defaultValue;
    }
    preferences.end();
    return value;
}

void saveFloat(const char *key, float value)
{
    if (!preferences.begin(NAMESPACE, false))
    {
        Serial.println("Failed to open preferences for writing");
        return;
    }

    // Only write if value changed
    float current = preferences.getFloat(key, value + 1.0); // Force write if key doesn't exist
    if (current != value)
    {
        preferences.putFloat(key, value);
        Serial.printf("Saved key: %s, value: %f\n", key, value);
    }

    preferences.end();
}

float loadFloat(const char *key, float defaultValue)
{
    if (!preferences.begin(NAMESPACE, true))
    {
        Serial.println("Failed to open preferences for reading");
        return defaultValue;
    }

    float value;
    if (preferences.isKey(key))
    {
        value = preferences.getFloat(key, defaultValue);
    }
    else
    {
        preferences.putFloat(key, defaultValue);
        value = defaultValue;
    }
    preferences.end();
    return value;
}

void saveInt(const char *key, int value)
{
    if (!preferences.begin(NAMESPACE, false))
    {
        Serial.println("Failed to open preferences for writing");
        return;
    }

    // Only write if value changed
    int current = preferences.getInt(key, value + 1); // Force write if key doesn't exist
    if (current != value)
    {
        preferences.putInt(key, value);
        Serial.printf("Saved key: %s, value: %d\n", key, value);
    }

    preferences.end();
}

int loadInt(const char *key, int defaultValue)
{
    if (!preferences.begin(NAMESPACE, true))
    {
        Serial.println("Failed to open preferences for reading");
        return defaultValue;
    }

    int value;
    if (preferences.isKey(key))
    {
        value = preferences.getInt(key, defaultValue);
    }
    else
    {
        preferences.putInt(key, defaultValue);
        value = defaultValue;
    }
    preferences.end();
    return value;
}

void saveString(const char *key, const char *value)
{
    if (!preferences.begin(NAMESPACE, false))
    {
        Serial.println("Failed to open preferences for writing");
        return;
    }

    char current[128] = {0}; // adjust size as needed

    size_t len = preferences.getBytes(key, current, sizeof(current));

    // Compare only if key exists
    if (len == 0 || strcmp(current, value) != 0)
    {
        preferences.putBytes(key, value, strlen(value) + 1); // include null terminator
        Serial.printf("Saved key: %s, value: %s\n", key, value);
    }

    preferences.end();
}

void loadString(const char *key, char *buffer, size_t size, const char *defaultValue)
{
    if (!preferences.begin(NAMESPACE, true))
    {
        strncpy(buffer, defaultValue, size);
        return;
    }

    if (preferences.isKey(key))
    {
        preferences.getBytes(key, buffer, size);
    }
    else
    {
        preferences.end();

        if (preferences.begin(NAMESPACE, false))
        {
            preferences.putBytes(key, defaultValue, strlen(defaultValue) + 1);
            preferences.end();
        }

        strncpy(buffer, defaultValue, size);
        return;
    }

    buffer[size - 1] = '\0';
    preferences.end();
}

void saveGPSHistory(const void *buffer, size_t size)
{
    if (!preferences.begin(NAMESPACE, false))
    {
        Serial.println("Failed to open preferences for writing GPS History");
        return;
    }
    preferences.putBytes("GPS_HIST", buffer, size);
    preferences.end();
    Serial.println("GPS History saved to NVS");
}

void loadGPSHistory(void *buffer, size_t size)
{
    if (!preferences.begin(NAMESPACE, true))
    {
        Serial.println("Failed to open preferences for reading GPS History");
        memset(buffer, 0, size);
        return;
    }
    size_t len = preferences.getBytes("GPS_HIST", buffer, size);
    preferences.end();
    
    if (len == 0) {
        memset(buffer, 0, size);
    }
}