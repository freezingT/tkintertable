import tkinter as tk
from tkinter import Frame, Button
from tkinter import font
import numpy as np
from functools import partial


class NavigationPanel(Frame):
    def __init__(self, parent, N, nPerPage, command=None):
        Frame.__init__(self, parent)

        # Parameters
        self.__initFonts()
        self._maxNIntermediateButtons = int(10)
        self._idx = -1 # button index, ranging from 0 to _maxNIntermediateButtons-1, init with -1 to trigger change if __changeIdx is called first
        self._page_start = -1 # count of the first page, ranges from 0 to _N-_maxNIntermediateButtons, init with -1 to trigger change if __changeIdx is called first

        self._b_First = None
        self._b_Previous = None
        self._b_Next = None
        self._b_Last = None
        self._interm_buttons = []

        self._command = command

        # Internal data representing the current state
        self._nPerPage = nPerPage
        self.updateN(N)
        return

    def updateN(self, newN):
        newN = max(0, newN) # ensure newN >= 0
        self._nPages = int(max(1, np.ceil(newN/self._nPerPage))) 
        self._N = newN
        self._nIntermButtons = int(max(1, min(self._nPages, self._maxNIntermediateButtons)))
        
        self.updateButtons()
        self.__changeIdx(0)
        
        return

    def updateButtons(self):
        if self._b_First is None:
            self._b_First = Button(self, text="<<", command=partial(self._button_callback, -1))
            self._b_First.pack(side=tk.LEFT)
            
            self._b_Previous = Button(self, text="<", command=partial(self._button_callback, -2))
            self._b_Previous.pack(side=tk.LEFT)

        if len(self._interm_buttons) == 0:
            self._createIntermediateButtons()
        self._hideUnnecessaryIntermediateButtons()

        if self._b_Next is None:
            self._b_Next = Button(self, text=">", command=partial(self._button_callback, -3))
            self._b_Next.pack(side=tk.LEFT)

            self._b_Last = Button(self, text=">>", command=partial(self._button_callback, -4))
            self._b_Last.pack(side=tk.LEFT)
        return

    def getStateData(self):
        prange = self.__computePageRange()
        data = {'page': self._idx, 'range': (self._page_start, self._page_start+self._nIntermButtons), 'page_range': prange}
        return data

    def __initFonts(self):
        self._f_actual = font.nametofont('TkTextFont').actual()
        self._f_normal = font.Font(family=self._f_actual.get('family'), size=self._f_actual.get('size'), underline=False, weight=font.NORMAL)
        self._f_highlight = font.Font(family=self._f_actual.get('family'), size=self._f_actual.get('size'), underline=True, weight=font.NORMAL)
        self._f_selected = font.Font(family=self._f_actual.get('family'), size=self._f_actual.get('size'), underline=False, weight=font.BOLD)

    def __computePageRange(self):
        if self._N <= 0:
            return (0, 0)
        start = self._nPerPage*(self._page_start + self._idx)
        end = min(self._nPerPage*(self._page_start + self._idx + 1), self._N)
        return (start, end)
    
    def __changeIdx(self, newPageIndex):
        changed = False
        newPageStart = int(max(0, min(self._nPages-self._nIntermButtons, newPageIndex - np.floor(self._nIntermButtons/2))))
        newIdx = newPageIndex - newPageStart # newButtonIndex

        if self._idx != newIdx:
            changed = True
            if self._idx >= 0:
                self._interm_buttons[self._idx].configure(font=self._f_normal)
            self._interm_buttons[newIdx].configure(font=self._f_selected)
        if self._page_start != newPageStart:
            changed = True
            for i, elt in enumerate(self._interm_buttons):
                elt.configure(text=str(i+newPageStart+1))

        self._idx = newIdx
        self._page_start = newPageStart
        return changed


    def _button_callback(self, identifier):
        if identifier == -1: # <<
            identifier = 0
        elif identifier == -2: # <
            identifier = max(0, self._page_start + self._idx - 1)
        elif identifier == -3: # >
            identifier = min(self._nPages-1, self._page_start + self._idx + 1)
        elif identifier == -4: # >>
            identifier = self._nPages-1
        elif identifier >= 0:
            identifier = self._page_start + identifier
        identifier = int(identifier)

        isChanged = self.__changeIdx(identifier)
        if isChanged:
            if self._command is not None:
                self._command()

    def _button_callback_mouse_enter(self, data):
        pass
    def _button_callback_mouse_leave(self, data):
        pass

    def _createIntermediateButtons(self):
        for i in range(self._maxNIntermediateButtons):
            button = Button(self, text=str(i+1), font=self._f_normal, command=partial(self._button_callback, i))
            if i==0:
                button.configure(font=self._f_selected)
            button.bind("<Enter>", self._button_callback_mouse_enter)
            button.bind("<Leave>", self._button_callback_mouse_leave)
            button.pack(side=tk.LEFT)
            self._interm_buttons.append(button)
            i += 1
        self._idx = 0
        self._page_start = 0

    def _hideUnnecessaryIntermediateButtons(self):
        if self._b_Last is not None:
            self._b_Last.pack_forget()
            self._b_Next.pack_forget()

        for i in range(self._nIntermButtons, self._maxNIntermediateButtons):
            self._interm_buttons[i].pack_forget()

        for i in range(1, self._nIntermButtons):
            #self._interm_buttons[i].configure(text=str(i+self._page_start+1))
            if not self._interm_buttons[i].winfo_ismapped():
                self._interm_buttons[i].pack(side=tk.LEFT)

        if self._b_Last is not None:
            self._b_Next.pack(side=tk.LEFT)
            self._b_Last.pack(side=tk.LEFT)
        return
    
