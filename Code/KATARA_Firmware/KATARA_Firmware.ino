
/*
 This code was written by Jonathan A White and is under the MIT license.
 */

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete


bool pumpForward[6][3] = {
  {1,0,0},
  {1,1,0},
  {0,1,0},
  {0,1,1},
  {0,0,1},
  {1,0,1}
};

bool pumpReverse[6][3] = {
  {0,0,1},
  {0,1,1},
  {0,1,0},
  {1,1,0},
  {1,0,0},
  {1,0,1}
};



//typedef void (*pumpCommand) (int * a);


void setup() {
  // initialize serial:
  Serial.begin(9600);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
//  for(int apin = 0; apin < 16, apin++){
     
//  }
  for(int pin = 2; pin < 70; pin++){
    pinMode(pin,OUTPUT);
  }
}
void pumpCycle(int rate, bool pumpStates[6][3], int valves[3]){
    for(int s = 0; s < 6; s++){
      for(int v = 0; v < 3; v++){
        digitalWrite(valves[v], pumpStates[s][v]);
      }
      delay(1000.0/(rate *6));
      if(Serial.available()){
        //reset valves
        for(int v = 0; v++; v < 3){
          digitalWrite(valves[v],0);
        }
        break;
      }
    }
}

void loop() {
  // print the string when a newline arrives:
  if (stringComplete) {
    int action = inputString[0] - '0';
    Serial.print(inputString);
    //int action = saction.toInt();
      switch (action){
        case 2: {//write pins

          // First, find number of pins. The message will have a to character integer pin number
          // followed by a one character boolian state. So nPins = (Length of message)/3.
          String message = inputString.substring(1);
          int nPins = message.length();
          nPins = nPins/3;
          for(int pin = 0; pin < nPins; pin++){
            String pinNum =  message.substring(3*pin, 3*pin+2);            
            String pinState = message.substring(3*pin+2, 3*pin+3);
            digitalWrite(pinNum.toInt(), pinState.toInt());
          }
          
          Serial.println("Set Pins");
          break;
        }
        case 3: {//run pump
          //get polarity
          char polarity = inputString[1];
          inputString.remove(0,2);
          // get valves
          int valves [3];
          //Serial.print("__Valves:");
          for(int v = 0; v < 3; v++){
            valves[v] = inputString.substring(0,3).toInt();
            inputString.remove(0,3);
          }
          
          //get rate
          int rate = inputString.substring(0,3).toInt();
          inputString.remove(0,3);
          //get time
          int nCycles = inputString.substring(0,6).toInt();
          if(polarity = 'r'){
            if(nCycles == 0){ // if python sent -1, toInt() would return 0
              while(1){
                pumpCycle(rate, pumpReverse, valves);
                if(Serial.available()){
                  break;
                }
              }
              //break;
            } else{ 
            for(int c = 0; c < nCycles; c++){
              pumpCycle(rate, pumpReverse, valves);
            }
           }
          } else{
            if (nCycles == 0){ // if python sent -1, toInt() would return 0
              while(1){  
                pumpCycle(rate, pumpForward, valves);
                if(Serial.available()){
                  break;
                }
              }
              //break;
          } else{
             for(int c = 0; c < nCycles; c++){
                pumpCycle(rate, pumpForward, valves);
             }
            }
           }
          // Return solenoid valves to normally open state.
           for(int v = 0; v < 3; v++){
             digitalWrite(valves[v], 0);
           }
           break;
          }
          case 1: { //name
            Serial.print("KATARA Arduino Firmware");
          }
          break;
        //}
      }
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

/*
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    if (inChar == 'c') {
      stringComplete = true;
    } else {
      // add it to the inputString:
      inputString += inChar;
    }
      // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    
  }
}


