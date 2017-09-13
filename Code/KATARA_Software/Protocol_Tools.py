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
    import tkFileDialog
    from tkSimpleDialog import Dialog
    import tkMessageBox
except:
    from tkinter import * #python 3
    from tkinter import filedialog
    tkFileDialog = filedialog
    from tkinter import simpledialog
    tkSimpleDialog = simpledialog
    from tkinter import messagebox
    tkMessageBox = messagebox
    Dialog = simpledialog.Dialog
import time
from threading import Thread
import threading
import json
from Step import Step
from StepDerivatives import *
from LabelEntry import LabelEntry
from no_wait_Dialog import no_wait_Dialog
import config


# Routine is a base class that manages a list of items to execute. Items can be either loops or single steps.
# each item will be grouped into a label frame placed into the the first column of its row.
# The Protocol and Loop classes inherit from Routines abd share methods from Routine to manage a list of steps.

class Routine(object):
    connected = False # set to true after connecting. #Note: this could cause problems if multiple devices require connecting

    # This is a tuple of illegal character for step names/types. A step that attemps to load a saved step named using a
    # special character will throw an error- the special character could be part of an attempt to execute malicious code.
    illegalCharacters = (
    '!', '@', "#", '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '<', '>', '/', '[', ']', '{', '}',
    '.', ',', ';', ':',)

    # Routine.__init__: Initialilizes Routine Objects
    #   Input:
    #       master - parent Tkinter frame that the routine is placed inside
    def __init__(self, master):
        self.steps = []  # stores references to items in procedure in the order they are displayed in the window
        self.Buttons = []  # store references to add buttons so they can be deleted if desired
        self.master = master
        self.routineFrame = LabelFrame(self.master, text='', padx=10, pady=10)
        self.addButtons()

    # Set the steps available to be added to the routine by clicking "add step" buttons.
    # This allows developers to easily write new step classes to be included in the GUI. This function
    # shold be called when intializing the GUI.
    #
    # Input: _stepImplementation is either a class of a step type to be availabe when adding a step, or a tuple of step
    # type classes
    #
    # Output: None
    def setStepImplementation(self, _stepImplementation):
        Routine.stepImplementation = _stepImplementation

    # Routine.draw: Shared drawing code used in both the Protocol and Loop draw the methods
    #   Inputs:
    #       _row - the row of the parent Tkinter Frame in which to place the routine
    #       _col - the column of the parent Tkinter Frame in which to place the routine
    #   Output: None
    def draw(self, _row, _col):
        self.row = _row # for redrawing
        self.col = _col
        self.routineFrame.grid_remove()
        self.routineFrame.grid(row=_row, column=_col, sticky=W, columnspan=3)
        for row, item in enumerate(self.steps):
            item.draw(row, 0)
        for row, btnRow in enumerate(self.Buttons):
            for col, btn in enumerate(btnRow):
                btn.grid(row=row, column=col+1)

    # Routine.resetPbox: removes items from display so they can be redrawn if new items or added or if a new protocol
    #   is loaded.
    # Input: None
    # Output: None
    def resetPbox(self):
        for item in self.steps:
            try:
                item.grid_remove()
            except AttributeError:
                pass  # do nothing, there's nothing there
        for btnRow in self.Buttons:
            for btn in btnRow:
                btn.grid_remove()

    # Routine.redraw: Redraws a Routine
    # Input: None
    # Output: None
    def redraw(self):
        self.resetPbox()
        self.draw(self.row, self.col)

    # Routine.addStep: If the protocol accepts multiple kinds of steps, prompts the user for what kind of step to add
    # to the routine, if only one kind of step is available, it adds that step with no prompt. It is called from an
    # 'add' button that gives the index into which the step will be inserted.
    #   Inputs:
    #       index - the index of the steps list data member into which the step will be inserted. Supplied by the
    #               calling button.
    #   Outputs: None
    def addStep(self, index):
        if config.stopEditing:
            no_wait_Dialog(self.master, "Error", "You cannot edit a protocol while it is running.")
            return
        if Protocol.running:
            raise tkMessageBox.showerror("Error", "You cannot edit a protocol while you are running it.")

        # If the protcol allows more than one step type
        if type(self.stepImplementation) == set or type(self.stepImplementation) == list or type(self.stepImplementation) == tuple:
            whatKindOfStep = Toplevel(self.master)
            whatKindOfStep.transient(self.master)


            whatStepWin = Frame(whatKindOfStep)
            whatStepWin.pack()
            whatStepWin.grab_set()
            Label(whatStepWin, text = "What kind of step would you like to add?").grid(row = 0, column = 0, columnspan =100, pady = 5, padx = 5)

            # addCommand is attached to the buttons for each step type in the "What kind of step..." prompt window.
            def addCommand(index, _stepImp):
                self.steps.insert(index, _stepImp(self.routineFrame))
                self.addButtons()
                self.redraw()
                whatKindOfStep.destroy()
            for i, stepImp in enumerate(self.stepImplementation):
                Button(whatStepWin, text=stepImp.parameter, command=lambda ind = index, stp = stepImp : addCommand(ind, stp)).grid(row=1, column=i)

        else: #The protocol only allows one step type.
            self.steps.insert(index, self.stepImplementation(self.routineFrame))# pass reference to superior object
            self.addButtons()
            self.redraw()

    # Routine.addLoop: Adds a loop to a routine. The index of the routine steps list in which to insert the loop is
    #               supplied by the calling button.
    #   Input:
    #       index - the index of the routine steps list in which to insert the loop. Supplied by the calling button.
    #   Output: None
    def addLoop(self, index):
        if config.stopEditing:
            no_wait_Dialog(self.master, "Error", "You cannot edit a protocol while it is running.")
            return
        newloop = Loop(self.routineFrame)
        newloop.setStepImplementation(self.stepImplementation)
        self.steps.insert(index, newloop)
        self.addButtons()
        self.redraw()

    # Routine.addButtons: adds buttons when a new step or loop is drawn.
    #   Input: None
    #   Output: None
    def addButtons(self):
        last = len(self.steps)
        btnRow = [Button(self.routineFrame, text="Add Step", command=lambda: self.addStep(last))]
        btnRow.append(Button(self.routineFrame, text="Add Loop", command=lambda: self.addLoop(last)))
        if last > 0: #add a remove button to the last that has
            self.Buttons[-1].append(Button(self.routineFrame, text="Remove", command=lambda: self.remove(last - 1)))
        self.Buttons.append(btnRow)

    # Routine.remove: Removes a step or loop from a protocol. Called by remove buttons.
    #   Input:
    #       index - the index of the step or loop to remove
    #   Output: None
    def remove(self, index):
        if config.stopEditing:
            no_wait_Dialog(self.master, "Error", "You cannot edit a protocol while it is running.")
            return
        self.steps[index].box.grid_forget()
        self.steps.pop(index)
        for btn in self.Buttons[-1]:
            btn.grid_forget()
        if len(self.Buttons) > 0:
            self.Buttons[-2][-1].grid_forget()
            self.Buttons[-2].pop()
        self.Buttons.pop()
        self.redraw()

    # Routine.saveEntries: Saves entries in a Routine Loop or Protocol
    #   Input: None
    #   Output: None
    def saveEntries(self):
        nItems = len(self.steps)
        for i, item in enumerate(self.steps):
            if i != nItems -1 or hasattr(self, 'activeLoop'): #can't be last item if routine object is a loop
                item.last = False
            else:
                item.last = True
            try:
                item.saveEntries()
            except Exception as E:
                if hasattr(item, 'activeLoop'): #then item is a loop. Only turn yellow if iteration error.
                    if E.message in ("Error: Unfilled number of iterations in loop.",
                                     "You must loop over a postitive integer number of iterations.",
                                     "You cannot run a loop with no steps!") or " is not a valid n" in E.message:
                        item.box.config(bg = 'yellow')
                        #turn yellow
                else: #turn yellow
                    item.box.config(bg = 'yellow')

                #in anycase, raise the error again.
                raise E
            if item.box.cget("bg") == "yellow":
                try:
                    item.box.config(bg = 'SystemButtonFace')
                except:
                    item.box.config(bg='gray')

    # Routine.save: Generate JSON serializable list containing information necessary to reconstruct routine
    #   Inputs: None
    #   Outputs: List of steps and loops in routine to be saved in the JSON format.
    def save(self):
        try:
            routineList = []
            for i in self.steps:
                routineList.append(i.save())
            return routineList
        except E:
            tkMessageBox.showerror("Error", E.message)

    # Routine.load: Reconstructs a saved routine from a list in a JSON file as generated in Routine.save.
    #   Inputs:
    #       savedRoutine - list of a saved routine and all its steps used to reconstruct a saved routine.
    #   Outputs: None
    def load(self, savedRoutine):
        self.steps = [] # reset items list  member
        self.Buttons = []
        self.addButtons()
        for i in savedRoutine: # elements of savedRoutine should a be lists where the zeroth element is the type of saved object as a string
            self.checkIfHasIllegalCharacters(i[0])
            item = eval(i[0])(self.routineFrame)
            item.load(i[1:])
            self.steps.append(item)
            self.addButtons()
        self.resetPbox()

    # Routine.checkIfHasIllegalCharacters : Checks if a string has illegal characters that could be used in malicious
    # code before eval is called on it.
    #   Input:
    #       s - string to check for illegal characters
    #   Output: None, but throws an error if an illegal character is found.
    def checkIfHasIllegalCharacters(self, s):
        for char in self.illegalCharacters:
            if char in s:
                raise ValueError('Illegal character' + char +' is the Step name: '+ s +'.')

    # Routine.run: runs a routine.
    #   Inputs:
    #   iter - used in derived classes: a tuple containing the number of iterations each outer loop will be iterated over. The immediate outer
    #           loop is first, the second outer loop is second, and so on. This is used for recursive error checking.
    def run(self, iter = None):
        for i in self.steps:
            i.run()

    # Routine.disconnected: Called by event handler if an arduino is disconnected while a protocol is running.
    #   input:
    #       input - accepts input from the event handler, but is not actually used.
    def disconnected(self, input = None):
        tkMessageBox.showerror("Error", "The connection with the arduino was lost and the protocol was terminated.")

    # Routine.warning: Called by event handler if an arduino connection is disrupted and recovered while a protocol is running.
    #   input:
    #       input - accepts input from the event handler, but is not actually used.
    def warning(self, input = None):
        no_wait_Dialog("Warning","There was a problem in the connection. "
                                 "The connection has been reset and the valve states have been restored.")

# Derived Class from Routine that adds extra error handling for communicating the the Arduinoi Firmware.
class ArduinoErrorProofedRoutine(Routine):
    vGUI = None #parent GUI, set in ValveGUI.__init__; this is used for error recovery.

    # ArduinoErrorProofedRoutine.run: The same as Routine.run with extra error handling
    #   Inputs:
    #       iter - used in derived classes: a tuple containing the number of iterations each outer loop will be iterated over. The immediate outer
    #           loop is first, the second outer loop is second, and so on. This is used for recursive error checking.
    #   Outputs:
    #       returns "Error" if there is a connection problem which recursively returns to the root calling run method to
    #       stop the protocol.
    def run(self, iter = None):
        for i in self.steps:
            try:
                ret = i.run(iter = iter)
                if ret  == "Error":
                    return "Error" #propogate up errors to calling loops/routines to stop protocol.
            except Warning as W:
                print("Warning!")
                print(W.message)
                if self.vGUI.device == "Arduino Mega":
                    self.master.event_generate("<<connection_warning>>", when = "tail")
                    from KATARAGUI import pumpGUI
                    for pGUI in pumpGUI.instances:
                        valves = pGUI.pump.valves
                        pGUI.pump = self.device.specifyPump(int(valves[0]), int(valves[1]), int(valves[2]))
            except Exception as E:
                print("Error!")
                print(E.message)
                Protocol.pRun.event.set()
                print(str(self.master.__class__))
                print(self.master.event_generate("<<disconnected_error>>", when = "tail"))
                return "Error" # stop protocol, bubbles up in first try statement above.
        return None

# Dialog box for prompting users what kind of step they would like to add; inherits from the Tkinter Dialog class.
class addStepDialog(Dialog):
    # addStepDialog.__init__
    #   Inputs:
    #       parentRoutine - Routine that we are adding a step to.
    #       index - Index in the parent routine to which the step will be added.
    def __init__(self, parentRoutine, index = None):
        self.parentRoutine = parentRoutine
        self.index = index
        Dialog.__init__(self, parentRoutine.master, title ="Add Step")

    # addStepDialog.body: Overwrites Dialog.body to provide custom message. Called in Dialog.__init__
    def body(self, frame):
        Label(frame, text="What kind of step would you like to add?").pack()

    # addStepDialog.buttonbox: Overwrites Dialog.buttonbox to create a box of custom buttons for dialog window. Called in Dialog.__init__
    def buttonbox(self):
        box = Frame(self)
        for i, stepImp in enumerate(self.parentRoutine.stepImplementation):
            Button(box, text=stepImp.parameter, command=lambda stp=stepImp:self.addCommand(stp)).grid(row=1, column=i)
        box.pack()


    # addStepDialog.addCommand: called by add step buttons to add a step.
    #   Inputs:
    #       stp - step type to add
    #   Output: None
    def addCommand(self, stp):
        self.parentRoutine.addCommand(self.index, stp)
        self.ok()


# Protocol classes are derived from routine, they implement control buttons at the top of the protocol box and provide
# a framework for editing custom protocols. They also can run non editable saved protocols that are loaded as buttons.
class Protocol(ArduinoErrorProofedRoutine):
    running = False
    holdFlag = False #set to true from external object when unsafe to start a protocol
    holdErrorMessage = "" #set error message to prompt user when user tries to start a protocol when holdFlag is True

    # Protocol.__init__:
    #
    # Inputs:
    #       _master - the parent Tkinter frame that the Protocol will be nested inside
    #       _writable - Defines whether this protocol is displayed in editable form. If not, the protocol is stored
    #                   in a custom protocol button. Clicking custom protocol buttons calls the protocol's run function.
    def __init__(self, _master, writable = True):
        self.box = LabelFrame(_master, text = "Protocol")
        super(Protocol, self).__init__(self.box)
        self.controlbox = LabelFrame(self.box)
        self.controlbox.grid(row = 0, column = 0, sticky = W)
        self.runbtn = Button(self.controlbox, text="Run Protocol", command=self.run)
        self.runbtn.pack(side = LEFT)
        Button(self.controlbox, text = "Save Protocol", command = self.save).pack(side = LEFT)
        Button(self.controlbox, text = "Load Protocol", command = self.loadProtocol).pack(side = LEFT)
        self.selfRunning = False
        self.writable = writable
        _master.bind("<<connection_warning>>", self.warning)
        _master.bind("<<disconnected_error>>", self.disconnected)
        if writable:
            self.setName("Run Protocol") #Displays "Run Protcol" text in run button.
            Routine.redraw = self.redraw # this line means that anytime the protocol is changed from any of its component objects, such as by a load or an add
            #action within a loop, the entire protocol is redrawn. All routine objects redraw the entire protocol. This line should not be executed
            #for protocols stored in custom buttons.

    # Protocol.setName - Sets the name of a protocol object for display on its calling button.
    #
    # Inputs:
    #       name - the name of the protocol
    # Outputs:
    #       None
    def setName(self, name):
        self.name = name

    # Protocol.drawProtocol - Draws a protocol
    #
    # Inputs:
    #       _row - row of the parent Tkinter frame where the Protocol will be placed using the grid manager
    #       _col = column of the parent Tkinter frame where the Protocol will be placed using the grid manager
    # Outputs:
    #       None
    def drawProtocol(self, _row, _col):
        self.row = _row
        self.col = _col
        self.box.grid(row = _row, column = _col, columnspan = 3, sticky = W)
        self.draw(_row, _col)

    # Protocol.save: Shows the user a save dialog box so they can save the protocol they are editing using JSON format.
    #   Inputs: None
    #   Outputs: None
    def save(self):
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot save a protocol while it is running. "
                    "Please either wait until the protocol finishes or stop it before saving it.")
            return
        if self.steps == []:
            tkMessageBox.showerror("Error", "You have not added any steps to your protocol. There is nothing to save!")
            return
        try:
            self.saveEntries()
        except ValueError as error:
            tkMessageBox.showerror("Error", error.message)
            return
        with tkFileDialog.asksaveasfile(mode = 'w', title="Save protocol", defaultextension = '.txt') as file:
            protocolList = Routine.save(self)
            protocolList.insert(0,"This is a saved Protocol") #This will help us deterimine whether loaded objects are infact saved protocols
            json.dump(protocolList, file)

    # Protocol.loadProtocol: Prompts user to choose a saved protocol file, reads the file, and replaces the protocol displayed
    # in the editing panel at the time of calling with the saved protocol.
    #   Inputs: None
    #   Outputs: None
    def loadProtocol(self):
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot load new protocol while a protocol is running. "
                    "Please either wait until the current protocol finishes or stop it before loading a new one.")
            return
        with tkFileDialog.askopenfile(mode = 'r', title = "Open Protocol") as file:
            try:
                savedProtocol = json.load(file)
                if savedProtocol[0] != "This is a saved Protocol":
                    raise ValueError("Error: This file is not a saved Protocol")
                savedProtocol.pop(0)
                while self.steps:
                    self.remove(0)


                self.load(savedProtocol)
                self.redraw()
            except Exception as E:
                tkMessageBox.showerror("Error", E.message)



    # Protocol.run: Executes the protocol, or stops it if it is already running.
    #   Inputs:
    #       iters - a tuple containing the number of iterations each outer loop will be iterated over. The immediate outer
    #               loop is first, the second outer loop is second, and so on. This is used for recursive error checking.
    def run(self, iter=None):
        if Protocol.holdFlag:
            tkMessageBox.showerror("Error", self.holdErrorMessage)
            return
        if not self.connected: #note: If the protocol uses multiple devices, this will need to be modified
            tkMessageBox.showerror("Error","Error: Not connected to the device.")
            return
        if not self.steps:
            tkMessageBox.showerror("Error", "There are no steps in this protocol!")
            return

        if self.running: #stop run
            if not self.writable:
                try:
                    self.runbtn.config(bg='SystemButtonFace', text=self.name)
                except:
                    self.runbtn.config(bg='gray', text=self.name)
            else:
                try:
                    self.runbtn.config(bg ='SystemButtonFace', text = "Run Protocol")
                except:
                    self.runbtn.config(bg='gray', text="Run Protocol")
            Routine.pRun.event.set() #sends message to protocol running in separate thread to stop
            self.running = False
            RoutineThread.protocolRunning = False

            if Loop.activeLoop:
                Loop.activeLoop.currIter.config(text="")
            return


        else: #start run
            try:
                self.saveEntries()
            except Exception as E:
                tkMessageBox.showerror("Error", E.message)
                return
            try:
                #Protocols are run in a separate thread so users can continue to interact with the GUI as it runs.
                Routine.pRun = RoutineThread(Routine.run, self, threading.current_thread(),
                                             button = not self.writable)
            except Warning as W:
                no_wait_Dialog(self.master, message = W.message, title = "Warning")
                print("Warning Dialog")
            except Exception as E:
                no_wait_Dialog(self.master, message= E.message, title = "Error")
                print("Error Dialog")
                return
            self.running = True
            self.runbtn.config(bg = 'red', text = "Cancel Run")
            if self.writable:
                config.stopEditing = True

            #pass reference to timer Widget to step Class
            timerWidget = Label(self.controlbox, text = "Step Runtime: ")
            timerWidget.pack(side = RIGHT)

            Step.timerWidget = timerWidget
            Protocol.pRun.start()

# Loop : Inherits from the ArduinoErrorProofedRoutine class, and manages a list of steps, that could include other
# loops, to be executed.
class Loop(ArduinoErrorProofedRoutine):
    activeLoop = None #reference active loop so that if a protocol is cancelled while a loop is running, we can remove "iterations:" label.

    # Loop.__init__
    # Input:
    #   master - a Tkinter frame that the Loop will be nested in
    # Output:
    #   None
    def __init__(self, master):
        # Loop frames hold the routine frame with steps and sub-loops, as well as a bar to specify # iterations
        self.box = LabelFrame(master, text="Loop")
        self.iterations = LabelEntry(self.box, 0, 0, "Number of iterations: ")
        self.currIter = Label(self.box, text="") #Displays current iteration while running
        self.currIter.grid(row=0, column=2)
        self.steptype = "Loop" #also alows Loops to be saved and loaded as if steps.
        super(Loop, self).__init__(self.box)

    # Loop.draw:
    #   Inputs:
    #       _row - the row of the Tkinter parent frame in which the loop will be drawn with the grid manager
    #       _cos - the column of the Tkinter parent frame in which the loop will be drawn with the grid manager
    #   Output: None
    def draw(self, _row, _col):
        self.box.grid(row=_row, column=_col, sticky=W)
        super(Loop, self).draw(1, 0)

    # Loop.saveEntries: Called before running or saving a protocol. Checks to make sure all entries are valid (recursively
    #   for nested loops) and saves the values so the protocol will not crash even if the user changes values during a run.
    # Input:
    #   iters - a tuple containing the number of iterations each outer loop will be iterated over. The immediate outer
    #           loop is first, the second outer loop is second, and so on. This is used for recursive error checking.
    # Output: None
    def saveEntries(self, iters = None):
        saveIter = self.iterations.get()
        if saveIter == "":
            raise ValueError("Error: Unfilled number of iterations in loop.")
        try:
            self.saveIter = int(saveIter)
        except:
            raise ValueError(saveIter + " is not a valid n")
        if self.saveIter < 1:
            raise ValueError("You must loop over a postitive integer number of iterations.")
        if self.steps == []:
            raise Exception("You cannot run a loop with no steps!")
        for item in self.steps:
            if iters:
                _iters = tuple([self.saveIter]+list(iters))
            else:
                _iters = (self.saveIter,)

            try:
                item.saveEntries(iters = _iters)
                if item.box.cget('bg') == "yellow":
                    try:
                        item.box.config(bg = 'SystemButtonFace')
                    except:
                        item.box.config(bg = 'gray')
            except Exception as E:
                if hasattr(item, 'activeLoop'):  # then item is a loop. Only turn yellow if iteration error.
                    if E.message in ("Error: Unfilled number of iterations in loop.",
                             "You must loop over a postitive integer number of iterations.",
                             "You cannot run a loop with no steps!") or " is not a valid n" in E.message:
                        item.box.config(bg='yellow')
                # turn yellow
                else:  # turn yellow
                    item.box.config(bg='yellow')
                # in anycase, raise the error again.
                raise E

    # Loop.save: Called recursively when Protocol.save is called. Returns information necessary to reconstruct loop to calling object.
    #   Inputs:
    #       None
    #   Outputs:
    #       savedLoop - A list of information necessary to reconstruct the loop to be saved in a JSON file.
    def save(self):
        savedLoop = super(Loop, self).save()
        print(type(self.stepImplementation))
        if hasattr(self.stepImplementation, '__iter__'): # if more than one step can be used in the protocol (self.stepImplementation is an iterable)
            stepImp = [s.__name__ for s in self.stepImplementation]
            savedLoop = ["Loop", stepImp, self.iterations.get()] + savedLoop
        else: #Otherwise only one steptype is used in a protocol
            savedLoop = ["Loop", self.stepImplementation.__name__, self.iterations.get()] + savedLoop
        return savedLoop

    # Called recursively when Protocol.loadProtocol is called. Reconstructs loop saved by Loop.save
    #   Inputs:
    #       savedLoop - list of information to reconstruct saved loop object, generated by Loop.saved and retrieved from
    #           a JSON file.
    #   Outputs:
    #       None
    def load(self, savedLoop):
        stepImp = savedLoop[0]
        self.stepImplementation = []
        if type(stepImp) == list:
            for s in stepImp:
                self.checkIfHasIllegalCharacters(s)
                self.stepImplementation.append(eval(s))
        else:
            self.checkIfHasIllegalCharacters(stepImp)
            self.stepImplementation = eval(stepImp)
        self.iterations.insert(0,savedLoop[1])
        self.iterations.saved = savedLoop[1]
        super(Loop, self).load(savedLoop[2:])


    # Loop.run - executes the loop
    # Inputs:
    #   iter - a tuple containing the current iteration values of outer loops. The current loop is at bin 0, the first
    #       outer Loop is at bin 1, ect.
    # Outputs:
    #       Returns "Error" if there is an error while running. This propogates up through the recursive structure to
    #       cancel the run.
    def run(self, iter = None):
        Loop.activeLoop = self #this marker allows steps to clean up iteration counter if the protocol is canceled
        for i in range(1,self.saveIter+1):
            self.currIter.config(text= "Iteration: " + str(i))
            if not iter:
                iter0 = (i,)

            else:
                iter0 = (i,) + iter
            if super(Loop, self).run(iter = iter0) == "Error": #run through one iteration of the loop
                return "Error"
        self.currIter.config(text="")
        Loop.activeLoop = None

# RoutineThread: class to run protocols in their own thread. This allows the program to run a protocl and manage the GUI at the same time
class RoutineThread(Thread):
    protocolRunning = False
    # RoutineThread.__init__
    #   Inputs:
    #       pRun - function or method to call for run, passed by calling routine object
    #       _routineObject - reference to the calling routine Object to call its run method (see above)
    #       mainthread - reference to the main thread; in the case that the user cancels this protocol, the main thread
    #                   will send this a flag. Step objects check for flags in their run method. If they find one, they
    #                   call join on mainthread to end the routinethread.
    #       button - a boolean: true if the protocol is inside a custom button, false if in editable protocol panel.
    #   Outputs:
    #       None
    def __init__(self, pRun, _routineObject, mainthread, button = False): #, name = None):
        if RoutineThread.protocolRunning:
            raise Exception("There is already a protocol running! Please either wait for it to finish or cancel it before running another protocol.")
        else:
            RoutineThread.protocolRunning = True
        Thread.__init__(self)
        self.routineObject = _routineObject
        self.pRun = pRun
        self.setDaemon(True)
        self.event = threading.Event()
        self.mainthread = mainthread
        Step.event = self.event
        Step.mainthread = self.mainthread
        Loop.mainthread = self.mainthread
        self.button = button

    # RoutineThread.run: Start a RoutineThread
    #   Inputs: None
    #   Outputs: None
    def run(self):
        try:
            self.pRun(self.routineObject)
            print("Running")
        except E:
            print("Run Except:")
            print(E.message)
        finally:
            print("Finally")
            config.stopEditing = False
            RoutineThread.protocolRunning = False
            try:
                self.routineObject.runbtn.config(bg='SystemButtonFace', text = self.routineObject.name)
            except:
                self.routineObject.runbtn.config(bg='gray', text=self.routineObject.name)
            self.routineObject.running = False

# ProtocolButtonPanel: User interface for loading saved protocols as custom buttons. Users can load single buttons, save
#                       Panels of buttons, and load panels of buttons.
class ProtocolButtonPanel:

    #ProtocolButtonPanel.__init__
    #   Input:
    #       master - Tkinter frame to place ProtocolButtonPanel
    #   Output:
    #       None
    def __init__(self, master):
        self.mainframe = LabelFrame(master, text = "Custom Buttons")
        self.customButtonFrame = LabelFrame(self.mainframe)

        self.buttons = [] #list of references to buttons
        self.protocols = [] #corresponding list of references to protocols
        self.master = master

    #ProtocolButtonPanel.draw: draws ProtocolButtonPanel
    #   Inputs:
    #       row - row of master Tkinter frame in which to draw ProtocolButtonPanel
    #       col - column of master Tkinter frame in which to draw ProtocolButtonPanel
    #   Outputs:
    #       None
    def draw(self, row, col):
        self.controlButtons = LabelFrame(self.mainframe)
        Button(self.controlButtons, text="Load Buttons", command=self.load).pack(side=LEFT)
        Button(self.controlButtons, text="Save Panel", command=self.saveButtonPanel).pack(side = LEFT)
        self.customButtonFrame.pack()
        self.controlButtons.pack()
        self.mainframe.grid(row = row, column = col, sticky = W)

    #ProtocolButtonPanel.load: load a saved protocol as a button- called by load button.
    #   Inputs:
    #       None
    #   Outputs:
    #       None
    def load(self):
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.mainframe, "Error", "You cannot load new buttons while a protocol is running. "
                    "Please either wait until the protocol finishes or stop it before loading a protocol.")
            return
        with tkFileDialog.askopenfile() as file:
            name = file.name
            try:
                name = file.name[name.rfind("/")+1:name.rfind(".")]
                saveFile = json.load(file)
            except Exception as E:
                tkMessageBox.showerror("Error", E.message)
                return
            if saveFile[0] == "This is a saved Protocol":
                saveFile.pop(0)
                self.addButton(saveFile, name)
            elif saveFile[0] == "This is a saved Button Panel":
                saveFile.pop(0)
                for button in saveFile:
                    name = button.pop(0)
                    self.addButton(button, name)

            else:
                tkMessageBox.showerror("Error","Error: This file is not a saved Protocol")

    # ProtocolButtonPanel.addButton: helper function to load- adds button that calls loaded protocol
    #   Inputs:
    #       Proc - JSON decoded list object specifying saved protocol
    #       name - name of button to be displayed in button.
    #   Outputs:
    #       None
    def addButton(self, Proc, name):
        newproc = Protocol(self.master, writable=False)
        newproc.setName(name)
        newproc.load(Proc)
        newButton = Button(self.customButtonFrame, text = name, command = newproc.run)
        newproc.runbtn = newButton
        for button in self.buttons:
            button.grid_remove()
        self.buttons.append(newButton)
        self.protocols.append(newproc)
        for i, button in enumerate(self.buttons):
            button.grid(row = i/5, column = i%5)

    # ProtocolButtonPanel.grid_remove: removes frame containing button panel from its master frame.
    #   Inputs:
    #       None
    #   Outputs:
    #       None
    #def grid_remove(self):
    #    self.mainframe.grid_remove()

    #ProtocolButtonPanel.saveButtonPanel - obtains JSON encodable list objects for each protocol in panel, and saves
    #                                       it as a JSON text file.
    #   Inputs:
    #       None
    #   Outputs:
    #       None
    def saveButtonPanel(self):
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.mainframe, "Error", "You cannot save your button panel while a protocol is running. "
                    "Please either wait until the protocol finishes or stop it before saving.")
            return
        if self.protocols == []:
            tkMessageBox.showerror("Error", "You have not loaded any buttons into your button panel. There is nothing to save!")
            return
        savelist = ["This is a saved Button Panel"]
        for prot in self.protocols:
            protocolList = Routine.save(prot) #using protocol.save would save a protocol file; we want a list to put into a button panel file.
            protocolList.insert(0, prot.name)  # This will help us deterimine whether loaded objects are infact saved protocols
            savelist.append(protocolList)
        with tkFileDialog.asksaveasfile(mode = 'w', title="Save Routine", defaultextension='.txt') as file:
            json.dump(savelist, file)
