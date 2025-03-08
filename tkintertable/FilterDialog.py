#!/usr/bin/env python
"""
    Module implements Table filtering and searching functionality.
    Created Oct 2008
    Copyright (C) Damien Farrell

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
    from tkinter import IntVar, StringVar
    from tkinter.ttk import Frame, Button, Label, Combobox, Entry
except ModuleNotFoundError:
    from Tkinter import IntVar, StringVar
    from ttk import Frame, Button, Label, Combobox, Entry

from tkintertable.Filtering import TableFilter

class FilterDialog(Frame, TableFilter):
    """Toplevel tkinter dialog to provide filtering functionality for a Table object"""

    def __init__(self, parent, fields, callback=None, closecallback=None):
        """Create a filtering gui frame.
        Callback must be some method that can accept tuples of filter
        parameters connected by boolean operators """
        Frame.__init__(self, parent)

        self.parent = parent
        self.closecallback = closecallback
        self.fields = fields
        self.filters = []
        self.addFilterBar()

        addbutton=Button(self,text='Go', command=lambda: callback(self.doFiltering))
        addbutton.grid(row=0,column=0,sticky='news',padx=2,pady=2)
        addbutton=Button(self,text='+Add Filter', command=self.addFilterBar)
        addbutton.grid(row=0,column=1,sticky='news',padx=2,pady=2)
        cbutton=Button(self,text='Close', command=self.close)
        cbutton.grid(row=0,column=2,sticky='news',padx=2,pady=2)
        self.resultsvar=IntVar()
        Label(self,text='found:').grid(row=0,column=3,sticky='nes')
        Label(self,textvariable=self.resultsvar).grid(row=0,column=4,sticky='nws',padx=2,pady=2)
        return

    def addFilterBar(self):
        """Add filter"""
        index = len(self.filters)
        f = FilterBar(self, index, self.fields)
        self.filters.append(f)
        f.grid(row=index+1,column=0,columnspan=5,sticky='news',padx=2,pady=2)
        return

    def close(self):
        """Close frame and do stuff in parent app if needed"""
        self.closecallback()
        self.destroy()
        return

    def getFilterStructure(self):
        filter_structure=[]
        for f in self.filters:
            filter_structure.append(f.getFilter())
        return filter_structure

    def updateResults(self, rownames):
        self.resultsvar.set(len(rownames))
        return

class FilterBar(Frame):
    """Class providing filter widgets"""
    operators = ['contains','excludes','=','!=','>','<','starts with',
                 'ends with','has length','is number']
    booleanops = ['AND','OR','NOT']
    def __init__(self, parent, index, fields):
        Frame.__init__(self, parent)
        self.parent=parent
        self.index = index
        self.filtercol=StringVar()
        filtercolmenu = Combobox(self,
                #labelpos = 'w',
                #label_text = 'Column:',
                textvariable = self.filtercol,
                values = fields,
                #initialitem = initial,
                width = 10)
        filtercolmenu.grid(row=0,column=1,sticky='news',padx=2,pady=2)
        self.operator=StringVar()
        operatormenu = Combobox(self,
                textvariable = self.operator,
                values = self.operators,
                #initialitem = 'contains',
                width = 8)
        operatormenu.grid(row=0,column=2,sticky='news',padx=2,pady=2)
        self.filtercolvalue=StringVar()
        valsbox=Entry(self,textvariable=self.filtercolvalue,width=20)
        valsbox.grid(row=0,column=3,sticky='news',padx=2,pady=2)
        valsbox.bind("<Return>", self.parent.doFiltering)
        self.booleanop=StringVar()
        self.booleanop.set('AND')
        booleanopmenu = Combobox(self,
                textvariable = self.booleanop,
                values = self.booleanops,
                #initialitem = 'AND',
                width = 6)
        booleanopmenu.grid(row=0,column=0,sticky='news',padx=2,pady=2)
        #disable the boolean operator if it's the first filter
        #if self.index == 0:
        #    booleanopmenu.component('menubutton').configure(state=DISABLED)
        cbutton=Button(self,text='-', command=self.close)
        cbutton.grid(row=0,column=5,sticky='news',padx=2,pady=2)
        return

    def close(self):
        """Destroy and remove from parent"""
        self.parent.filters.remove(self)
        self.destroy()
        return

    def getFilter(self):
        """Get filter values for this instance"""
        col = self.filtercol.get()
        val = self.filtercolvalue.get()
        op = self.operator.get()
        booleanop = self.booleanop.get()
        return col, val, op, booleanop
