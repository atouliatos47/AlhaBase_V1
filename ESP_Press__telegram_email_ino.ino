/*
 * Power Press with Reason Codes + Email Alerts
 * 
 * Features:
 * - Press 1: Start/Stop with reason code selection
 * - Button 2: Maintenance reason
 * - Button 3: Quality reason
 * - Email notifications with stop reason
 * - Full AlphaBase integration
 */

// Libraries
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// WiFi Credentials
const char* ssid = "SKYPL2JH";
const char* password = "zNeUN3iQa2AbCJ";

// AlphaBase Configuration
const char* alphabaseURL = "http://192.168.0.52:8000";
const char* alphabaseUsername = "atoul";
const char* alphabasePassword = "password123";
String authToken = "";

// MQTT Configuration
const char* mqttServer = "192.168.0.52";
const int mqttPort = 1883;
const char* mqttTopicStatus = "alphabase/presses/status";
const char* mqttTopicCommands = "alphabase/presses/commands";

// Device Info
const char* deviceID = "Press-Simulator-01";

// ============================================================================
// PIN DEFINITIONS
// ============================================================================

// Press 1 Control
const int PIN_BUTTON_START_STOP = 15;  // Button 1 - Start/Stop
const int PIN_RED_LED = 2;             // Red LED
const int PIN_GREEN_LED = 4;           // Green LED

// Reason Buttons
const int PIN_BUTTON_MAINTENANCE = 5;  // Button 2 - Maintenance reason
const int PIN_BUTTON_QUALITY = 21;     // Button 3 - Quality reason

// ============================================================================
// STATE MACHINE
// ============================================================================

enum PressState {
  IDLE,                // Press not running - Red LED ON
  RUNNING,             // Press running - Green LED BLINKING
  WAITING_FOR_REASON   // Press stopped, waiting for reason - Both LEDs BLINKING
};

PressState pressState = IDLE;

// ============================================================================
// CLIENTS
// ============================================================================

WebServer server(80);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ============================================================================
// BUTTON DEBOUNCING
// ============================================================================

int buttonStartStopState = HIGH;
int lastButtonStartStopState = HIGH;
unsigned long lastDebounceTimeStartStop = 0;

int buttonMaintenanceState = HIGH;
int lastButtonMaintenanceState = HIGH;
unsigned long lastDebounceTimeMaintenance = 0;

int buttonQualityState = HIGH;
int lastButtonQualityState = HIGH;
unsigned long lastDebounceTimeQuality = 0;

unsigned long debounceDelay = 50;

// ============================================================================
// LED BLINKING
// ============================================================================

unsigned long lastBlinkTime = 0;
const long blinkInterval = 500;  // 500ms blink
bool ledState = LOW;

// ============================================================================
// TIMING
// ============================================================================

unsigned long lastMQTTPublish = 0;
const long mqttPublishInterval = 5000;

unsigned long pressStartTime = 0;
unsigned long pressStopTime = 0;

// ============================================================================
// WIFI CONNECTION
// ============================================================================

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n✅ WiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// ============================================================================
// ALPHABASE AUTHENTICATION
// ============================================================================

bool loginAlphaBase() {
  Serial.println("Logging in to AlphaBase...");
  
  HTTPClient http;
  String url = String(alphabaseURL) + "/auth/login";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["username"] = alphabaseUsername;
  doc["password"] = alphabasePassword;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  int httpCode = http.POST(jsonData);
  
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<512> responseDoc;
    deserializeJson(responseDoc, response);
    
    authToken = responseDoc["access_token"].as<String>();
    Serial.println("✅ AlphaBase Login Successful!");
    http.end();
    return true;
  }
  
  Serial.print("❌ AlphaBase Login Failed. HTTP Code: ");
  Serial.println(httpCode);
  http.end();
  return false;
}

// ============================================================================
// NOTIFICATION HANDLERS
// ============================================================================

void sendStopEmailAlert(String reason, unsigned long runtime) {
  int minutes = runtime / 60;
  int seconds = runtime % 60;

  Serial.println("📧 Sending EMAIL alert...");
  
  HTTPClient http;
  String url = String(alphabaseURL) + "/notifications/send-alert";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + authToken);
  
  StaticJsonDocument<512> doc;
  doc["to_email"] = "atouliatos43@gmail.com";
  doc["alert_title"] = "Press 1 Stopped - " + reason;
  String message = "Press 1 has been stopped.\n\n";
  message += "Reason: " + reason + "\n";
  message += "Runtime: " + String(minutes) + " minutes " + String(seconds) + " seconds\n";
  doc["alert_message"] = message;
  
  StaticJsonDocument<256> dataDoc;
  dataDoc["press_number"] = 1;
  dataDoc["reason"] = reason;
  dataDoc["runtime_seconds"] = runtime;
  doc["data"] = dataDoc;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  int httpCode = http.POST(jsonData);
  if (httpCode == 200) {
    Serial.println("✅ Email sent successfully!");
  } else {
    Serial.print("❌ Email failed. Code: ");
    Serial.println(httpCode);
  }
  http.end();
}

void sendStopTelegramAlert(String reason, unsigned long runtime) {
  int minutes = runtime / 60;
  int seconds = runtime % 60;

  Serial.println("💬 Sending TELEGRAM alert...");
  
  HTTPClient http;
  // Use the new Telegram endpoint
  String url = String(alphabaseURL) + "/notifications/send-telegram-alert";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + authToken);
  
  // Telegram API just needs title, message, and data
  StaticJsonDocument<512> doc;
  doc["title"] = "Press 1 Stopped - " + reason;
  doc["message"] = "Press 1 has been stopped.";
  
  StaticJsonDocument<256> dataDoc;
  dataDoc["Reason"] = reason;
  dataDoc["Runtime"] = String(minutes) + " min " + String(seconds) + " sec";
  dataDoc["Press"] = "Press 1";
  doc["data"] = dataDoc;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  int httpCode = http.POST(jsonData);
  if (httpCode == 200) {
    Serial.println("✅ Telegram sent successfully!");
  } else {
    Serial.print("❌ Telegram failed. Code: ");
    Serial.println(httpCode);
  }
  http.end();
}

// This is the new main function to call both alerts
void sendStopNotifications(String reason) {
  if (authToken == "") {
    Serial.println("⚠️  Not authenticated. Skipping notifications.");
    return;
  }
  
  // Calculate runtime
  unsigned long runtime = (pressStopTime - pressStartTime) / 1000; // seconds

  Serial.println("\n🔔 Sending stop notifications...");
  Serial.print("   Reason: ");
  Serial.println(reason);
  
  // Send both notifications
  sendStopEmailAlert(reason, runtime);
  sendStopTelegramAlert(reason, runtime);
}

// ============================================================================
// ALPHABASE DATA LOGGING
// ============================================================================

void logEventToAlphaBase(String event, String reason = "") {
  if (authToken == "") return;
  
  HTTPClient http;
  String url = String(alphabaseURL) + "/data/set";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + authToken);
  
  StaticJsonDocument<512> doc;
  doc["collection"] = "press_events";
  doc["key"] = String("press1_") + String(millis());
  
  StaticJsonDocument<256> valueDoc;
  valueDoc["press_number"] = 1;
  valueDoc["event"] = event;
  if (reason != "") {
    valueDoc["reason"] = reason;
  }
  valueDoc["timestamp"] = millis();
  valueDoc["device_id"] = deviceID;
  
  doc["value"] = valueDoc;
  
  String requestData;
  serializeJson(doc, requestData);
  
  http.POST(requestData);
  http.end();
}

// ============================================================================
// MQTT CONNECTION
// ============================================================================

void connectMQTT() {
  Serial.print("Connecting to MQTT");
  
  while (!mqttClient.connected()) {
    Serial.print(".");
    
    String clientId = "PressSimulator-" + String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("\n✅ MQTT Connected!");
      mqttClient.subscribe(mqttTopicCommands);
      return;
    }
    
    delay(2000);
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Handle MQTT commands if needed
}

// ============================================================================
// MQTT PUBLISH STATUS
// ============================================================================

void publishStatusMQTT() {
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceID;
  
  String stateStr;
  if (pressState == IDLE) stateStr = "IDLE";
  else if (pressState == RUNNING) stateStr = "RUNNING";
  else if (pressState == WAITING_FOR_REASON) stateStr = "WAITING_FOR_REASON";
  
  doc["press1"] = stateStr;
  doc["timestamp"] = millis();
  doc["ip"] = WiFi.localIP().toString();
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  mqttClient.publish(mqttTopicStatus, jsonData.c_str());
}

// ============================================================================
// WEB SERVER HANDLER
// ============================================================================

void handleGetStatus() {
  String stateStr;
  if (pressState == IDLE) stateStr = "IDLE";
  else if (pressState == RUNNING) stateStr = "RUNNING";
  else if (pressState == WAITING_FOR_REASON) stateStr = "WAITING_FOR_REASON";
  
  String json = "{";
  json += "\"device_id\": \"" + String(deviceID) + "\",";
  json += "\"press1\": \"" + stateStr + "\",";
  json += "\"uptime\": " + String(millis() / 1000);
  json += "}";
  
  server.send(200, "application/json", json);
}

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║  Press Monitor with Reason Codes      ║");
  Serial.println("╚════════════════════════════════════════╝\n");
  
  // Connect WiFi
  connectToWiFi();
  
  // Login to AlphaBase
  if (!loginAlphaBase()) {
    Serial.println("⚠️  Continuing without AlphaBase...");
  }
  
  // Setup MQTT
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(mqttCallback);
  connectMQTT();
  
  // Start Web Server
  server.on("/status", HTTP_GET, handleGetStatus);
  server.begin();
  Serial.println("🌐 Web Server Started on /status");
  
  // Initialize Pins
  pinMode(PIN_RED_LED, OUTPUT);
  pinMode(PIN_GREEN_LED, OUTPUT);
  pinMode(PIN_BUTTON_START_STOP, INPUT_PULLUP);
  pinMode(PIN_BUTTON_MAINTENANCE, INPUT_PULLUP);
  pinMode(PIN_BUTTON_QUALITY, INPUT_PULLUP);
  
  // Set Initial State - IDLE
  digitalWrite(PIN_RED_LED, HIGH);
  digitalWrite(PIN_GREEN_LED, LOW);
  
  Serial.println("\n✅ Setup Complete!\n");
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.println("Button 1 (D15): Start/Stop Press");
  Serial.println("Button 2 (D5):  Maintenance Reason");
  Serial.println("Button 3 (D21): Quality Reason");
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}

// ============================================================================
// LOOP
// ============================================================================

void loop() {
  // Maintain WiFi
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }
  
  // Maintain MQTT
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();
  
  // Handle Web Server
  server.handleClient();
  
  // Handle Buttons
  handleStartStopButton();
  handleMaintenanceButton();
  handleQualityButton();
  
  // Update LEDs based on state
  updateLEDs();
  
  // Periodic MQTT status publish
  unsigned long currentMillis = millis();
  if (currentMillis - lastMQTTPublish >= mqttPublishInterval) {
    lastMQTTPublish = currentMillis;
    publishStatusMQTT();
  }
}

// ============================================================================
// BUTTON HANDLERS
// ============================================================================

void handleStartStopButton() {
  int reading = digitalRead(PIN_BUTTON_START_STOP);
  
  if (reading != lastButtonStartStopState) {
    lastDebounceTimeStartStop = millis();
  }
  
  if ((millis() - lastDebounceTimeStartStop) > debounceDelay) {
    if (reading != buttonStartStopState) {
      buttonStartStopState = reading;
      
      if (buttonStartStopState == LOW) {
        Serial.println("\n🔘 START/STOP Button Pressed!");
        
        if (pressState == IDLE) {
          // Start the press
          pressState = RUNNING;
          pressStartTime = millis();
          Serial.println("✅ Press 1 STARTED");
          Serial.println("   Green LED blinking...");
          logEventToAlphaBase("STARTED");
          
        } else if (pressState == RUNNING) {
          // Stop the press - wait for reason
          pressState = WAITING_FOR_REASON;
          pressStopTime = millis();
          Serial.println("🛑 Press 1 STOPPED");
          Serial.println("⏳ Waiting for reason code...");
          Serial.println("   Press Button 2 (Maintenance) or Button 3 (Quality)");
          logEventToAlphaBase("STOPPED");
        }
      }
    }
  }
  
  lastButtonStartStopState = reading;
}

void handleMaintenanceButton() {
  int reading = digitalRead(PIN_BUTTON_MAINTENANCE);
  
  if (reading != lastButtonMaintenanceState) {
    lastDebounceTimeMaintenance = millis();
  }
  
  if ((millis() - lastDebounceTimeMaintenance) > debounceDelay) {
    if (reading != buttonMaintenanceState) {
      buttonMaintenanceState = reading;
      
      if (buttonMaintenanceState == LOW && pressState == WAITING_FOR_REASON) {
        Serial.println("\n🔧 MAINTENANCE Reason Selected!");
        sendStopNotifications("Maintenance");
        logEventToAlphaBase("REASON_SELECTED", "Maintenance");
        pressState = IDLE;
        Serial.println("✅ Back to IDLE state\n");
      }
    }
  }
  
  lastButtonMaintenanceState = reading;
}

void handleQualityButton() {
  int reading = digitalRead(PIN_BUTTON_QUALITY);
  
  if (reading != lastButtonQualityState) {
    lastDebounceTimeQuality = millis();
  }
  
  if ((millis() - lastDebounceTimeQuality) > debounceDelay) {
    if (reading != buttonQualityState) {
      buttonQualityState = reading;
      
      if (buttonQualityState == LOW && pressState == WAITING_FOR_REASON) {
        Serial.println("\n⚠️  QUALITY Reason Selected!");
        sendStopNotifications;
        logEventToAlphaBase("REASON_SELECTED", "Quality Issue");
        pressState = IDLE;
        Serial.println("✅ Back to IDLE state\n");
      }
    }
  }
  
  lastButtonQualityState = reading;
}

// ============================================================================
// LED UPDATE
// ============================================================================

void updateLEDs() {
  switch (pressState) {
    case IDLE:
      // Red LED ON, Green LED OFF
      digitalWrite(PIN_RED_LED, HIGH);
      digitalWrite(PIN_GREEN_LED, LOW);
      break;
      
    case RUNNING:
      // Red LED OFF, Green LED BLINKING
      digitalWrite(PIN_RED_LED, LOW);
      if (millis() - lastBlinkTime >= blinkInterval) {
        lastBlinkTime = millis();
        ledState = !ledState;
        digitalWrite(PIN_GREEN_LED, ledState);
      }
      break;
      
    case WAITING_FOR_REASON:
      // BOTH LEDs BLINKING (alternate)
      if (millis() - lastBlinkTime >= blinkInterval) {
        lastBlinkTime = millis();
        ledState = !ledState;
        digitalWrite(PIN_RED_LED, ledState);
        digitalWrite(PIN_GREEN_LED, !ledState);  // Opposite of red
      }
      break;
  }
}