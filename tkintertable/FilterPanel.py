#!/usr/bin/env python
"""
    Module implements a panel for Table filtering functionality.
    Created Feb 2025
    The code is based on the code by Damien Farrell in the Filtering.py file.

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from __future__ import absolute_import, division, print_function

try:
    import tkinter as tk
    from tkinter import StringVar, IntVar
except:
    import Tkinter as tk
    from Tkinter import StringVar, IntVar

try:
    from customtkinter import CTkFrame as Frame
    from customtkinter import CTkButton as Button
    from customtkinter import CTkLabel as Label
    from customtkinter import CTkComboBox as Combobox
    from customtkinter import CTkEntry as Entry
    from customtkinter import CTkScrollableFrame
    #from tkinter import *
    from tkinter import filedialog, messagebox, simpledialog
except:
    Frame = tk.Frame
    Button = tk.Button
    Label = tk.Label
    Combobox = tk.ttk.Combobox
    Entry = tk.Entry
    CTkScrollableFrame = tk.Frame # this is not scrollable!


try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from types import *
from cellcontentoperators import *



def doFiltering(searchfunc, filters=None):
    """Module level method. Filter recs by several filters using a user provided
       search function.
       filters is a list of tuples of the form (key,value,operator,bool)
       returns: found record keys"""

    if filters == None:
        return
    F = filters
    sets = []
    for f in F:
        col, val, op, boolean = f
        names = searchfunc(col, val, op)
        sets.append((set(names), boolean))
    names = sets[0][0]
    for s in sets[1:]:
        b=s[1]
        if b == 'AND':
            names = names & s[0]
        elif b == 'OR':
            names = names | s[0]
        elif b == 'NOT':
            names = names - s[0]
        #print len(names)
    names = list(names)
    return names

def getOperators(fieldtype: str) -> list[str]:
    lst = []
    if fieldtype == "text":
        lst = ['contains','excludes','starts with', 'ends with', 'regex']
    elif fieldtype == "number":
        lst = ['=','!=','>','<']
    elif fieldtype == "date":
        lst = ['on', 'before', 'since']
    else:
        pass
    return lst
    

class FilterFrame(Frame):

    def __init__(self, parent, fields, fieldtypes: list[Literal["text", "number", "date"]], callback=None):
        """Create a filtering gui frame.
        Callback must be some method that can accept tuples of filter
        parameters connected by boolean operators """
        Frame.__init__(self, parent)
        self.parent = parent
        self.callback = callback
        self.fields = fields
        self.fieldtypes = fieldtypes
        if len(fields) != len(fieldtypes):
            raise RuntimeError('Number of given fields and number of field types must match.')
        self.filters = []

        #self.columnconfigure(1, weight=2)
        topframe = Frame(self)
        topframe.pack(side=tk.TOP, fill="x", anchor="n")

        gobutton=Button(topframe, text='Go', command=self.callback)
        gobutton.pack(side=tk.LEFT, fill="x", expand=True, padx=2, pady=2)
        #addbutton.grid(row=0,column=0, sticky='news', padx=2, pady=2)

        addbutton=Button(topframe, text='+Add Filter', command=self.addFilterBar)
        addbutton.pack(side=tk.LEFT, fill="x", expand=True, padx=2, pady=2)
        #addbutton.grid(row=0,column=1,sticky='news',padx=2,pady=2)

        self.resultsvar=IntVar()
        foundlabel = Label(topframe, text='Results:')
        foundlabel.pack(side=tk.LEFT, padx=(20,2), pady=2)#.grid(row=0,column=3,sticky='nes')
        numlabel = Label(topframe, textvariable=self.resultsvar)
        numlabel.pack(side=tk.LEFT, padx=2, pady=2)#.grid(row=0,column=4,sticky='nws',padx=2,pady=2)
        
        self.scrollableFrame = CTkScrollableFrame(self, height=100)
        self.scrollableFrame._scrollbar.configure(height=100)
        #self.scrollableFrame.grid(row=1, column=0, sticky='news', padx=2, pady=2, columnspan=4)
        self.scrollableFrame.pack(side=tk.TOP, fill="x", expand=True, padx=2, pady=2, anchor="n")

        self.addPlaceholder()
        return

    def addFilterBar(self):
        """Add filter"""
        index = len(self.filters)
        f = FilterBar(self.scrollableFrame, self, index, self.fields)
        self.filters.append(f)
        f.pack(side="top", padx=2, pady=2, anchor="ne", fill="x", expand=True)
        self.addPlaceholder()        
        return

    def addPlaceholder(self):
        placeholder = FilterBarPlaceholder(self.scrollableFrame, self)
        placeholder.pack(side="top", padx=2, pady=2, anchor="ne", fill="x", expand=True)
        return

    def getFieldType(self, fieldname):
        return self.fieldtypes[self.fields.index(fieldname)]

    def doFiltering(self, searchfunc, trigger_index=-1):
        F=[]
        for f in self.filters:
            if f.isValid():
                F.append(f.getFilter())
        if len(F) == 0:
            F = None

        names = doFiltering(searchfunc, F)
        self.updateResults(len(names))
        return names

    def _triggerFiltering(self, trigger_index=-1):
        F=[]
        for f in self.filters:
            F.append(f.getFilter())

        n = self.callback(F)
        self.updateResults(n)

    def updateResults(self, i):
        self.resultsvar.set(i)
        return

class FilterBarPlaceholder(Frame):
    """Class providing "+"-Button for a new FilterBar"""

    def __init__(self, parent, filterframe):
        Frame.__init__(self, parent)
        self.filterframe = filterframe
        cbutton=Button(self,text='+', command=self.callback, width=25)
        cbutton.pack(side=tk.LEFT)

        label = Label(self, text="Filter")
        label.pack(side=tk.LEFT)

        return

    def callback(self):
        self.close()
        self.filterframe.addFilterBar()
        return
    
    def close(self):
        """Destroy and remove from parent"""
        self.destroy()
        return

class FilterBar(Frame):
    """Class providing filter widgets"""
    booleanops = ['AND','OR','NOT']

    def __init__(self, parent, filterframe, index, fields):
        Frame.__init__(self, parent)
        self.filterframe=filterframe
        self.index = index
        self.filtercol=StringVar()

        self._booleanselected = 'AND'
        self._columnselected = None
        self._operatorselected = None
        self._valueselected = None

        cbutton=Button(self,text='-', command=self.close, width=25)
        #cbutton.grid(row=0,column=5,sticky='news',padx=2,pady=2)
        cbutton.pack(side=tk.LEFT)

        self.booleanop=StringVar()
        self.booleanop.set('AND')
        self._booleanopmenu = Combobox(self,
                variable = self.booleanop,
                values = self.booleanops,
                command=lambda event: self.actioncallback(0, event),
                state="readonly",
                #initialitem = 'AND',
                width = 70)
        #booleanopmenu.grid(row=0,column=0,sticky='news',padx=2,pady=2)
        self._booleanopmenu.pack(side=tk.LEFT)
        #disable the boolean operator if it's the first filter
        #if self.index == 0:
        #    booleanopmenu.component('menubutton').configure(state=DISABLED)

        self._filtercolmenu = Combobox(self,
                #labelpos = 'w',
                #label_text = 'Column:',
                variable = self.filtercol,
                values = fields,
                command=lambda event: self.actioncallback(1, event),
                state="readonly",
                width = 150)
                #initialitem = initial,)
        #filtercolmenu.grid(row=0,column=1,sticky='news',padx=2,pady=2)
        self._filtercolmenu.pack(side=tk.LEFT, expand=False, fill="x")

        self.operator=StringVar()
        self._operatormenu = Combobox(self,
                variable = self.operator,
                values = [],
                command=lambda event: self.actioncallback(2, event),
                state="readonly",
                #initialitem = 'contains',
                width = 100)
        #operatormenu.grid(row=0,column=2,sticky='news',padx=2,pady=2)
        self._operatormenu.pack(side=tk.LEFT)

        self.filtercolvalue=StringVar()
        self._valsbox=Entry(self, textvariable=self.filtercolvalue, width=20)
        #valsbox.grid(row=0,column=3,sticky='news',padx=2,pady=2)
        self._valsbox.pack(side=tk.LEFT, expand=True, fill="x")
        self._valsbox.bind("<Return>", lambda event: self.actioncallback(3, event))
        self._valsbox.bind("<FocusOut>", lambda event: self.actioncallback(3, event))

        return

    #def activate(self):
    #    pass

    def actioncallback(self, id, event):
        changed = False
        if id == 0: # booleanop
            changed = self._booleanselected != self.booleanop.get()
            self._booleanselected = self.booleanop.get()
        elif id == 1: # column
            changed = self._columnselected != self.filtercol.get()
            if changed: 
                old = self._columnselected
                self._columnselected = self.filtercol.get()
                self.switchOperatorSet(oldOperator=old)
        elif id == 2: # operator
            changed = self._operatorselected != self.operator.get()
            self._operatorselected = self.operator.get()
        elif id == 3: # value
            changed = self._valueselected != self.filtercolvalue.get()
            self._valueselected = self.filtercolvalue.get()

        if changed and self.isValid():
            self.filterframe._triggerFiltering(self.index)
    
    def isValid(self):
        return self._columnselected is not None and self._operatorselected is not None and self._valueselected is not None and len(self._valueselected) > 0

    def switchOperatorSet(self, oldOperator=None):
        type = self.filterframe.getFieldType(self._columnselected)
        if oldOperator is not None:
            oldtype = self.filterframe.getFieldType(oldOperator)
            if type == oldtype:
                return
        ops = getOperators(type)
        self._operatormenu.configure(values=ops)
        if len(ops) > 0:
            self.operator.set(ops[0])
            self._operatorselected = self.operator.get()
        else:
            self.operator.set('')
            self._operatorselected = None
        return

    def close(self):
        """Destroy and remove from parent"""
        self.filterframe.filters.remove(self)
        self.destroy()
        return


    def getFilter(self):
        """Get filter values for this instance"""
        col = self.filtercol.get()
        val = self.filtercolvalue.get()
        op = self.operator.get()
        booleanop = self.booleanop.get()
        return col, val, op, booleanop
