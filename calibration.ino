#include "HX711.h"

#define DOUT 6
#define CLK 7

HX711 scale;

float calibration_factor = -405500; // Your current value

void setup() {
  Serial.begin(115200);
  Serial.println("HX711 Calibration");
  Serial.println("Remove all weight from scale");
  Serial.println("After readings begin, place known weight on scale");
  Serial.println("Press + or a to increase calibration factor");
  Serial.println("Press - or z to decrease calibration factor");
  
  scale.begin(DOUT, CLK);
  scale.set_scale();
  scale.tare(); // Reset to zero
  
  Serial.print("Current calibration factor: ");
  Serial.println(calibration_factor);
}

void loop() {
  scale.set_scale(calibration_factor);
  
  Serial.print("Weight: ");
  float weight = scale.get_units(10); // Average of 10 readings
  Serial.print(weight, 3); // 3 decimal places
  Serial.print(" g");
  Serial.print(" | Cal Factor: ");
  Serial.print(calibration_factor);
  Serial.print(" | Raw: ");
  Serial.println(scale.read_average(5)); // Raw reading
  
  if(Serial.available()) {
    char temp = Serial.read();
    
    if(temp == '+' || temp == 'a')
      calibration_factor += 100; // Increase
    else if(temp == '-' || temp == 'z')
      calibration_factor -= 100; // Decrease
    else if(temp == 't' || temp == 'T')
      scale.tare(); // Reset to zero
  }
  
  delay(500);
}