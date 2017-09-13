#MIT License
#
#Copyright (c) 2017 Jonathan A. White
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

try:
    from Tkinter import * #python 2.7
except:
    from tkinter import * #python 3
import time
from LabelEntry import LabelEntry
from Protocol_Tools import *
import config

# Base class for steps in a protocol. Should extend in each usage case for particular kinds of steps on other kinds devices
# Derived classes should add entries in the draw method, and place entries in self.entries array data member so they can
# the run method can iterate over them. Using just plain step acts as a pause in the protocol.
class Step:
    NestingRuleStatement = " Python expressions may refer to the iteration of the local loop as i[0], i[1] for the" \
                           " iteration of the loop that the local loop is nested inside, or i[n] for the nth outer" \
                           " loop where n is a natural number."
    parameter = "Step" #derived classes should set their parameter member. This will be used in protocols including
    #  many step types when adding a step, these protocols will prompt the user for what step type they wish to add,
    # and display buttons for each type labeled by their self.parameter member.

    # This is a tuple of illegal character for step names/types. A step that attemps to load a saved step named using a
    # special character will throw an error- the special character could be part of an attempt to execute malicious code.
    #illegalCharacters = ('!','@',"#", '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '<','>', '/', '[', ']', '{', '}',
    #'.',',',';',':',)

    # Step.__init__:
    # Inputs:
    #       _super - reference to the procedure holding the Step instance
    # Outputs: None
    def __init__(self, _super):
        self.box = LabelFrame(_super, padx=5, pady=5, text=self.parameter)
        self.super = _super
        self.steptype = "Step" #override in derived classes with their own name.
        # Used in Step.save, derived classes should not have to implement their own save method

        self.entries = []  # derived classes should place entry objects in here

    # Step.draw: Draws Step in super Procedure
    # Inputs:
    #       _row - the row in which to draw the step
    #       _col - the column in which to draw the step
    # Outputs: None
    def draw(self, _row, _col):
        self.col = _col
        self.row = _row
        self.box.grid(row=_row, column=_col, sticky=W)

    # Step.saveEntries: save user entered values before running or saving to file.
    # Inputs:
    #       type - string 'float' or 'int'; specifies whether entry should be a float or an int
    #       iters - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    # Outputs: None
    def saveEntries(self, type = "float", iters = None):
        for entry in self.entries:
            input = entry.get()
            if input == '':
                raise ValueError("Error: Entry unfilled in " + self.parameter + "step.")

            if type == "float":
                try:
                    entry.saved = float(input)
                    entry.expression = False
                except:
                    entry.saved = input
                    entry.expression = True

            elif type == "int":
                try:
                    entry.saved = int(input)
                    entry.expression = False
                except:
                    entry.saved = input
                    entry.expression = True
            else:
                raise ValueError("Invalid data type for "+self.parameter +" step.")

    # step.checkIfHasi: check if user entered 'i', but forgot to specify brackets. If so, give them a useful error
    # message.
    # Inputs:
    #       expr - User entered expression
    # Outputs: None
    def checkIfHasi(self, expr):
        if "i" in expr and "i[" not in expr:
            raise ValueError("The i variable is a python tuple. To access the iteration of the local loop, use i[0],"
                             " i[1] for the next outer loop, and so on.")


    # Step.recursiveIterCheck:This method recursively checks whether an expression inputed into a loop entry is valid
    # for all loops it is nested inside. The first call iterates over the first loop, and each recursive call iterates
    # over the next loop. The recursive calls terminate when all loops are accounted for
    # Inputs:
    #       iters - tuple where each entry is the number iterations in each nested loop, that has not b
    #       expression - string expression to evaluate for each iteration
    #       checkFunction - Function to check whether the valuation of the expression is valid at each iteration of the loops;
    #                accepts expression (above) and i (below); raises a ValueError if the evaluation is unacceptable.
    #       currentIters - tuple that stores the current interation of the outer loops, passed to inner loops.
    # Outputs: None
    def recursiveIterCheck(self, iters, expression, checkFunction, currentIters):
        if len(iters) > 0:
            for i1 in range(1,iters[-1]+1):
                i0 = (i1,) + currentIters
                self.recursiveIterCheck(iters[:-1], expression, checkFunction, i0)
        else: #empty list
            print("Check: ", currentIters)
            checkFunction(expression, currentIters)

    # Step.iterToString: When recursive IterCheck fails, feeds the iteration it failed on to an error message.
    # Inputs:
    #       i - tuple object containing the iteration of all parent loops/Protocol which contain this step.
    # Output: Sting giving the iterations of each loop in which a protocol fails.
    def iterToString(self, i):
        out = ''
        for j, k in enumerate(i):
            out += "i[" + str(j) + "] = " + str(k) + ", "
        return out

    #Step.save: returns a JSON serializable list specifying the information necessary to rebuild this list using the
    # the Step.load function; called when the user saves a protocol.
    # Inputs: None
    # Outputs:
    #       sList - a JSON serializable list specifying the information necessary to rebuild this list using the
    # the Step.load function
    def save(self):
        sList = [self.steptype]
        for i in self.entries:
            sList.append(i.get())
        return sList

    # Step.load: reinitializes a step from a list generated from Step.save. Used when loading saved protocols.
    # Input:
    #       sList - A list specifying the information necessary to intialize a step; must be in the format
    # Outputs: None
    def load(self, sList):
        if len(sList) != len(self.entries):
            raise ValueError("Error: List of saved entries is not the same length as the number of entries in this step object.")
        for i, entry in enumerate(self.entries):
            entry.saved = sList[i]
            entry.insert(0,sList[i])

    # Step.pause: Step.pause pauses the protocol thread for however long the step action needs to take
    # while checking whether the user has cancelled the protocol every 0.01 seconds.
    # Inputs:
    #       runtime - the time to pause
    #       cleanup - a function that cleans up some other objects, for example GUI text or color, when the user cancels
    #           a protocol run
    #       iter - tuple of loop iterations. None if the step is not inside a loop. The iteration of the immediate loop
    #               is stored in i[0], the first outer loop in i[1], and the nth outer loop in i[n].
    # Outputs: None
    def pause(self, runtime, cleanup = None, iter = None):
        self.box.config(bg = 'green')
        start = time.time()#clock()
        while time.time() - start < runtime:#clock() - start < runtime:
            self.timerWidget.config(text = "Step Runtime (s): " + str(int(time.time()-start)))#time.clock() - start)))
            self.event.wait(0.01) #event set in RoutineThread initialization
            self.checkIfCancel(cleanup = cleanup)
        self.timerWidget.config(text = '')
        self.timerWidget.grid_forget()
        try:
            self.box.config(bg = 'SystemButtonFace')
        except:
            self.box.config(bg='gray')

    # Step.checkIfCancel: Called during Step.run to check whether the user has cancelled the run. If they have, it
    # it returns the step icon to nonrunning view, and calls the passed cleanup function to return any other objects to
    # nonrunning configuration.
    #   Inputs:
    #       cleanup - a function that resets other objects involved in executing the protocol if the user cancels it.
    #           This is used in derived classes.
    #   Outputs: None
    def checkIfCancel(self, cleanup = None):
        if self.event.isSet():
            try:
                self.box.config(bg='SystemButtonFace')
            except:
                self.box.config(bg='gray')
            self.timerWidget.config(text="")
            config.stopEditing = False
            if cleanup:
                cleanup()  # clean up step before ending
            self.mainthread.join()  # mainthread set in ProcedureThread initialization
