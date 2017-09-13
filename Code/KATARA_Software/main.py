#MIT License
#
#Copyright (c) 2017 Jonathan A. White
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



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
