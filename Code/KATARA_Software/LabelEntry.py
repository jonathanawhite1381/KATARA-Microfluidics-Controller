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
    from tkinter import * # python 3

#puts a label in the specified grid coordinate of master, and an entry to the right of it. returns reference to entry
class LabelEntry:
    def __init__(self, master, lrow, lcol, txt, width = 10):
        self.lab = Label(master, text = txt)
        self.lab.grid(row = lrow, column = lcol, sticky=W)
        self.Ent = Entry(master, width = width)
        self.Ent.grid(row = lrow, column = lcol +1, sticky=W)
        self.saved = '' #filled by Step saved method

    def grid_forget(self):
        for widget in (self.lab, self.Ent):
            widget.grid_forget()

    def insert(self, l, txt):
        self.Ent.insert(l, txt)

    def get(self):
        return self.Ent.get()