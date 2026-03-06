#include <Wire.h>
#include "Adafruit_TCS34725.h"

// Create the sensor object
Adafruit_TCS34725 tcs = Adafruit_TCS34725(
  TCS34725_INTEGRATIONTIME_50MS,
  TCS34725_GAIN_4X
);

// global Variables 
uint16_t r;
uint16_t g;
uint16_t b;
uint16_t c;
const uint16_t PRESENCE_THRESHOLD = 150;



void setup() {
  Serial.begin(9600);
  Serial.println("TCS34725 Color Sensor Test");

  if (tcs.begin()) {
    Serial.println("Sensor found!");
  } else {
    Serial.println("No TCS34725 detected... check wiring!");
    while (1);
  }
}

void getRgbValues(){
  tcs.getRawData(&r, &g, &b, &c);
}

bool objectDetected(uint16_t c){
  return c > PRESENCE_THRESHOLD;  
}

String getColorName(uint16_t r,uint16_t g,uint16_t b, uint16_t c){

  if(c == 0){
    return "Unknown";
  }

  float rRatio = (float)r/c;
  float gRatio = (float)g/c;
  float bRatio = (float)b/c;

  
 if ((gRatio > rRatio) && (gRatio > bRatio) && (gRatio > 0.40)) {
    return "Green";
  }

  else if ((bRatio > rRatio) && (bRatio > gRatio) && (bRatio > 0.40)) {
    return "Blue";
  }

  else if (c >= 1000){
    return "Gray";
  }
  else if (c > 620){
    return "Black";
  }
  else {
      return "Unknown";
  }


}

void loop() {

  getRgbValues();

/*
  if (c != 0) {
    Serial.print(" r/c: "); Serial.print((float)r / c, 3);
    Serial.print(" g/c: "); Serial.print((float)g / c, 3);
    Serial.print(" b/c: "); Serial.println((float)b / c, 3);
  }
*/
/*
  Serial.print("R: "); Serial.print(r);
  Serial.print(" G: "); Serial.print(g);
  Serial.print(" B: "); Serial.print(b);
  Serial.print(" C: "); Serial.println(c);
*/

  if(objectDetected(c)){
    String name = getColorName(r,g,b,c);
    Serial.print("->");
    Serial.println(name);
  }
  else {
    Serial.println("-> No object found");
  }

  

  delay(500);
}