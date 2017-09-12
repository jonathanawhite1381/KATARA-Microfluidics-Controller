# This code was written by Jonathan A White, a member of the Streets Lab at the University of California, Berkeley,
# and is licensed under the MIT license.

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