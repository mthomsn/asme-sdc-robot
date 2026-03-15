#include <Wire.h>
#include "Adafruit_TCS34725.h"
#include <Servo.h>

#define redpin 3
#define greenpin 5
#define bluepin 6
#define commonAnode true

Adafruit_TCS34725 tcs =
  Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

// create servo object to control a servo 
Servo myservo;
// variable to keep track of servo position
int pos = 0; 

byte gammatable[256];

bool isGreenRGB(int r, int g, int b) {
  return (r >= 42   && r <= 60)  &&
         (g >= 110  && g <= 145) &&
         (b >= 45   && b <= 70);
}

bool isBlueRGB(int r, int g, int b) {
  return (r >= 25   && r <= 40)  &&
         (g >= 76  && g <= 80) &&
         (b >= 110  && b <= 130);
}

bool isBlackRGB(int r, int g, int b) {
  return (r >= 58  && r < 85) &&
         (g >= 95  && g <= 100) &&
         (b >= 65  && b <= 85);
}

bool isGrayRGB(int r, int g, int b) {
  return (r >= 70 && r <= 85) &&
         (g >= 90 && g <= 96) &&
         (b >= 67 && b <= 75);
}

bool isBrownRGB(int r, int g, int b) {
  return (r >= 85 && r <= 120) &&
         (g >= 75 && g <= 97) &&
         (b >= 60 && b <= 70);
}

bool isRecyclable(int r, int g, int b) {
  return isGreenRGB(r,g,b) || isBlueRGB(r,g,b);
}

bool isGarbage(int r, int g, int b) {
  return isBlackRGB(r,g,b) || isGrayRGB(r,g,b) || isBrownRGB(r,g,b);
}

void setup() {
  Serial.begin(9600);
  myservo.attach(9);  

  if (!tcs.begin()) {
    Serial.println("sensor not found so sad :(");
    while (1);
  }

  pinMode(redpin, OUTPUT);
  pinMode(greenpin, OUTPUT);
  pinMode(bluepin, OUTPUT);

  for (int i = 0; i < 256; i++) {
    float x = i;
    x /= 255;
    x = pow(x, 2.5);
    x *= 255;

    gammatable[i] = commonAnode ? (255 - x) : x;
  }
}

void loop() {
  float red, green, blue;

  tcs.setInterrupt(false);
  delay(60);
  tcs.getRGB(&red, &green, &blue);
  tcs.setInterrupt(true);

  int r = (int)red;
  int g = (int)green;
  int b = (int)blue;

  Serial.print("R: "); Serial.print(r);
  Serial.print("\tG: "); Serial.print(g);
  Serial.print("\tB: "); Serial.print(b);

  if (isRecyclable(r,g,b)) {
    Serial.print("\t=> RECYCLABLE");
    if (isGreenRGB(r,g,b)) Serial.print(" (GREEN)");
    if (isBlueRGB(r,g,b))  Serial.print(" (BLUE)");
    for (pos = 0; pos <= 180; pos += 1) { 
    // for each step until we reach 90, we will move 1 degree
    myservo.write(pos);              
    delay(15); // delay so servo has time to move                  
  }
  }
  else if (isGarbage(r,g,b)) {
    Serial.print("\t=> GARBAGE");
    if (isBlackRGB(r,g,b)) Serial.print(" (BLACK)");
    else if (isGrayRGB(r,g,b)) Serial.print(" (GRAY)");
    else if (isBrownRGB(r,g,b)) Serial.print(" (BROWN)");
    for (pos = 180; pos >= 0; pos -= 1) { 
    myservo.write(pos);
    delay(15);
  }
  }
  else {
    Serial.print("\t=> EMPTY");
  }

  Serial.println();

  analogWrite(redpin, gammatable[r]);
  analogWrite(greenpin, gammatable[g]);
  analogWrite(bluepin, gammatable[b]);

  delay(120);
}