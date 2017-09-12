# This code was written by Jonathan A White, a member of the Streets Lab at the University of California, Berkeley,
# and is licensed under the MIT license.


import serial

import time

# Valve Controller is the base class for sending serial communications to valve controlling circuits using the pyserial
# package by default. The derived class, KATARAValveController sends USB signals interpretable by the KATARA Arduino firmware.
# Derived classes are not necessarily bound to using the pyserial package if the extender prefers another package.
class ValveController:
    pPumps = []

    # ValveController.__init__: Connects to valve controlling device.
    #   Input:
    #       port - string name of the serial port to open.
    #   Output: None, but may raise errors.
    def __init__(self, port):
        #connect to port at default baudrate of 9600
        #set time out to 0.1 second. If arduino does not respond to a read request with in 1/10 second, terminate read.
        self.ser = serial.Serial(port, timeout = 0.1)
        self.testConnection()


        # Create a dictionary to keep track of pinStates. The derived class should add entries to this dictionary.
        self.pinStates = {}
        self.pump = perstalticPump

    # ValveController.testConnection: An abstract method that tests whether a connection has been made successfully
    #   with the usb device- this will require serial communication specific to the device which should be implemented
    #   in a derived class. The implementation should throw an error if there is a connection problem.
    #   See KATARAValveController for an example implementation.
    # Inputs: None
    # Outputs: returns None, But must throw an error if there is a connection problem.
    def testConnection(self):
        raise NotImplementedError("testConnection must be implemented in ValveController child classes.")

    # ValveController.close: closes serial connection to device.
    # Inputs: None
    # Outputs: None
    def close(self):
        self.ser.close()

    # ValveController.togglePin: Toggles the indicated pin: if it is high when the function is called, the pin is set
    #       low. If it is low when the function is called, it is set high. This is called when buttons in the GUI are
    #       pressed.
    #   Inputs:
    #       pin - the pin to toggle
    #   Outputs: None
    def _togglePin(self, pin):
        if self.pinStates[pin] == 1: #pin is high, set low
            self.setPins((pin,),(0,))
            self.pinStates[pin] = 0
            return 0
        else: #pin is low, set high
            self.setPins((pin,),(1,))
            self.pinStates[pin] = 1
            return 1

    # ValveController.getPinState: Returns the current state of a pin
    #   Inputs:
    #       pin - the pin to inquire the state of.
    #   Outputs:
    #       the state of the pin: 1 for high, 0 for low
    def getPinState(self,pin):
        return self.pinStates[pin]

    # ValveController.setPins: An abstract method for sending serial communications to valve control circuits using
    #  pyserial. It should be implemented by a derived classes which gives serial commands for particular circuits.
    # Derived classes could also use a different serial package if desired.
    # See KATARAValveController for  a sample implementation.
    #   Inputs:
    #       pins - a tuple or list of pins to set.
    #       states - a tuple or list corresponding to the pins argument indicating the state to set each each pin.
    #   Outputs: optional indication of successful write
    def setPins(self, pins, states):
        raise NotImplementedError("Error: setPins must be implemented in ValveController derived class.")

    # ValveController.specifyPump: Creates and returns a pump object that can run peristastic pump sequences on three
    #                               valves
    # Inputs:
    #       v1 - the first valve in the peristaltic pump
    #       v2 - the second valve in the peristaltic pump
    #       v3 - the third valve in the peristaltic pump
    # Output:
    #       returns a peristaltic pump object for running peristaltic pump sequences (see below)
    def specifyPump(self,v1,v2,v3):
        for v in (v1, v2, v3):
            self._checkPin(v)
        pPump = self.pump(v1, v2, v3, self)
        self.pPumps.append(pPump)
        return pPump #returns a reference to the pPump

    # ValveController._checkPin: Abstract method to check if user pin input is valid. Overriding _checkPin methods in
    # derived classes should an error if the user inputted an unavailable/invalid pin. See KATARAValveController for
    # example.
    # Inputs:
    #       pin - user input for what should be a reference to an available pin.
    # Output: Throws error if pin is invalid
    def _checkPin(self, pin):
        if pin not in self.pinStates:
            raise ValueError("Error: invalid pin.")

    # ValveController._write: Abstract method - derived classes should implement to sends serial commands to the device
    # and handle write errors. See KATARAValveController for example.
    #   Inputs:
    #       out - string to send over serial
    #   Outputs: may raise warning or errors if IOErrors are encountered.
    def _write(self, out):
        raise NotImplementedError("write must be implemented in the the ValveController child class.")


    # ValveController.isOpen: Checks whether the connection to the device is open.
    # Input: None
    # Output: Boolean; True if a connection is open, False if not.
    def isOpen(self):
        return self.ser.isOpen()


# peristalticPump is a base class that is extended by KATARA pump to implement serial commands for interfacing with the
# KATARA firmware, or could be extended to communicate with other devices for controlling peristaltic pumps.
# peristalticPump objects store valves that are members the pump
class perstalticPump:

    # peristalticPump.__init__: The constructor should be called by the ValveController.specifyPump method; this ensures
    #       that the program does not try to establish a connection to the Arduino multiple times, and takes advantage
    #       error checking information built into ValveController objects
    # Inputs:
    #   v1 - the first valve in the peristaltic pump
    #   v2 - the second valve in the peristaltic pump
    #   v3 - the third valve in the peristaltic pump
    #   ctlr - pyserial object that has a connection to the valve controlling device.
    def __init__(self, v1, v2, v3, ctlr):
        valves = []
        for v in (v1, v2, v3): #make sure each valve is a two character string so the arduino can parse the serial signal.
            v = '0'*(3-len(str(v)))+ str(v)
            valves.append(v)
        if len(set(valves)) < 3:  # if user entered the same valve more than once
            raise ValueError("Error: Please enter three different valve numbers to specify the pump.")
        self.valves = tuple(valves)
        self.ctlr = ctlr

    # peristalticPump.forward: run the peristaltic pump forward
    #   Inputs:
    #       rate - the rate at which to actuate pump cycles (Hz)
    #       cycles - the number of cycles to pump. Input -1 to run indefinitely.
    #       wait - boolean whether to pause the thread until the pumping sequence is finished.
    def forward(self, rate, cycles, wait = False):
        self._runPump(rate, cycles, 'f')

    # peristalticPump.reverse: run the peristaltic pump reverse
    #   Inputs:
    #       rate - the rate at which to actuate pump cycles (Hz)
    #       cycles - the number of cycles to pump. Input -1 to run indefinitely.
    #       wait - boolean whether to pause the thread until the pumping sequence is finished.
    def reverse(self, rate, cycles, wait = False):
        self._runPump(rate, cycles, 'r', wait = False)

    # peristalticPump._runPump: An abstract method for sending serial commands to actuate a pumping sequence. Should be
    #       implemented in a derived class.
    #   Inputs:
    #       rate - the rate at which to actuate pump cycles (Hz)
    #       cycles - the number of cycles to pump. Input -1 to run indefinitely.
    #       direction - the direction to pump. Should be either string 'f' for forward or string 'r' for reverse.
    #       wait - boolean whether to pause the thread until the pumping sequence is finished.
    #   Output: None
    def _runPump(self, rate, cycles, direction, wait = False):
        raise NotImplementedError("Error: run pump must be implemented in a peristasicPump derived class.")

    # peristalticPump.stop: Abstract method to stop a peristaltic pumping sequence before completion. Derived classes\
    #       should implement whatever serial commands are necessary for their device.
    #   Input: None
    #   Output: None
    def stop(self):
        raise NotImplementedError("Error: stop must be implemented in a peristalticPump derived class.")

    # peristalticPump.checkRateCycles: Checks that user input for the number of cycles and rate of peristaltic pump is
    #       valid. Accepted rates are 1-999 Hz, and number of cycles 1-999999 or -1 for indefinite.
    #   Inputs:
    #       rate - user rate input to check validity of.
    #       cycles - user cycles input to check validity of.
    #       wait - user input boolean whether to pause the thread until the pumping sequence is finished.
    #   Output: None, but will raise error if input invalid.
    def checkRateCycles(self, rate, cycles, wait):
        if type(cycles) != int:
            raise TypeError("Please enter an integer number of cycles.")
        if type(rate) != int:
            raise TypeError("Please enter an integer number of cycles per second.")
        if cycles > 999999 or cycles <-1 or cycles == 0: #KATARA serial protocol expects 6 character cycles or less.
            raise ValueError("Please enter from 1 to 999999 cycles or -1 cycles to pump continuously until interrupted.")
        if rate > 999 or rate < 1: #KATARA serial protocol expects 3 character rate or less
            raise ValueError("Please enter from 1 to 999 pump cycles per second.")
        if wait == -1 and wait:
            raise ValueError("Cannot run the pump indefinitely and pause the thread until execution is finished.")





