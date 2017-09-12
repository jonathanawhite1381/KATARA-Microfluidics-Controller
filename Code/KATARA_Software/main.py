# This code was written by Jonathan A White, a member of the Streets Lab at the University of California, Berkeley,
# and is licensed under the MIT license.


from KATARAGUI import KATARAGUI
try:
    from Tkinter import Tk  #python 2.7
except:
    from tkinter import Tk  #python 3
import config
try:
    import tkMessageBox
except:
    from tkinter import messagebox
    tkMessageBox = messagebox
from no_wait_Dialog import no_wait_Dialog

def disconnected(input=None):
    tkMessageBox.showerror("Error", "The protocol failed; check your connection to the Arduino.")

def warning(input=None):
    no_wait_Dialog("Warning", "There was a problem in the connection. "
                              "The connection has been reset and the valve states have been restored.")

root = Tk()
try:
    root.iconbitmap('KATARA.ico')
except:
    pass
config.root = root
root.bind_all("<<connection_warning>>", warning)
root.bind_all("<<disconnected_error>>", disconnected)
app = KATARAGUI(root)
root.mainloop()
