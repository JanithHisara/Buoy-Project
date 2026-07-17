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
    
    const uint8_t *ptr = (const uint8_t *)buffer;
    size_t remaining = size;
    int chunk_idx = 0;
    while(remaining > 0) {
        size_t chunk_size = remaining > 500 ? 500 : remaining;
        char key[15];
        sprintf(key, "GPS_HIST_%d", chunk_idx);
        preferences.putBytes(key, ptr, chunk_size);
        ptr += chunk_size;
        remaining -= chunk_size;
        chunk_idx++;
    }
    preferences.end();
    Serial.println("GPS History chunked and saved to NVS");
}

void loadGPSHistory(void *buffer, size_t size)
{
    memset(buffer, 0, size);
    if (!preferences.begin(NAMESPACE, true))
    {
        Serial.println("Failed to open preferences for reading GPS History");
        return;
    }
    
    uint8_t *ptr = (uint8_t *)buffer;
    size_t remaining = size;
    int chunk_idx = 0;
    
    // Check if chunk 0 exists to see if we have valid saved data
    char key0[15];
    sprintf(key0, "GPS_HIST_0");
    if (preferences.getBytesLength(key0) == 0) {
        preferences.end();
        return; // Empty history
    }

    while(remaining > 0) {
        size_t chunk_size = remaining > 500 ? 500 : remaining;
        char key[15];
        sprintf(key, "GPS_HIST_%d", chunk_idx);
        size_t len = preferences.getBytesLength(key);
        
        if (len == chunk_size) {
            preferences.getBytes(key, ptr, chunk_size);
        } else {
            // Mismatch or corrupted chunk -> Discard everything
            Serial.println("GPS History size mismatch! Discarding old history.");
            memset(buffer, 0, size);
            break;
        }
        
        ptr += chunk_size;
        remaining -= chunk_size;
        chunk_idx++;
    }
    
    preferences.end();
}