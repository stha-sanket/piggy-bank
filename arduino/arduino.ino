#include "HX711.h"

#define DOUT 6
#define CLK 7

HX711 scale;

// REPLACE WITH YOUR CALIBRATED VALUE
float calibration_factor = -405500; // Change this after calibration

void setup() {
  Serial.begin(115200);
  scale.begin(DOUT, CLK);
  
  scale.set_scale(calibration_factor);
  scale.tare(); // Reset to zero
  
  Serial.println("Load Cell Ready");
  Serial.println("Weight (g):");
}

void loop() {
  float weight = scale.get_units(5); // Average of 5 readings
  
  Serial.print("Weight: ");
  Serial.print(weight, 6); // 1 decimal place
  Serial.println(" g");
  
  delay(500);
}