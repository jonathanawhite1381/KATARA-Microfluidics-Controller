#MIT License
#
#Copyright (c) 2017 Jonathan A. White
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from Step import Step
from LabelEntry import LabelEntry
try:
    from Tkinter import * #python 2.7
except:
    from tkinter import * #python 3
from ValveController import ValveController

# ValveSteps are Steps in a Routine that open or close valves.
class ValveStep(Step):
    parameter = "Open/close valve" # this text is included in add step dialog boxes.

    # ValveStep.__init__: intializes ValveStep
    #   Input:
    #       _super - parent Tkinter frame object in which to draw ValveStep instance
    #   Output: None
    def __init__(self, _super):
        Step.__init__(self, _super)
        self.Valve = LabelEntry(self.box, 0, 0, "Valve:", width = 16)
        self.Valve.expression = False
        self.State = LabelEntry(self.box, 0, 2, "State:", width = 16)
        self.State.expression = False
        self.entries = [self.Valve, self.State]
        self.steptype = "ValveStep"

    # ValveStep.run: executes valve opening and closing
    #   Inputs:
    #       cleanup - does nothing for this class. Accepted as an argument because routines pass it to every object in
    #               their steps list. Other Step derivatives and loops use it.
    #       iter - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    #   Output: None
    def run(self, cleanup = None, iter = None):
        valves = []
        states = []
        for j in range(len(self.Valve.saved)):
            i = iter
            if self.Valve.expression:
                valves.append(eval(self.Valve.saved[j], {}, {'i' : i}))
            else:
                valves.append(int(self.Valve.saved[j]))
            if self.State.expression:
                states.append(eval(self.State.saved[j], {}, {'i' : i}))
            else:
                states.append(int(self.State.saved[j]))
            if states[-1] == 1:
                Step.btndict[valves[-1]].config(bg="green")
            else:  # the saved state is 0
                Step.btndict[valves[-1]].config(bg="gray")
        self.setValves(valves, states)
        Step.pause(self, 0)
        self.checkIfCancel()

    # ValveStep.saveEntries: save user entries for running or writing to file
    #   Inputs:
    #       type - data type that entries should be. Valve entries should be ints.
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    def saveEntries(self, type="int", iters=None):
        stateEntry = self.State.get()
        valveEntry = self.Valve.get()

        #first check if inputs are list, then check each entry
        stateEntry = stateEntry.replace(' ', '') #remove spaces
        states = tuple(stateEntry.rsplit(','))
        valves = tuple(valveEntry.rsplit(','))


        if len(set(valves)) < len(valves):
            raise ValueError("There are duplicate pin entries.")

        if len(states) != len(valves):
            if len(states) == 1:
                states = tuple(list(states)*len(valves))
            else:
                raise ValueError("The number of valves and states entered in Valve Step are different.")

        self.Valve.expression = [0]*len(states)
        self.State.expression = [0]*len(states)

        # check that all entries are valid
        for i in range(len(states)):
            self.checkValveStateEntry(valves[i], states[i], iters, listNum = i)

        #Save Entries
        self.State.saved = states
        self.Valve.saved = valves

    # ValveStep.checkValveStateEntry: Checks whether entries are valid. If step is in a loop and has an expression
    # That evaluates as a function of the loop iteration, recursively checks if it is valid for all loop iterations.
    #   Inputs:
    #       valve - user valve entry
    #       state - user state entry
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    #       listNum - the position in the comma separated list of user entered valves/states.
    def checkValveStateEntry(self, valve, state, iters, listNum = None):
        if not iters: # just look for integers
            try:
                valve1 = int(valve)
            except:
                raise ValueError(valve + " is not an available valve. Available valves are "
                                 + self.btndict["AvailablePinsStatement"] + ".")
            if valve1 not in self.btndict:
                raise ValueError(valve + " is not an available valve. Available valves are "
                                 + self.btndict["AvailablePinsStatement"] + ".")
            if state not in ("0", "1"):
                raise ValueError("Valve state " + state +"  is not allowed. "
                                    "The valve state must be either 1 (energized) or 0 (not energized).")
            self.setEntryExpressionBool(listNum, False, False)
            return

        try:
            valve = int(valve)
            valveIsInt = True
        except:
            valveIsInt = False
        if valveIsInt:
            if valve not in self.btndict:
                raise ValueError("Valve " + str(valve) + " is not available. Available valves are "
                                 + self.btndict["AvailablePinsStatement"])
        if valveIsInt and state in ("0","1"):
            self.setEntryExpressionBool(listNum, False, False)
            return
        elif state in ("0", "1"): #then either the valve entry is an expression or an error
            self.recursiveIterCheck(iters, valve, self.checkValidValveEntry, ())
            self.setEntryExpressionBool(listNum, True, False)
        elif valveIsInt: # Either the state entry is a correct python expression or an error
            self.recursiveIterCheck(iters, state, self.checkValidStateEntry, ())
            self.setEntryExpressionBool(listNum, False, True)
        else: #Both the state and valve entries are either expressions or errors
            self.recursiveIterCheck(iters, state, self.checkValidStateEntry, ())
            self.recursiveIterCheck(iters, valve, self.checkValidValveEntry, ())
            self.setEntryExpressionBool(listNum, True, True)

    # ValveStep.setEntryExressionBool: Sets whether each user entered state/valve is an expression or hard value.
    #   Inputs:
    #       entry - position in the user entered comma-separated list of valves/states.
    #       valveExprBool - 1 if expression, 0 if not
    #       stateExprBool - 1 if expression, 0 if not
    #   Outputs: None
    def setEntryExpressionBool(self, entry, valveExprBool, stateExprBool):
        self.State.expression[entry] = stateExprBool
        self.Valve.expression[entry] = valveExprBool

    # ValveStep.checkValidValveEntry: Evaluates an expression for a valve entry with given loop iterations and checks
    # whether it is valid.
    #   Inputs:
    #       valve - expression for a valve
    #       i - tuple of the iterations of all loops in which the valve step is nested inside.
    #   Outputs: None, but raises error if the valve entry is invalid at the given loop iterations.
    def checkValidValveEntry(self, valve, i):
        try:
            valve1 = eval(valve, {}, {'i': i})
            print(i, valve1)
        except Exception as E:
            self.checkIfHasi(valve)
            raise ValueError("Valve entry must either be an available valve or a valid python expression "
                             "evaluating to an available valve. Available valves are "
                             + self.btndict["AvailablePinsStatement"] + ". " + Step.NestingRuleStatement)
        if valve1 not in self.btndict:
            raise ValueError("Valve entry " + valve + " evaluates to " + str(valve1) + " on iteration "
                             + self.iterToString(i) + ". Available valves are " + self.btndict[
                                 "AvailablePinsStatement"])

    # ValveStep.checkValidStateEntry: Evaluates an expression for a state entry with given loop iterations and checks
    # whether it is valid.
    #   Inputs:
    #       ste - expression for a state
    #       i - tuple of the iterations of all loops in which the valve step is nested inside.
    #   Outputs: None, but raises error if the state entry is invalid at the given loop iterations.
    def checkValidStateEntry(self, state, i):
        try:
            state = eval(state,{}, {'i':i})
        except:
            self.checkIfHasi(state)
            raise ValueError("Valve state " + state +"  is not allowed. "
                            "State entries for valve steps must either be 1 (energized), 0 (denergized)"
                             " or, if in a loop, a python expression evaluating to 0 or 1." + Step.NestingRuleStatement)
        if state not in (0, 1):
            raise ValueError("State entries for valve steps must either be  1 (energized), 0 (denergized),"
                             " or a python expression evaluating to 1 or 0. For interation " + self.iterToString(i)
                             +" the expression evaluates to " + str(state) + ".")

    # ValveStep.setValves: Sends a serial command through a ValveController object to set valve states. Set upon
    # ValveController object's initialization in the KATARAGUI.connect method.
    #   Inputs:
    #       valve - tuple of valves to set the state of
    #       state - tuple of states to set corresponding valves to.
    #   Output: None
    def setValves(self, valve, state):
        raise NotImplementedError("Error: ValveStep.setValve must be set upon initialization of the device.")

# PumpSteps are steps in a Routine that run peristaltic pumping sequences.
class PumpStep(Step):
    parameter = "Pump"

    # PumpStep.__init__
    #   Input:
    #       _super - parent Tkinter frame object in which to draw ValveStep instance
    #   Output: None
    def __init__(self, _super):
        Step.__init__(self, _super)
        self.box.config(text = "Pump")
        self.rate = LabelEntry(self.box, 0, 0, "Rate (cycles/s):", width = 3)
        self.nCycles = LabelEntry(self.box, 0, 2, "Number of Cycles:", width = 9)
        self.steptype = "PumpStep"

        valvesbox = LabelFrame(self.box)
        valvesbox.grid(row = 1, column = 0, columnspan = 10)
        self.valveEntries = []
        for valve in (1,2,3):
            self.valveEntries.append(LabelEntry(valvesbox, 1, 2*valve, " --> Valve " + str(valve) + ": ", width = 2))
        self.entries = [self.rate, self.nCycles]+ self.valveEntries
        self.box.pack()

    # PumpStep.saveEntries: Saves user entered entries in PumpStep for running or writing to saved file. If there are
    # Expressions that evaluate as a function of loop iteration, all loop iterations are checked recursively.
    #   Inputs:
    #       type - data type the user entries should be, for PumpStep, should be ints.
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    #   Output: None
    def saveEntries(self, type="int", iters=None):
        rate = self.rate.get()
        cycles = self.nCycles.get()

        # Check if valve entries are ok for all loop iterations.
        valves = []
        allInt = True
        for v in self.valveEntries:
            v0 = v.get()
            valves.append(v0)
            try:
                v1 = int(v0)
                if v1 not in self.btndict:
                    raise ValueError(v0 + " in pump step is not a valid valve. Valid valves are " +
                                     self.btndict["AvailablePinsStatement"] + ".")
                v.expression = False
            except:
                if not iters:
                    raise ValueError(v0 + " in pump step is not a valid valve. Valid valves are " +
                                 self.btndict["AvailablePinsStatement"] + ".")
                else: #check if valid expression fo valve
                    self.recursiveIterCheck(iters, v0, self.checkValidValveEntry, ())
                    v.expression = True
                    allInt = False
        if allInt:
            if len(set(valves)) < 3:
                raise ValueError("There are duplicate valve entries")
        else:
            self.recursiveIterCheck(iters, valves, self.checkDuplicateValves, ())

        try:
            rate1 = int(rate)
            if rate1 < 0:
                raise ValueError(rate + " is not a valid rate for a pump step. Rates must be positive integers.")
            self.rate.expression = False
        except:
            if not iters:
                raise ValueError(rate + " is not a valid rate for a pump step. Rates must be positive integers.")
            else: #check if valid expression.
                self.recursiveIterCheck(iters, rate, self.checkValidRate, ())
                self.rate.expression = True

        try:
            try:
                cycles1 = int(cycles)
            except:
                if not iters:
                    raise ValueError(
                        cycles + " is not a valid number of cycles for a pump step. The number of cycles must"
                                 " be either a positive integer or -1 to pump indefinitely until interupted.")
                else:  # check if valid expression
                    self.recursiveIterCheck(iters, cycles, self.checkValidCycles, ())
                    self.nCycles.expression = True
                    Step.saveEntries(self, type="int", iters=iters)
                    return

            if cycles1 == -1:
                if iters:
                    raise ValueError("Pump steps can pump indefinitely only if they"
                                             " are the final step in a protocol.")
                else:
                    if hasattr(self, 'last') and not self.last:
                        raise ValueError("Pump steps can pump indefinitely only if they"
                                             " are the final step in a protocol.")


            if cycles1 < -1:
                if iters:
                    raise ValueError(
                    cycles + " is not a valid number of cycles for a pump step. The number of cycles must be"
                             " a positive integer.")
                else:
                    raise ValueError(
                        cycles + " is not a valid number of cycles for a pump step. The number of cycles must be"
                                 " a positive integer, or -1 on the final step of a protocol to pump indefinitely.")
            self.nCycles.expression = False
        except ValueError as E:
            raise E

        Step.saveEntries(self, type = "int", iters = iters)

    # PumpStep.checkValidRate: If pumpstep is in a loop and has an expression entry for rate as a function of the loop
    # iteration, checkValidRate checks whether the expression evaluates to a valid rate on the given iteration.
    #   Input:
    #       input - Expression for the rate
    #       i - tuple of iterations for each outer loop. The immediate outer loop is the the first position, the
    #           outer-most loop is in the last position.
    #   Output: None, but throws an error if invalid.
    def checkValidRate(self, input, i):
        try:
            rate = eval(input, {}, {'i' : i})
            if type(rate) != int or rate < 1:
                raise ValueError()
        except:
            raise ValueError(input + " is not a valid rate for a pump step. Rates must be positive integers or, in a "
                            "loop, python expressions evaluating to positive integers." + self.NestingRuleStatement)
        if (type(rate) != int and type(rate) != float) or rate < 0:
            raise ValueError(input + " is not a valid rate for a pump step. Rates must be positive integers or, in a "
                            "loop, python expressions evaluating to positive integers." + self.NestingRuleStatement)

    # PumpStep.checkValidCycles: If pumpstep is in a loop and has an expression entry for number of cycles as a function
    # of the loop iteration, checkValidCycles checks whether the expression evaluates to a valid number of cycles on
    # the given iteration.
    #   Input:
    #       input - Expression for the number of cycles
    #       i - tuple of iterations for each outer loop. The immediate outer loop is the the first position, the
    #           outer-most loop is in the last position.
    #   Output: None, but throws an error if invalid.
    def checkValidCycles(self, input, i):
        try:
            cycles = eval(input, {}, {'i' : i})
            if type(cycles) != int or cycles < 1:
                raise ValueError()
        except:
            raise ValueError(input + " is not a valid number of cycles for a pump step. The number of cycles must be"
                                      " a positive integer.")
        if cycles == -1:
            raise ValueError("You cannot pump indefinately inside a loop. " + input + " in pump step evaluates to -1 on"
                            " iteration " + self.iterToString(i) + ".")
        if type(cycles) != int or int < 1:
            raise ValueError("Number of cycles" + input + " evaluates to " + cycles + " on iteration "
                       + self.iterToString(i) + ". The number of cycles must be a positive integer.")


    # PumpStep.specifyPump: Create pump object using a ValveControllerObject. Set upon instantiation of ValveController
    # in KATARAGUI.connect.
    #   Inputs:
    #       v1 - the first valve in the peristaltic pump
    #       v2 - the second valve in the peristaltic pump
    #       v3 - the third valve in the peristaltic pump
    #   Output:
    #       returns KATARAPump Object
    def specifyPump(self, v1, v2, v3):
        raise NotImplementedError("Error: Pumpstep.specifyPump must be set upon initialization of the device.")

    # PumpStep.changeValveColor: Changes the color of the valve button while the pump is running.
    #   Input:
    #       color - the color to change the valve button to.
    #   Output: None
    def changeValveColor(self, color):
        for v in self.pump.valves:
            Step.btndict[int(v)].config(bg=color)

    # PumpStep.cleanup: Resests GUI after finishing pump sequence.
    #   Inputs: None
    #   Outputs: None
    def cleanup(self): #call this method if a protocol is canceled in the middle of a pump step
        self.pump.ctlr.ser.write("c")
        self.changeValveColor("gray")

    # PumpStep.run: runs the pump sequence.
    #   Inputs:
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    #       time - time to pause thread while the pump sequence is running.
    #   Outputs: None
    #def run(self, cleanup = None, iter = None, time = None):
    def run(self, iter=None, time=None):
        i = iter

        valves = []
        for v in self.valveEntries:
            if v.expression:
                valves.append(eval(v.saved, {}, {'i' : i}))
            else:
                valves.append(v.saved)
        self.pump = self.specifyPump(valves[0], valves[1], valves[2])
        ValveController.pPumps.remove(self.pump)
        self.changeValveColor("Blue")
        if self.nCycles.expression:
            nCycles = eval(self.nCycles.saved, {}, {'i' : i})
        else:
            nCycles = self.nCycles.saved
        if self.rate.expression:
            rate = eval(self.rate.saved, {}, {'i' : i})
        else:
            rate = self.rate.saved
        self.pump.forward(rate, nCycles)
        if nCycles == -1:
            Step.pause(self, float('Inf'), cleanup=self.cleanup)
        else:
            Step.pause(self, float(nCycles)/float(rate), cleanup=self.cleanup)
        Step.pause(self, time, cleanup = self.cleanup)
        self.changeValveColor("gray")

    # PumpStep.checkValidValveEntry: If PumpStep is in a loop and has an expression entry for a valve as a function
    # of the loop iteration, checkValidValve checks whether the expression evaluates to a valid valve on
    # the given iteration.
    #   Input:
    #       input - Expression for the valve
    #       i - tuple of iterations for each outer loop. The immediate outer loop is the the first position, the
    #           outer-most loop is in the last position.
    #   Output: None, but throws an error if invalid.
    def checkValidValveEntry(self, valve, i):
        try:
            valve = eval(valve, {}, {'i': i})
            print(i, valve)
        except:
            self.checkIfHasi(valve)
            raise ValueError("Valve entry must either be an available valve or a valid python expression "
                             "evaluating to an available valve. Available valves are "
                             + self.btndict["AvailablePinsStatement"] + ". " + Step.NestingRuleStatement)
        if valve not in self.btndict or type(valve) != int or valve < 1:
            raise ValueError("Valve entry " + str(valve) + " evaluates to " + str(valve) + " on iteration "
                             + self.iterToString(i) + ". Available valves are " + self.btndict[
                                 "AvailablePinsStatement"])

    # PumpStep.checkDuplicateValves: Checks if expressions for valves evaluate to duplicates on a given loop iteration.
    #   Inputs:
    #       valves - list of valves to evaluate
    #       i - the iteration of all outer loops.
    #   Outputs: None
    def checkDuplicateValves(self, valves, i):
        evaledValves = []
        for v in valves:
            evaledValves.append(eval(v, {}, {'i':i}))
        if len(set(evaledValves)) < 3:
            raise ValueError("There are duplicate valves on iteration " + self.iterToString(i))

# Pauses a protocol
class PauseStep(Step):
    parameter = "Pause"
    # PauseStep.__init__: intializes PauseStep
    #   Input:
    #       _super - parent Tkinter frame object in which to draw PauseStep instance
    #   Output: None
    def __init__(self, _super):  # super is a reference to the procedure holding the item instance
        Step.__init__(self, _super)
        self.steptype = "PauseStep"
        self.time = LabelEntry(self.box, 0, 0, "Time (s):")
        self.time.expression = None
        self.entries.append(self.time)

    # PauseStep.saveEntries: Save user entered time value for running or writing to file.
    #   Inputs:
    #       type - data types accepted - float for PauseStep
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    #   Output: None
    def saveEntries(self, type = "float", iters = None):
        timeEntry = self.time.get()
        if not iters:
            time = float(timeEntry)
            if time < 0:
                raise ValueError(
                    "Invalid pause time: " + self.timeEntry + "; you cannot pause for a negative amount of time.")
            self.time.expression = False
        else:
            self.recursiveIterCheck(iters, timeEntry, self.inputCheckForPause, ())
            self.time.expression = True
        Step.saveEntries(self)

    # PauseStep.inputCheckForPause: If PauseStep is in a loop and has an expression entry for a pause time as a function
    # of the loop iteration, inputCheckForPause checks whether the expression evaluates to a valid time on
    # the given iteration.
    #   Input:
    #       input - Expression for the pause time
    #       i - tuple of iterations for each outer loop. The immediate outer loop is the the first position, the
    #           outer-most loop is in the last position.
    #   Output: None, but throws an error if invalid.
    def inputCheckForPause(self, expression, i):
        try:
            time = eval(expression, {}, {'i' : i})
        except:
            self.checkIfHasi(expression)
            raise ValueError("Expression " + expression + " in Pause step does not evaluate to a positive float on "
                                                          "iteration " + self.iterToString(i) + ".")
        if (type(time) != float and type(time) != int) or time < 0:
            raise ValueError("Cannot pause for " + expression + " seconds on iteration" + self.iterToString(i)
                             + ". You can only pause for a positive integer of float number of seconds.")



    # Step.run pauses the protocol. The function is still called run to allow duck typing.
    #   Input:
    #       cleanup - function to cleanup after step: None for Step.run
    #       iter - tuple of the number iterations for each outer loop. The immediate outer loop is the the first
    #       position, the outer-most loop is in the last position.
    #   Output: None
    def run(self, iter = None):
        i = iter
        if self.time.expression:
            runtime = eval(self.time.saved, {}, {'i' : i})
        else:
            runtime = self.time.saved
        Step.pause(self, runtime)
