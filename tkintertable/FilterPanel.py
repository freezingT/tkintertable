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
    from tkinter import StringVar
except ImportError:
    import Tkinter as tk
    from Tkinter import StringVar

try:
    from customtkinter import CTkFrame as Frame
    from customtkinter import CTkButton as Button
    from customtkinter import CTkLabel as Label
    from customtkinter import CTkComboBox as Combobox
    from customtkinter import CTkEntry as Entry
    from customtkinter import CTkScrollableFrame
except ImportError:
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
from .Filtering import TableFilter


def getOperators(fieldtype: str) -> list[str]:
    lst = []
    if fieldtype == "text":
        lst = ['contains',
               'excludes',
               'starts with',
               'ends with',
               'contains (c.ins.)',
               'starts with (c.ins.)',
               'ends with (c.ins.)',
               'regex'
               ]
    elif fieldtype == "number":
        lst = ['=','!=','>','<']
    elif fieldtype == "date":
        lst = ['on', 'before', 'since']
    else:
        pass
    return lst


class FilterPanel(Frame, TableFilter):

    def __init__(self,
                 parent,
                 fields,
                 fieldtypes: list[Literal["text", "number", "date"]]=None,
                 callback=None
                 ):
        """Create a filtering gui frame.
        Callback must be some method that can accept tuples of filter
        parameters connected by boolean operators """
        Frame.__init__(self, parent)
        self.parent = parent
        self.callback = callback
        self.fields = fields
        if fieldtypes is None:
            fieldtypes = ["text"]*len(fields)
        self.fieldtypes = fieldtypes
        if len(fields) != len(fieldtypes):
            raise RuntimeError('Number of given fields and number of field types must match.')
        self.filters = []

        self.filterframe = CTkScrollableFrame(self, height=100)
        self.filterframe._scrollbar.configure(height=100)
        self.filterframe.pack(side=tk.TOP, fill="x", expand=True, padx=2, pady=2, anchor="n")

        self.addFilterBar()
        return

    def addFilterBar(self):
        """Add filter"""
        index = len(self.filters)
        f = FilterBar(self.filterframe, self, index)
        self.filters.append(f)
        f.pack(side="top", padx=2, pady=2, anchor="ne", fill="x", expand=True)
        return

    def getFieldType(self, fieldname):
        return self.fieldtypes[self.fields.index(fieldname)]


    def triggerFiltering(self, trigger_index=-1):
        self.callback(self.doFiltering)
        return

    def getFilterStructure(self):
        filter_structure=[]
        for f in self.filters:
            if f.isValid():
                filter_structure.append(f.getFilter())
        return filter_structure


    def updateResults(self, rownames):
        # do nothing
        return


class FilterBar(Frame):
    """Class providing filter widgets"""
    booleanops = ['AND','OR','NOT']

    def __init__(self, parent, filterframe, index, activated=False):
        Frame.__init__(self, parent)
        self.filterframe = filterframe
        self.index = index

        self._cbutton=Button(self, text='+', command=self.activate, width=25)
        self._cbutton.pack(side=tk.LEFT, padx=2, pady=2)

        self._label = Label(self, text="Add Filter")
        self._label.pack(side=tk.LEFT, padx=(5, 2), pady=2)
        self.activated = False

        # the following attributes are used when the bar is built
        self._booleanselected = None
        self._columnselected = None
        self._operatorselected = None
        self._valueselected = None
        self.booleanop = None
        self._booleanopmenu = None
        self._filtercolmenu = None
        self.operator = None
        self._operatormenu = None
        self.filtercol = None
        self.filtercolvalue = None
        self._valsbox = None

        if activated:
            self.activate()
        return

    def activate(self):
        self._cbutton.configure(text="-", command=self.close)
        self._label.destroy()
        self.buildBar()
        self.filterframe.addFilterBar()
        return


    def buildBar(self):
        self.filtercol=StringVar()

        self._booleanselected = 'AND'
        self._columnselected = None
        self._operatorselected = None
        self._valueselected = None

        self.booleanop=StringVar()
        self.booleanop.set('AND')
        self._booleanopmenu = Combobox(self,
                variable = self.booleanop,
                values = self.booleanops,
                command=lambda event: self.actioncallback(0, event),
                state="readonly",
                width = 70)
        self._booleanopmenu.pack(side=tk.LEFT, padx=2, pady=2)

        self._filtercolmenu = Combobox(self,
                variable = self.filtercol,
                values = self.filterframe.fields,
                command=lambda event: self.actioncallback(1, event),
                state="readonly",
                width = 150)
        self._filtercolmenu.pack(side=tk.LEFT, expand=False, fill="x", padx=2, pady=2)

        self.operator=StringVar()
        self._operatormenu = Combobox(self,
                variable = self.operator,
                values = [],
                command=lambda event: self.actioncallback(2, event),
                state="readonly",
                width = 150)
        self._operatormenu.pack(side=tk.LEFT, padx=2, pady=2)

        self.filtercolvalue=StringVar()
        self._valsbox=Entry(self, textvariable=self.filtercolvalue, width=20)
        self._valsbox.pack(side=tk.LEFT, expand=True, fill="x", padx=2, pady=2)
        self._valsbox.bind("<Return>", lambda event: self.actioncallback(3, event))
        self._valsbox.bind("<FocusOut>", lambda event: self.actioncallback(3, event))
        self.activated = True
        return

    def actioncallback(self, id_, event):
        changed = False
        if id_ == 0: # booleanop
            changed = self._booleanselected != self.booleanop.get()
            self._booleanselected = self.booleanop.get()
        elif id_ == 1: # column
            changed = self._columnselected != self.filtercol.get()
            if changed:
                old = self._columnselected
                self._columnselected = self.filtercol.get()
                self.switchOperatorSet(oldOperator=old)
        elif id_ == 2: # operator
            changed = self._operatorselected != self.operator.get()
            self._operatorselected = self.operator.get()
        elif id_ == 3: # value
            changed = self._valueselected != self.filtercolvalue.get()
            self._valueselected = self.filtercolvalue.get()

        if changed:
            self.filterframe.triggerFiltering(self.index)
        return

    def isValid(self):
        return self.activated and self._columnselected is not None and self._operatorselected is not None and self._valueselected is not None and len(self._valueselected) > 0

    def switchOperatorSet(self, oldOperator=None):
        type_ = self.filterframe.getFieldType(self._columnselected)
        if oldOperator is not None:
            oldtype = self.filterframe.getFieldType(oldOperator)
            if type_ == oldtype:
                return
        ops = getOperators(type_)
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
        self.filterframe.triggerFiltering()
        return


    def getFilter(self):
        """Get filter values for this instance"""
        col = self.filtercol.get()
        val = self.filtercolvalue.get()
        op = self.operator.get()
        booleanop = self.booleanop.get()
        return col, val, op, booleanop
