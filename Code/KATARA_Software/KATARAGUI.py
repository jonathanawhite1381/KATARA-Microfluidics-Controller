# This code was written by Jonathan A White, a member of the Streets Lab at the University of California, Berkeley,
# and is licensed under the MIT license.


from ValveController import ValveController, perstalticPump
from KATARAValveController import KATARAValveController
from USB_GUI import *
from Protocol_Tools import *
from Step import Step
from StepDerivatives import ValveStep # passes dictionary of available valves to ValveStep object
from threading import Timer
from no_wait_Dialog import no_wait_Dialog


# KATARAGUI: the main class for the KATARA microfluidics controller GUI. Inherits from usbGUI which implements a shared
# framework with the companion thermocycling GUI.
class KATARAGUI(usbGUI):
    btndict = {} #make dictionary of buttons a class data member so it is accessible from any scope of the program and other objects can color buttons.
    pumpGUIsAcross = 3

    # KATARAGUI.__init__
    #   Inputs:
    #       master - Tk object (created by calling Tk() from Tkinter package)
    #   Outputs:
    #       None
    def __init__(self, master):
        self.setDeviceType()
        usbGUI.__init__(self, master)
        master.wm_title("KATARA")
        self.canvas.config(width = 460, height = 550)
        self.canvas.xview_moveto('0.0')
        self.canvas.yview_moveto('0.0')
        self.canvas.config(offset = '100,100')

        #create manual valve control button panel]
        self.drawButtonPanelDim()

        #create interface to specify pump modules
        self.pumpBar = LabelFrame(self.mainframe, text = "Add Pump Module")
        self.pumpBar.grid(column = 0, row = 2, sticky = W)
        self.pumpName = LabelEntry(self.pumpBar, 0, 0, "Name: ")

        valves = LabelFrame(self.pumpBar)
        valves.grid(column = 0, row = 1, sticky = W, columnspan = 6)
        self.valveEntries = []
        for valve in (1,2,3):
            self.valveEntries.append(LabelEntry(valves, 0, 2*valve -2, " --> Valve " + str(valve) + ": ", width = 5))

        self.addPumpBtn = Button(self.pumpBar, text = "Add", command = self.addPump)
        self.addPumpBtn.grid(column  = 2, row = 0, sticky = W)

        # if the new window button is checked, the control interface for new pumps will open in a new window. Otherwise,
        # the control interface will go below the pump bar.
        self.newWin = IntVar()
        Checkbutton(self.pumpBar, variable = self.newWin, text="New Window").grid(row = 0, column = 3)

        #frame to place in window pump GUIs
        self.pumpGUIs = LabelFrame(self.mainframe, text = "Pump Interfaces")
        self.pumpGUIs.grid(column = 0, row = 3, sticky = W)
        self.windowPumps = []


        #add protocol box
        self.ProtocolBox(4, 0, (PumpStep, ValveStep, PauseStep))
        Step.btndict = self.btndict
        self.mainframe.bind("<<connection_warning>>", self.warning)
        self.mainframe.bind("<<disconnected_error>>", self.disconnected)
        Protocol.holdErrorMessage = "You cannot start a protocol while a pump is running." #message to give user
        #when Protocol.holdFlag==True, for this program, while a pump is running.
        ArduinoErrorProofedRoutine.vGUI = self

    # KATARAGUI.setDeviceType - Set the Driver for communicating with the valve controlling device. Overwrite
    # if using a device other than an Arduino running KATARA firmware.
    #   Input: None
    #   Output: None
    def setDeviceType(self):
        self.devicetype = KATARAValveController

    #redefine protocol box after overiding Protocol with the Arduino Proofed (enhanced error handling) version.
    # KATARAGUI.ProtocolBox: Set up interface for editing, loading, saving, and running protocols.
    #   Inputs:
    #       row - row in the main window to add the protocol interfaces
    #       column - the column in the main window to add the protocol interface
    #       stepImplementation - tuple of the different kinds of steps (string) that the user could add, or if only one kind of
    #           is available, the kind of step that the user can add (string)
    #   Outputs: None
    def ProtocolBox(self, row, col, stepImplementation):
        self.customProtocolPanel = ProtocolButtonPanel(self.mainframe)
        self.customProtocolPanel.draw(row, col)
        self.Protocol = Protocol(self.mainframe)
        self.Protocol.setStepImplementation(stepImplementation)
        self.stepImplementation = stepImplementation
        self.Protocol.drawProtocol(row + 1, col)
        if type(stepImplementation) == type(
                Step):
            self.Protocol.addStep(1)

    # KATARAGUI.drawButtonPanel - draws a rectangular array of buttons
    # Inputs:
    #       buttonsAcross - The number of columns to draw in the button array
    #       buttonsDown - The number of rows to draw in the button array.
    # Outputs: None
    def drawButtonPanel(self, buttonsAcross, buttonsDown):
        self.buttons_down = buttonsDown
        self.buttons_across = buttonsAcross
        self.btn = [[0 for x in range(self.buttons_down)] for x in range(self.buttons_across)]
        self.btnPanel = LabelFrame(self.mainframe)
        self.btnPanel.grid(column=0, row=1, sticky=W)
        KATARAGUI.btndict["AvailablePinsStatement"] = "integer numbers 2-69"# to show in error messages where user enters
        # invalid pin number

        for y in range(self.buttons_down):
            for x in range(self.buttons_across):
                pin_num = self.coordToPin(x, y)
                if self.maxPinCondition(pin_num):
                    break
                self.btn[x][y] = Button(
                    self.btnPanel, text=str(pin_num), bg="gray", width=5, height=2,
                    command=lambda x1=x, y2=y: self.toggle(x1, y2)
                )
                KATARAGUI.btndict[pin_num] = self.btn[x][y]
                self.btn[x][y].grid(column=x, row=y, sticky=W)

    # KATARAGUI.drawButtonPanelDim: Draw button panel with specified dimensions, buttons_accros by buttons_down.
    # Override for set ups that use fewer than 68 buttons
    # Inputs: None
    # Outpus: None
    def drawButtonPanelDim(self):
        buttons_across = 12
        buttons_down = 6
        self.drawButtonPanel(buttons_across, buttons_down)

    # KATARA GUI.maxPinCondition: Since the number of buttons you want to draw will not always fit in a neat
    # rectangle, this method checks if buttons for all available pins have been drawn so far in the grid.
    # Override if using a set up with fewer than 68 buttons.
    # Inputs:
    #       pin_num - an integer pin number that is about to be drawn
    # Output:
    #       boolean true if pin_num is greater than the maximum designated pin, false if within bounds.
    def maxPinCondition(self, pin_num):
        return pin_num > 69

    # KATARAGUI.coordToPIn : used to convert location of button in grid to Arduino pin number it corresponds to
    # Inputs:
    #       col - the column that the button is in
    #       row - the row that the button is in
    # Output:
    #       the Arduino pin number of the button in col, row
    def coordToPin(self, col, row):  # convert position in button array to pin number
        #  digital pins 0 and 1 are used in USB communication,
        #  digital pins 0 and 1 are used in USB communication,
        # so the GUI cannot use these pins for
        # valve control. To use them,  you must program the arduino to control valves autonomously.
        return row * self.buttons_across + col + 2

    # KATARAGUI.connect # connects to an Arduino loaded with the KATARA Arduino Firmware- overides base method.
    # Inputs:
    #       port - The com port to which the arduino is attached
    # Outputs: None
    def connect(self, port):
        reset = False
        if self.device and self.device.isOpen():
            reset = True

        if pumpGUI.runningPump:
            tkMessageBox.showerror("Error", "You cannot reconnect while a pump is running.")
            raise Exception("You cannot reconnect while a pump is running.")

        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot reconnect while a protocol is running.")
            return

        usbGUI.connect(self, port)
        ValveStep.setValves = self.device.setPins
        PumpStep.specifyPump = self.device.specifyPump
        PumpStep.ctlr = self.device
        if reset:
            for btn in self.btndict:
                self.btndict[btn].config(bg = 'gray')
            for pump in ValveController.pPumps:
                pump.ctlr = self.device

    # KATARAGUI.toggle: accepts location of pin toggle button in grid, toggles button color and pin High/low. This
    # is attached to button objects in KATARAGUI.drawButtonPanel
    # Inputs:
    #       col - the column in which the calling button has been placed in the button panel
    #       row - the row in which the calling button has been placed in the button panel
    # Output: None
    def toggle(self, col, row):
        pin = self.coordToPin(col, row)
        if not self.device or not self.device.isOpen():
            tkMessageBox.showerror("Error", "Not connected to arduino")
            return
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot manually control valves while running a protocol.")
            return

        #turn off any running pumps
        pumpsRunning = False
        if pumpGUI.runningPump:
            try:
                pumpGUI.runningPump.offtimer.cancel()
            except: #the timer expired between if statement and cancel call
                pass
            finally:
                pumpGUI.runningPump.pump.stop()
                pumpGUI.runningPump.pumpOff()
                pumpsRunning = True
        try:
            pinHigh = self.device._togglePin(pin)
        except Warning as W:
            tkMessageBox.showerror("Warning", W.message)
            for pGUI in pumpGUI.instances:
                valves = pGUI.pump.valves
                pGUI.pump = self.device.specifyPump(int(valves[0]), int(valves[1]), int(valves[2]))
            pinHigh = self.device.pinStates[pin]
        except IOError as E:
            tkMessageBox.showerror("Error", E.message)
            return
        except Exception as E:
            print(E.message)
            tkMessageBox.showerror("Error", E.message)
            return

        if pinHigh or pumpsRunning:
            self.btn[col][row].config(bg="green")
        else:  # valve open and green, toggle to closed and gray
            self.btn[col][row].config(bg="gray")

    #KATARAGUI.addPump: Add (draw) a pump control module to the KATARAGUI pump panel
    # Inputs: None
    # Outputs: None
    def addPump(self):
        if not self.device or not self.device.isOpen():
            tkMessageBox.showerror("Error", "Not connected to arduino.")
            return
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot add pumps while protocols are running.")
            return
        name = self.pumpName.get()
        try:
            valves = []
            for v in self.valveEntries:
                vn = int(v.get())
                self.device._checkPin(vn)
                valves.append(vn)

            if len(set(valves)) < 3: #if user entered the same valve more than once
                tkMessageBox.showerror("Error", "Please enter three different valve numbers to specify the pump.")
                return
            #if there were an error, it would have been raised by now, so now we can mark each valve as added to a pump.
            # we will not do t his if we are opening the pump GUI in the new window, because they are destroyed when closed

            try:

                pump = pumpGUI(valves[0],valves[1],valves[2],self.device, name, winPump=self.newWin.get(), master = self.master)

            except Exception as E:
                tkMessageBox.showerror("Error", E.message)
                return
            if self.newWin.get():
                pump.draw()
            else:
                nPumps = len(pumpGUI.panelPumps[:-1])
                for i, p in enumerate(pumpGUI.panelPumps[:-1]):
                    p.redraw(i)
                pump.draw(master = self.pumpGUIs, _row=nPumps / KATARAGUI.pumpGUIsAcross, _column=nPumps % KATARAGUI.pumpGUIsAcross)

        except ValueError or TypeError: #if entered pin is not between 2 and 69
            tkMessageBox.showerror("Error", "Please enter integer pin numbers between 2-69.")
        except Exception as E:
            tkMessageBox.showerror("Error", E.message)

    # KATARAGUI.disconnected: called if an <<disconnected_error>> Tkinter event is generated during a protocol run (bound in line 65)
    # Inputs:
    #       tokenArgument - accepted because the Tkinter error catching system wants to pass an argument
    # Outputs: None
    def disconnected(self, tokenArgument=None):
        tkMessageBox.showerror("Error", "The connection with the arduino was lost and the protocol was terminated.")

    # KATARAGUI.warning: called if an <<connection_warning>> Tkinter event is generated during a protocol run (bound in line 64)
    # Inputs:
    #       tokenArgument - accepted because the Tkinter error catching system wants to pass an argument
    # Outputs: None
    def warning(self, tokenArgument=None):
        no_wait_Dialog("Warning", "There was a problem in the connection. "
                                      "The connection has been reset and the valve states have been restored.")

#this class implements pump controlling GUI modules
class pumpGUI:
    names = []
    instances = []
    panelPumps = []  # keep track of references to pumps displayed in main window. Pumps displayed in new windows
    runningPump = None

    # pumpGUI.__init__: Initializes a pump interface.
    # Inputs:
    #       _v1 - The first valve in the peristaltic pump
    #       _v2 - The second valve in the peristaltic pump
    #       _v3 - The third valve in the peristaltic pump
    #       _ctlr - a reference the KATARAValveController object (which sends usb commands to the Arduino)
    #       name - the name of the pump to be displayed at the top of the interface
    #       winPump - optional boolean, If true opens interface in a new window, if false, adds interface in the main
    #           KATARA GUI's pump panel.
    #       master - the parent Tkinter frame. This argument is ommitted if the interface is opened in a new window.
    def __init__(self, _v1, _v2, _v3, _ctlr, name, winPump = False, master = None):
        self.master = master
        if name in self.names:
            raise NameError("There is already a pump named " + name + ".")
        self.name = name
        self.running = False

        # Keep track of all pumpGUI objects created.
        pumpGUI.names.append(name)
        pumpGUI.instances.append(self)

        self.ctlr = _ctlr
        self.pump = self.ctlr.specifyPump(_v1, _v2, _v3) #reference to peristalsic pump object
        self.winPump=winPump
        if not winPump:
            pumpGUI.panelPumps.append(self)


        self.pumpFrame = None # this is filled in pumpGUI.draw



    # pumpGUI.draw: draws the pumpGUI, parameters are necessary if drawing in main GUI, ommitted if drawn in own window
    #  Inputs:
    #       master - Parent Tkinter Frame
    #       _row - the row of the parent Tkinter frame in which to place the pump interface
    #       _col - the column of the parent Tkinter frame in which to place the pump interface
    # Outputs: None
    def draw(self, master = None, _row = None, _column = None):
        # if the "open new window" pFrame is checked, open a window with pump GUI
        if self.winPump:
            self.npump = Toplevel(self.master) #
            self.npump.wm_title(self.name)
            self.npump.minsize(width = 200, height = 95)
            self.pumpFrame = Frame(self.npump)
            self.pumpFrame.pack()
            self.npump.protocol("WM_DELETE_WINDOW", self.remove)
        else:
            self.pumpGUIs = master #pumpGUIs is a reference to the label frame that holds all of the pump GUIs
            self.pumpFrame = LabelFrame(master)
            self.pumpFrame.grid(row = _row, column = _column, sticky = W)

        Name = LabelFrame(self.pumpFrame, bg = "gray")
        Name.grid(row=0, column = 0, sticky = W)
        NameLabel = Label(Name, text = self.name)
        NameLabel.grid(row=0, column=0, sticky=W)
        self.rate = LabelEntry(self.pumpFrame, 1,0, "Rate (cycles/s):", width = 10)
        self.cycles = LabelEntry(self.pumpFrame, 2,0,"Number of Cycles:", width = 10)
        self.reverse = IntVar()
        self.reverseBtn = Checkbutton(self.pumpFrame, variable = self.reverse, text = "Reverse")
        self.reverseBtn.grid(row = 0, column=1, sticky = W)
        self.startButton = Button(self.pumpFrame, text = "Start", command = self.start, bg = "green")
        self.startButton.grid(row = 3, column = 1, sticky = "E")
        self.deleteBtn = Button(self.pumpFrame, text = "Delete", command=self.remove).grid(row=3, column=0, sticky= W)


    # pumpGUI.start: run the pump with the peristalsic pump object which does all of the parameter checking. If the pump
    # is already running, stop it. GUI related case checking happens here.
    # Inputs: None
    # Outputs: None
    def start(self):
        if not self.pump.ctlr.isOpen():
            tkMessageBox.showerror("Error","Not connected to arduino.")
            print("nconnected")
            return
        if RoutineThread.protocolRunning:
            no_wait_Dialog(self.master, "Error", "You cannot manually start pumps while running a protocol.")
            return
        if pumpGUI.runningPump:
            runningPump = pumpGUI.runningPump
            try:
                runningPump.offtimer.cancel()
            except: #either timer ended, or was an infinite running pump
                pass
            finally:
                runningPump.pump.stop()
                runningPump.pumpOff()
                if runningPump is self:
                    return
        try:
            if self.reverse.get():
                self.pump.reverse(int(self.rate.get()), int(self.cycles.get()))
            else: #forward
                self.pump.forward(int(self.rate.get()), int(self.cycles.get()))
        except Warning as W: #This case might happen if the connection is disrupted are reset.
            tkMessageBox.showerror("Warning", W.message)
            try:
                if self.reverse.get():
                    self.pump.reverse(int(self.rate.get()), int(self.cycles.get()))
                else:  # forward
                    self.pump.forward(int(self.rate.get()), int(self.cycles.get()))
            except Exception as E:
                tkMessageBox.showerror(E.message)
                return
        except IOError as E:
            print("IOError")
            tkMessageBox.showerror("Error", E.message)
            return
        except Exception as E:
            print("Exception")
            tkMessageBox.showerror("Error", E.message)
            return
        self.running = True
        pumpGUI.runningPump = self
        self.changeValveColor("Blue")
        self.startButton.config(text="Stop",bg="red")
        for v in self.pump.valves:
            self.ctlr.pinStates[v]=0 # The KATARA firmware automatically de-energizes valves after pumping, so this
                    # line this line ensures our accounting be in order after the pump sequence ends.
        Protocol.holdFlag = True
        if self.cycles.get() != "-1":
            self.offtimer = Timer(float(self.cycles.get()) / float(self.rate.get()), self.pumpOff)
            self.offtimer.setDaemon(True)
            self.offtimer.start()

    # pumpGUI.changeValveColor: changes the color of the peristaltic pump member buttons in the toggle button panel.
    #   Input:
    #       color - the color to which to change the toggle buttons.
    #   Output: None
    def changeValveColor(self, color):
        for v in self.pump.valves:
            btn = KATARAGUI.btndict[int(v)]
            btn.config(bg=color)

    # pumpGUI.pumpOff: resets the GUI after a pumping sequence.
    #   Inputs: None
    #   Outputs: None
    def pumpOff(self): #this method doesn't take an arguement, so we can pass it into a timer object
        self.startButton.config(text="Start", bg = "green")
        self.changeValveColor("gray")
        self.running = False
        pumpGUI.runningPump = None
        Protocol.holdFlag = False


    # pumpGUI.remove: Attached to the "Delete" button on a pump interface- allows user to delete a the pump interface.
    #   Input: None
    #   Output: None
    def remove(self):
        if self.running:
            tkMessageBox.showerror("Error", "You can't delete a pump while it is running.")
            return
        pumpGUI.names.remove(self.name)
        pumpGUI.instances.remove(self)
        if not self.winPump:
            pumpGUI.panelPumps.remove(self)
            self.pumpFrame.grid_forget()
            for i, pump in enumerate(pumpGUI.panelPumps):
                pump.redraw(i)
            pass
        else:
            self.npump.destroy()

    # pumpGUI.redraw: When a user adds a pump interface to the KATARAGUI, all existing pump interfaces are redrawn
    #               with this method.
    #   Input:
    #       i - the pump interface index in the list the class list of main window instances: pumpGUI.panelPumps
    #   Output: None
    def redraw(self, i):
        cycles_saved = self.cycles.get()
        rate_saved = self.rate.get()
        reverse_saved = self.reverse.get()
        self.pumpFrame.grid_remove()
        self.draw(master = self.pumpGUIs, _row=(i) / KATARAGUI.pumpGUIsAcross, _column=(i) % KATARAGUI.pumpGUIsAcross)  # pumps arrayed in four column rows
        self.rate.insert(0, rate_saved)
        self.cycles.insert(0, cycles_saved)
        if reverse_saved:
            self.reverseBtn.select()



