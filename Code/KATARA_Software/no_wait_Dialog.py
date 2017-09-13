try:
    from tkSimpleDialog import * # python 2.7
except:
    from tkinter import simpledialog # python 3
    tkSimpleDialog = simpledialog
    Dialog = simpledialog.Dialog

class no_wait_Dialog(Dialog):
    #the constructor is the same as a normal dialog except wait_window is not called, and a message is accepted
    def __init__(self, parent, title=None, message = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        if message:
            self.message = message

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

        self.initial_focus.focus_set()

    def buttonbox(self):
        # add standard ok button box, no cancel button

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def body(self, master):
        Label(master, text = self.message).pack()
