#MIT License
#
#Copyright (c) 2017 Jonathan A. White
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from ValveController import *

# The KATARAValveController class provides an interface to communicate with an arduino mega running the KATARA firmware.
class KATARAValveController(ValveController):
    deviceType = "Arduino Mega"

    #KATARAValveController.__init__: Connects by calling base class constructor, sets up dictionary to keep track of pin
    #       states which also denotes available pins.
    #   Input:
    #       port - the string name of the serial port to connect to.
    def __init__(self, port):
        ValveController.__init__(self, port)
        self.port = port
        for p in range(2,70):
            self.pinStates[p]=0
        # specify KATARAPumps
        self.pump = KATARAPump

    # KATARAValveController.setPins: sets a tuple, list, or set of pins to the corresopnding state in the tuple
    # or list of states.
    #   Inputs:
    #       pins - a tuple, list, or set of pins. It must be the same length as state
    #       states - a tuple or list of states to set the pins. Must be the same length as pins.
    #   Output: Responding message from device.
    def setPins(self, pins, states):
        if type(pins) not in (tuple, list, set):
            raise ValueError("'pins' entry must be a tuple, list or set.")
        if type(states) not in (tuple, list):
            raise ValueError("'states' entry must be a tuple, list or set.")
        if len(set(pins)) < len(pins):
            raise ValueError("There is a duplicate pin entry.")
        if len(pins) != len(states):
            raise ValueError("The length of the pins and states entries must be the same.")

        message = "2" #2 is the case for writing multiple pins in the arduino firmware switch/case structure
        for pinNum in range(len(pins)):
            message += self._handleSetPinsInput(pins[pinNum], states[pinNum])
        self._write(message)
        response = self.ser.readline()
        print(response)
        return response

    # KATARAValveController._handleSetPinsInput: A helper method to setPins. It verifies the input is valid, throws an
    #           error if it is not, and processes the input to prepare it for writing as a serial command.
    # Inputs:
    #       pin - number of a pin to set
    #       state - the state to set the pin to
    # Output: A three character pin that holds the pin number in the first two characters and the state in the third.
    def _handleSetPinsInput(self, pin, state):
        self._checkPin(pin)
        # check if state is valid
        if state not in (0, 1):
            raise ValueError("Pin " + str(pin) + " must be set to either 0 or 1.")
        self.pinStates[pin] = state
        if pin < 10:
            pin = '0' + str(int(pin))
        else:
            pin = str(int(pin))
        return pin + str(state)

    # KATARAValveController.testConnection - Tests whether a serial connection to the Arduino firmware has been
    #   successfully established, throws an IOError if not.
    # Inputs: None
    # Outputs: None
    def testConnection(self):
        self.ser.timeout  = 1
        time.sleep(1) # wait after initializing connection to arduino to give it time to reset.
        self.ser.write("1c")
        response = self.ser.readline()
        self.ser.timeout = 0.1 # tell the serial object to time out and throw an error if the Arduino takes longer than
                               # 0.1 seconds to respond to a serial command.
        print(response)
        if response != "1KATARA Arduino Firmware":
            raise IOError("The device is not an Arduino running the KATARA firmware.")


    # KATARAValveController._checkPin: checks to see if user pin input is valid
    #   Input:
    #       pin - user input for pin
    #   Output: None, but raises error if pin is an invalid value.
    def _checkPin(self, pin):
        if pin not in range(2,70): #and pin not in self.analogPinAliases:
            raise  ValueError("Error: invalid pin number. The available pins are numbered 2-69 (A0-A15 are aliases for integer pins 54-69).")

    # KATARAValveController._write: This method sends all serial messages and handles IO errors.
    # Inputs:
    #       out - serial message to send (string)
    # Outputs: None
    def _write(self, out):
        try:
            print("Writing")
            self.ser.write(str(out))
            self.ser.write('c')
            print("Sent:", str(out) + "c")
        except Exception as E:
            print("Error:")
            print(E.message)
            self.ser.close()
            try:
                self.ser = serial.Serial(self.port, timeout=1)
                for pump in ValveController.pPumps:
                    pump.ser = self.ser
                self.testConnection()
                self.ser.timeout = 0.1
            except Exception as E:
                print(E.message)
                self.ser.close()
                raise IOError(
                    "The connection to the arduino was lost. Check to make sure it is still plugged in and reconnect.")
            for pin in self.pinStates:
                if self.pinStates[pin]:
                    self.setPin(pin, 1)
            self.ser.write(str(out) + "c")
            raise Warning("There was a problem in the connection. The connection has been reset and the valve states have been restored.")


# KATARAPump derived peristalticPump for sending USB signals to to the KATARA shield instructing it to run peristaltic
# pump sequences.
class KATARAPump(perstalticPump):

    # KATARAPump.__init__: Should be called by KATARAValveController.specifyPumpCalls parent class constructor,
    # see peristalticPump.__init__ for more details.
    def __init__(self, _v1, _v2, _v3, ctlr):
        perstalticPump.__init__(self, _v1, _v2, _v3, ctlr)

    # KATARAPump._runPump: implements the serial communications to the KATARA Firmware to tell it to run peristaltic
    #           pump sequences.
    # Inputs:
    #       rate - rate (Hertz) at which the peristaltic pump should complete pumping cycles.
    #       cycles - the number of persistaltic pump cycles to complete. Input -1 to run indefinitely.
    #       direction - 'f' if forward, 'r' if reverse.
    def _runPump(self, rate, cycles, direction, wait  = False):
        self.checkRateCycles(rate, cycles, wait)
        toWrite = '3' + direction
        for v in self.valves:
            toWrite += v
        rate = str(rate)
        toWrite += '0' * (3 - len(rate)) + rate  # rate is a three character string
        cycles = str(cycles)
        toWrite += '0' * (6 - len(cycles)) + cycles  # time is a four character string
        try:
            self.ctlr.ser.write(toWrite + 'c')
        except Exception as E:
            self.ctlr.ser.close()
            try:
                self.ctlr.ser = serial.Serial(self.ctlr.port, timeout=1)
                self.ctlr.testConnection()
                self.ctlr.ser.timeout = 0.1
                for pump in ValveController.pPumps:
                    pump.ser = self.ctlr.ser
            except Exception as E:
                print(E.message)
                self.ctlr.ser.close()
                raise IOError(
                    "The connection to the arduino was lost. Check to make sure it is still plugged in and reconnect.")
            for pin in self.ctlr.pinStates:
                if self.ctlr.pinStates[pin]:
                    self.ctlr.setPin(pin, 1)
            self.ctlr.ser.write(toWrite + 'c')
            raise Warning(
                "There was a problem in the connection. The connection has been reset and the valve states have been restored.")

        for valve in self.valves:
            self.ctlr.pinStates[int(valve)] = 0
        if wait: #pause thread until pump cycle is complete
            time.sleep(float(cycles)/float(rate))
        self.ctlr.ser.readline()

        ret = '1'
        while ret:
            try:
                ret = self.ctlr.ser.readline()
                print(ret)
            except:
                break

    # KATARAPump.stop: Sends a serial signal to stop a pumping sequence before completing all indicated cycles
    #   Input: None
    #   Output: None
    def stop(self):
        self.ctlr.ser.write("c")
        self.ctlr.ser.readline()