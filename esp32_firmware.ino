/*
 * OceanNav ESP32 Client Firmware
 * ----------------------------------------------------
 * Connects your ESP32 module to the OceanNav website.
 * 
 * Hardware Interactions:
 * 1. Pressing the physical EN (Reset) button boots the chip,
 *    which prints the "DEVICE_LOCATED" token to Serial.
 * 2. When the website initiates a scan, it sends the command
 *    "AT+CGPSINFO?". The ESP32 parses this and replies with
 *    coordinates representing a tracking track in Colombo Waters.
 */

#define BAUDRATE 115200

// Set to true to print real GPS module coordinates if you have a Neo-6M module,
// or false to output simulated demo coordinate paths in Colombo waters.
const bool USE_PHYSICAL_GPS = false;

// If you have a physical GPS module connected, configure its Serial RX/TX pins
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
HardwareSerial gpsSerial(2);

void setup() {
  // Initialize Serial port for PC communication
  Serial.begin(BAUDRATE);
  
  // Initialize secondary serial port for real GPS if enabled
  if (USE_PHYSICAL_GPS) {
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  }
  
  // Wait for serial port to stabilize
  delay(1200);
  
  // --- EN BUTTON BOOT TRIGGER ---
  // The website background serial listener reads this boot string.
  // When detected, the web interface triggers a "Device Located" banner.
  Serial.println("==========================================");
  Serial.println("DEVICE_LOCATED");
  Serial.println("SYSTEM: ESP32 client online and tracking.");
  Serial.println("==========================================");
}

void loop() {
  // Check if commands are received from the PC website
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Check if the command matches the GPS info scan request
    if (command.equalsIgnoreCase("AT+CGPSINFO?") || command.equalsIgnoreCase("GPS") || command.equalsIgnoreCase("Gps")) {
      
      if (USE_PHYSICAL_GPS) {
        // Read from NEO-6M / SIM800L module and pipe response to PC Serial port
        unsigned long startWait = millis();
        bool dataSent = false;
        
        while (millis() - startWait < 2000) {
          if (gpsSerial.available() > 0) {
            String gpsData = gpsSerial.readStringUntil('\n');
            gpsData.trim();
            
            // Expected coordinate format: "lat,lon" (e.g. 6.9271,79.8612)
            if (gpsData.length() > 0) {
              Serial.println(gpsData);
              dataSent = true;
            }
          }
        }
        if (!dataSent) {
          // Fallback if physical GPS has no fix or signal lock
          Serial.println("6.9271,79.8612");
        }
      } else {
        // --- SIMULATED GPS TRACK PATH ---
        // Simulates 6 locations close to Colombo harbor for live demo testing.
        // The points are sent with small delays to create a live animation.
        Serial.println("6.9271,79.8612");
        delay(350);
        Serial.println("6.9285,79.8630");
        delay(350);
        Serial.println("6.9312,79.8654");
        delay(350);
        Serial.println("6.9340,79.8682");
        delay(350);
        Serial.println("6.9378,79.8715");
        delay(350);
        Serial.println("6.9415,79.8750");
        
        // Print complete notice or print JSON
        Serial.println("SUCCESS: Track coordinates logged");
      }
    }
  }
  
  delay(50);
}
