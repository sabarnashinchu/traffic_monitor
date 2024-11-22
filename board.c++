#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi configuration
const char* ssid = "CYRUSBYTE";          // Replace with your Wi-Fi SSID
const char* password = "12345678";  // Replace with your Wi-Fi password

// HTTP server on port 80
ESP8266WebServer server(80);

// LED pin configuration
const int redLedPin = D3;  // Connect the red LED to D3 (or another GPIO pin)
const int greenLedPin = D7; // Connect the green LED to D7 (or another GPIO pin)

// Timer variables
int counter = 40; // Start the counter at 40
bool isTimerPaused = false; // Flag to control whether the timer is paused

// LCD setup
LiquidCrystal_I2C lcd(0x27, 16, 2); // Set the LCD address to 0x27 for a 16x2 display

// Weather API settings
const char* apiKey = "7145b20bcd2af28f0906caf3d9489c40";
const char* city = "Karur";  // City name
const char* weatherAPI = "http://api.openweathermap.org/data/2.5/weather?q=";

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(115200);

  // Set up LED pins as output
  pinMode(redLedPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
  digitalWrite(redLedPin, HIGH);  // Turn the red LED on initially
  digitalWrite(greenLedPin, LOW); // Ensure the green LED is off initially

  // Initialize the I2C interface and LCD
  Wire.begin(D2, D1); // SDA on D2 (GPIO 4), SCL on D1 (GPIO 5)
  lcd.init();
  lcd.backlight();
  lcd.clear();

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi");
  Serial.println(WiFi.localIP());

  // Fetch weather data after connecting to Wi-Fi
  fetchWeather();

  // Set up the HTTP server endpoints
  server.on("/extend_time", HTTP_GET, []() {
    if (isTimerPaused) {
      // If the timer is paused, resume it and extend the time by 10 seconds
      isTimerPaused = false;  // Resume the timer
      counter += 1;  // Increase the timer by 10 seconds
      lcd.clear();
      digitalWrite(redLedPin, HIGH);
      digitalWrite(greenLedPin, LOW);
      server.send(200, "text/plain", "Emergency mode ended. Timer resumed and extended by 10 seconds!");
    } else {
      // If the timer is not paused, just extend the timer by 10 seconds
      counter += 10; // Increase the timer by 10 seconds
      lcd.clear();
      digitalWrite(redLedPin, HIGH);
      digitalWrite(greenLedPin, LOW);
      server.send(200, "text/plain", "Timer extended by 10 seconds!");
    }
  });

  server.on("/show_weather_data", HTTP_GET, []() {
    fetchWeather();
    server.send(200, "text/plain", "Displaying weather data on LCD!");
  });

  // Emergency vehicle detection endpoint
  server.on("/emergency_vehicle", HTTP_GET, []() {
    isTimerPaused = true; // Pause the timer
    digitalWrite(greenLedPin, HIGH);  // Turn on the green LED
    digitalWrite(redLedPin, LOW);     // Turn off the red LED
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Emergency vehicle");
    lcd.setCursor(0, 1);
    lcd.print("detected!");
    server.send(200, "text/plain", "Emergency vehicle detected!");
  });

  server.begin(); // Start the HTTP server
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient(); // Handle HTTP requests

  if (isTimerPaused) {
    return; // If the timer is paused, do nothing (skip timer updates)
  }

  // Regular timer functionality when not paused
  lcd.setCursor(0, 0);
  lcd.print("Time: ");
  lcd.setCursor(6, 0);

  if (counter > 0) {
    if (counter == 9) {
      lcd.clear();
      lcd.print("Time: ");
    }
    lcd.print(counter);
    counter = counter - 1; // Decrease the counter by 1 each second
    delay(1000);           // Wait for 1 second
  } else {
    lcd.setCursor(0, 0);
    lcd.print("Time Finished");
    digitalWrite(redLedPin, LOW);  // Turn off the red LED when time is up
    digitalWrite(greenLedPin, HIGH); // Turn on the green LED when time is up
  }
}

void fetchWeather() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;
    String url = String(weatherAPI) + city + "&appid=" + apiKey + "&units=metric";

    http.begin(client, url); // Specify the URL and client
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println(payload); // For debugging
      displayWeather(payload);
    } else {
      Serial.println("Error on HTTP request");
    }
    http.end();
  }
}

void displayWeather(String json) {
  StaticJsonDocument<512> doc; // Adjust size as needed
  DeserializationError error = deserializeJson(doc, json);

  if (!error) {
    // Extract the desired values
    const char* description = doc["weather"][0]["description"]; // Weather description
    float humidity = doc["main"]["humidity"]; // Humidity
    float windSpeed = doc["wind"]["speed"]; // Wind speed
    float temperature = doc["main"]["temp"]; // Temperature

    // Display values on the LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("weather: ");
    lcd.setCursor(0, 1);
    lcd.print(description);

    delay(2000); // Show description for 2 seconds

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("humidity: ");
    lcd.setCursor(0, 1);
    lcd.print(humidity);
    lcd.print(" %");

    delay(2000); // Show humidity for 2 seconds

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("wind speed: ");
    lcd.setCursor(0, 1);
    lcd.print(windSpeed);
    lcd.print(" m/s");

    delay(2000); // Show wind speed for 2 seconds

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("temperature: ");
    lcd.setCursor(0, 1);
    lcd.print(temperature);
    lcd.print(" C");

    delay(2000); // Show temperature for 2 seconds
    lcd.clear();
  } else {
    Serial.println("Failed to parse JSON");
  }
}