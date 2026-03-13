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

// gets the raw RGB and clear values
void getRgbValues(){
  tcs.getRawData(&r, &g, &b, &c);
}

// Returns true if the clear sensor value is above the threshold,
// indicating an object is detected.
bool objectDetected(uint16_t c){
  return c > PRESENCE_THRESHOLD;  
}


// This functions allows us to get the color names from a ratio of the RGB and clear values 
String getColorName(uint16_t r,uint16_t g,uint16_t b, uint16_t c){


  // Calculate normalized RGB ratios relative to the clear light value
  // This helps determine which color channel is strongest compared to total light
  float rRatio = (float)r/c;
  float gRatio = (float)g/c;
  float bRatio = (float)b/c;

  // Calculate the clear light ratio compared to all channels combined
  // Used to help detect low-saturation colors like gray or black
  float cRatio = (float)c / (r + g + b + c);
  
  
 if ((gRatio > rRatio) && (gRatio > bRatio) && (gRatio > 0.40)) { // gets the green color name 
    return "Green";
  }

  else if ((bRatio > rRatio) && (bRatio > gRatio) && (bRatio > 0.40)) { // gets the blue color name
    return "Blue";
  }

  else if ((rRatio < cRatio) && (gRatio < cRatio) && (bRatio < cRatio) && (c >= 1000)){ // gets the gray color name 
    return "Gray";
  }
  else if ((rRatio < cRatio) && (gRatio < cRatio) && (bRatio < cRatio) && (c > 650)){ // gets the black color name
    return "Black";
  }
  else {
      return "Unknown";
  }


}

// Determines whether the detected object should be classified as trash or recycle
String getType(String name){

  if(name == "Green" || name == "Blue"){ // Green and Blue items are classified as recycle
    return "Recycle";
  }
  else if (name == "Black" || name == "Gray"){ // Black and Gray items are classified as trash
    return "Trash";
  }
  else{
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
    if (objectDetected(c)) {

    String colorName = getColorName(r,g,b,c);
    String typeName = getType(colorName);

    Serial.print("Color: ");
    Serial.print(colorName);
    Serial.print(" type: ");
    Serial.println(typeName);

  } else {
    Serial.println("No object detected");
  }
 
  

  

  delay(700);
}