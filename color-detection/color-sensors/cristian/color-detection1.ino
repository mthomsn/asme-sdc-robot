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

String getColorName(uint16_t r,uint16_t g,uint16_t b, uint16_t c){

  if(c < 630){ //tells if the color is black
    return "Black";
  }
  else if((g > r * 2.1) && (g > b * 2.0)){ //tells if the color is Green
    return "Green";
  }
  else if ((b > r * 1.5) && (b > g * 0.7)){ //tells if the color is blue
    return "Blue";
  }
  else{
    return "Unknown";
  }

}

void loop() {

  getRgbValues();

  String name = getColorName(r,g,b,c);
  Serial.println(name);

  //Serial.print("R: "); Serial.print(r);
  //Serial.print(" G: "); Serial.print(g);
  //Serial.print(" B: "); Serial.print(b);
  //Serial.print(" C: "); Serial.println(c);

 

  delay(500);
}