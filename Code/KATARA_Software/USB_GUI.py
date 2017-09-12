# This code was written by Jonathan A White, a member of the Streets Lab at the University of California, Berkeley,
# and is licensed under the MIT license.

try:
    from Tkinter import * # python 2.7
    import Tkinter
except:
    from tkinter import * #python 3
    import tkinter
from Protocol_Tools import *
from Step import Step
from LabelEntry import LabelEntry
import serial
from serial.tools import list_ports


#Serves as a base class for GUIs connecting USB devices.
class usbGUI:

    #usbGUI.__init__: intializes the usbGUI.
    #   Input:
    #       master - Tk object returned by calling Tk() in the main file.
    #   Output: None
    def __init__(self, master):

        #create a canvas on which to put the mainframe so we can have a scroll bar (only canvases support scrollbars)
        self.canvas = Canvas(master, borderwidth = 0)
        self.vertScrollBar = Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vertScrollBar.set)

        self.vertScrollBar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)


        self.mainframe = Frame(self.canvas) #save reference to window
        self.master = master

        self.canvas.create_window((5, 5), window=self.mainframe, anchor="nw", tags="self.mainframe")
        #Routine.canvas = self.canvas #give the Procedure class a reference to canvas so that it can change the window size when
        # adding/removing buttons.
        Routine.frame = self.mainframe


        self.mainframe.bind("<Configure>", self.onFrameConfigure) # Call usbGUI.onFrameConfigure whenever a <Configure>
        #event is generated, eg created, something is changed inside window like adding or deleting a step.


        #Initialize the menu bar and connect menu.
        self.menubar = Menu(master)
        #self.menubar.config(bg ='red')
        self.connectmenu = Menu(self.menubar, tearoff=0)
        self.connectmenu.config(postcommand = self.resetConnectMenu)
        self.populateConnectMenu()
        self.menubar.add_cascade(label="Connect", menu=self.connectmenu)

        master.config(menu=self.menubar)

        self.device = None #not yet initialized

    # usbGUI.resetConnectMenu: Called when the user clicks on the "Connect" dropdown menu- checks what USB devices are
    #   connected and updates the dropdown menu to list those devices.
    # Inputs: None
    # Outputs: None
    def resetConnectMenu(self):
        # First, delete currently listed devices
        nCommands = len(self.connectmenu._tclCommands)
        self.connectmenu.delete(0, nCommands)
        #Now check devices and then add them.
        self.populateConnectMenu()


    # usbGUI.populateConnectMenu: Checks what usb devices are connected to the computer and adds them to a list to be
    #   shown in the connect dropdown menu
    # Inputs: None
    # Outputs: None
    def populateConnectMenu(self):
        ports = [port for port in serial.tools.list_ports.comports() if port[2] != 'n/a']
        for port in ports:
            self.connectmenu.add_command(label=port[1], command=lambda prt=port[0]: self.connect(prt))

    # usbGUI.onFrameConfigure: called whenever a '<Configure>' event is generated (see binding in constructor). This
    # happens when something changes in the window, for example, when a step is added. This method adjuts the frame size
    # and depending on the size of the window contents on configure, and adds a scroll bar if the size exceeds the
    # screensize.
    #   Inputs:
    #       event - passed by Tkinter binding code to call when '<Configure>' events are generated.
    #   Outputs: None
    def onFrameConfigure(self, event):
        if event.width < self.master.winfo_screenwidth()- 200:
            self.canvas.configure(width = event.width)
        elif self.canvas.cget('width') < self.master.winfo_screenwidth()-200:
            self.canvas.configure(width = self.master.winfo_screenwidth()-200)

        if event.height < self.master.winfo_screenheight() - 200:
            self.canvas.configure(height = event.height)
        elif self.canvas.cget('height') < self.master.winfo_screenheight() -200:
            self.canvas.configure(self.master.winfo_screenheight() -200)

        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # usbGUI.connect: Called by list items in the connect dropdown menu: tries to connect to the corresponding usb
    # device.
    # Inputs:
    #       port - the string name of the port which we are trying to connect to.
    def connect(self, port):
        if not self.device: #not yet initialized:
            pass
        elif self.device.isOpen():
            if tkMessageBox.askyesno("Disconnect?", "You have already connected to an "+self.device.deviceType+" valve controller."
                                        " Would you like to try connecting to port " +port+"?"
                                        " Establishing a new connection to the Arduino will reset its valves states."):
                self.device.close()
            else:
                return
        try:
            self.device = self.devicetype(port) #define device type in derived class constructor before calling base constructor
            Routine.connected = True
        except Exception as E:
            tkMessageBox.showerror("Error", E.message)
            #self.openErrorWindow("Error: Could not connect. Make sure that the correct Com port "
            #"is selected, another program is not using it, and that the device is on."
            #)
            raise Exception(E.message)#"Could not connect. Make sure that the right Com port is selected and that another program is not using it")

    # usbGUI.ProtocolBox: Draws the Protocol Box
    # Inputs:
    #       row - the row of the parent frame in which to place the protocol box
    #       col - the column of the parent frame in which to place the protocol box
    #       stepImplementation - Step object or list of step objects that the user can add to their protocol.
    # Outputs: None
    def ProtocolBox(self, row, col, stepImplementation):
        self.customProtocolPanel = ProtocolButtonPanel(self.mainframe)
        self.customProtocolPanel.draw(row, col)
        self.Protocol = Protocol(self.mainframe)
        self.Protocol.setStepImplementation(stepImplementation)
        self.stepImplementation = stepImplementation
        self.Protocol.drawProtocol(row+1, col)
        if type(stepImplementation) == type(Step): # classobj: #(stepImplementation) != tuple and type(stepImplementation) != set and type(stepImplementation) != list:
            self.Protocol.addStep(1)

    # usbGUI.destroy: destroys the serial object closing the usb Connection when the GUI window is closed and the
    # program is terminated
    # Inputs: None
    # Outputs: None
    def destroy(self): #cleans up at window close
        try:
            self.device.destroy()
        except E:
            tkMessageBox.showerror(E.message)
            pass