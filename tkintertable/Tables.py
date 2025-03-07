#!/usr/bin/env python
"""
    Implements the core TableCanvas class.
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
import sys
try:
    from tkinter import * # type: ignore
    from tkinter.ttk import * # type: ignore
except:
    from Tkinter import * # type: ignore
    from ttk import * # type: ignore
if (sys.version_info > (3, 0)):
    from tkinter import filedialog, messagebox, simpledialog
    from tkinter import font
    import tkinter.colorchooser as tkColorChooser
else:
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog
    import tkMessageBox as messagebox
    import tkFont as font
    import tkColorChooser

from .TableModels import TableModel
from .TableFormula import Formula
from .Prefs import Preferences
from .FilterDialogFactoryInterface import FilterDialogFactoryInterface as FDFI
from .Dialogs import *

import math, time
import os, types
import copy
import platform
import numpy as np
from bisect import bisect_left
from collections import defaultdict

class TableCanvas(Canvas):
    """A tkinter class for providing table functionality"""

    def __init__(self, parent=None, model=None, data=None, read_only=False, show_popup=True,
                 width=None, height=None, bgcolor='#F7F7FA', fgcolor='black', filterdialogfactory: FDFI = None,
                 rows=10, cols=5, **kwargs):
        Canvas.__init__(self, parent, bg=bgcolor,
                         width=width, height=height,
                         relief=GROOVE,
                         scrollregion=(0,0,300,200))
        self.parentframe = parent
        #get platform into a variable
        self.ostyp = self.checkOSType()
        self.platform = platform.system()
        self.width = width
        self.height = height
        self.set_defaults()
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.currentpage = None
        self.navFrame = None
        self.currentrow = 0
        self.currentcol = 0
        self.reverseorder = 0
        self.startrow = self.endrow = None
        self.startcol = self.endcol = None
        self.allrows = False       #for selected all rows without setting multiplerowlist
        self.multiplerowlist=[]
        self.multiplecollist=[]
        self.columnTooltipEnable=defaultdict(lambda: True)
        self.col_positions=[]       #record current column grid positions
        self.row_positions=[] 
        self.minrowheights=defaultdict(lambda : self.minrowheight)
        self.maxcellwidth = defaultdict(lambda: self.defaultmaxcellwidth)
        self.mode = 'normal'
        self.read_only = read_only
        self.show_popup = show_popup
        self.filtered = False
        self.rowUpdateRequired = False
        self.resetToMinRowHeight = False
        self.filterdialogfactory = filterdialogfactory
        if self.filterdialogfactory is not None:
            self.filterdialogfactory.subscribe(self.triggerFiltering, self.showAll)

        self.loadPrefs()
        #set any options passed in kwargs to overwrite defaults and prefs
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        if data is not None:
            self.model = TableModel()
            self.model.importDict(data)
        elif model is not None:
            self.model = model
        else:
            self.model = TableModel(rows=rows,columns=cols)

        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()
        self.tablewidth = (self.cellwidth)*self.cols
        self.tableheight = self.rowheight*self.rows
        self.do_bindings()
        #initial sort order
        self.model.setSortOrder()

        #column specific actions, define for every column type in the model
        #when you add a column type you should edit this dict
        self.columnactions = {'text' : {"Edit":  'drawCellEntry' },
                              'number' : {"Edit": 'drawCellEntry' }}
        self.setFontSize()
        self.initFontSizeTable()
        return

    def set_defaults(self):
        """Set default settings"""

        self.cellwidth=150
        self.defaultmaxcellwidth=500
        self.mincellwidth=22
        self.rowheight=20
        self.minrowheight=20
        self.xpadding=5
        self.horizlines=1
        self.vertlines=1
        self.alternaterows=0
        self.autoresizecols = 0
        self.inset=2
        self.x_start=0
        self.y_start=1
        self.linewidth=1.0
        self.rowheaderwidth=40
        self.showkeynamesinheader=False
        self.thefont = ('Arial',12)
        self.bgcolor = '#F7F7FA'
        self.fgcolor = 'black'
        self.entrybackgr = 'white'
        self.grid_color = '#ABB1AD'
        self.selectedcolor = 'yellow'
        self.rowselectedcolor = '#CCCCFF'
        self.multipleselectioncolor = '#ECD672'

        popupmenu_enabled = {"Set Fill Color" : True,
                                "Set Text Color" : True,
                                "Copy" : True,
                                "Paste" : True,
                                "Fill Down" : True,
                                "Fill Right" : True,
                                "Add Row(s)" : True,
                                "Delete Row(s)" : True,
                                "View Record" : True,
                                "Clear Data" : True,
                                "Select All" : True,
                                "Auto Fit Columns" : True,
                                "Filter Records" : True,
                                "New": True,
                                "Load": True,
                                "Save": True,
                                "Import text": True,
                                "Export csv": True,
                                "Plot Selected" : True,
                                "Plot Options" : True,
                                "Export Table" : True,
                                "Preferences" : True,
                                "Formulae->Value" : True,
                                "Rename Column": True,
                                "Sort by": True,
                                "Delete This Column": True,
                                "Add New Column": True}
        self.showPopupMenuEntry = popupmenu_enabled
        return

    def setFontSize(self):
        """Set font size to match font, we need to get rid of fontsize as
            a separate variable?"""

        if hasattr(self, 'thefont') and type(self.thefont) is tuple:
            self.fontsize = self.thefont[1]
        return

    def initFontSizeTable(self):
        symbols = list(map(lambda x: chr(x), range(255)))
        def constant_factory(c):
            return lambda: c
        symbol_sizes = defaultdict()
        for sym in symbols:
            txttmp = self.create_text(50, 50, text=sym)
            size = self.bbox(txttmp)
            symbol_sizes[sym] = size[2]-size[0]
            self.delete(txttmp)
        symbol_sizes.default_factory = constant_factory(int(np.median(list(symbol_sizes.values()))))
        self.fontSizeTable = symbol_sizes

    def mouse_wheel(self, event):
        """Handle mouse wheel scroll for windows"""

        if event.num == 5 or event.delta == -120:
            event.widget.yview_scroll(1, UNITS)
            self.tablerowheader.yview_scroll(1, UNITS)
        if event.num == 4 or event.delta == 120:
            if self.canvasy(0) < 0:
                return
            event.widget.yview_scroll(-1, UNITS)
            self.tablerowheader.yview_scroll(-1, UNITS)
        self.redrawVisible()
        return

    def do_bindings(self):
        """Bind keys and mouse clicks, this can be overriden"""
        self.bind("<Button-1>",self.handle_left_click)
        self.bind("<Double-Button-1>",self.handle_double_click)
        self.bind("<Control-Button-1>", self.handle_left_ctrl_click)
        self.bind("<Shift-Button-1>", self.handle_left_shift_click)

        self.bind("<ButtonRelease-1>", self.handle_left_release)
        if self.ostyp=='mac':
            #For mac we bind Shift, left-click to right click
            self.bind("<Button-2>", self.handle_right_click)
            self.bind('<Shift-Button-1>',self.handle_right_click)
        else:
            self.bind("<Button-3>", self.handle_right_click)

        self.bind('<B1-Motion>', self.handle_mouse_drag)
        self.bind('<Motion>', self.handle_motion)

        self.bind_all("<Control-x>", self.deleteRow)
        self.bind_all("<Control-n>", self.addRow)
        self.bind_all("<Delete>", self.clearData)
        self.bind_all("<Control-v>", self.paste)

        #if not hasattr(self,'parentapp'):
        #    self.parentapp = self.parentframe

        self.parentframe.master.bind_all("<Right>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Left>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Up>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Down>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<KP_8>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Return>", self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Tab>", self.handle_arrow_keys)
        #if 'windows' in self.platform:
        self.bind("<MouseWheel>", self.mouse_wheel)
        self.bind('<Button-4>', self.mouse_wheel)
        self.bind('<Button-5>', self.mouse_wheel)
        self.focus_set()
        return

    def getModel(self):
        """Get the current table model"""
        return self.model

    def setModel(self, model):
        """Set a new model - requires redraw to reflect changes"""
        self.model = model
        return

    def createfromDict(self, data):
        """Attempt to create a new model/table from a dict"""

        try:
            namefield=self.namefield
        except:
            namefield=data.keys()[0]
        self.model = TableModel()
        self.model.importDict(data, namefield=namefield)
        self.model.setSortOrder(0,reverse=self.reverseorder)
        return

    def createTableFrame(self, callback=None):
        self.show(callback)
        return

    def show(self, callback=None):
        """Adds column header and scrollbars and combines them with
           the current table adding all to the master frame provided in constructor.
           Table is then redrawn."""

        #Add the table and header to the frame
        self.tablerowheader = RowHeader(self.parentframe, self, width=self.rowheaderwidth)
        self.tablecolheader = ColumnHeader(self.parentframe, self)
        self.Yscrollbar = AutoScrollbar(self.parentframe,orient=VERTICAL,command=self.set_yviews)
        self.Yscrollbar.grid(row=1,column=2,rowspan=1,sticky='news',pady=0,ipady=0)
        self.Xscrollbar = AutoScrollbar(self.parentframe,orient=HORIZONTAL,command=self.set_xviews)
        self.Xscrollbar.grid(row=2,column=1,columnspan=1,sticky='news')
        self['xscrollcommand'] = self.Xscrollbar.set
        self['yscrollcommand'] = self.Yscrollbar.set
        self.tablecolheader['xscrollcommand'] = self.Xscrollbar.set
        self.tablerowheader['yscrollcommand'] = self.Yscrollbar.set
        self.parentframe.rowconfigure(1,weight=1)
        self.parentframe.columnconfigure(1,weight=1)

        self.tablecolheader.grid(row=0,column=1,rowspan=1,sticky='news',pady=0,ipady=0)
        self.tablerowheader.grid(row=1,column=0,rowspan=1,sticky='news',pady=0,ipady=0)
        self.grid(row=1,column=1,rowspan=1,sticky='news',pady=0,ipady=0)

        self.adjustColumnWidths()
        self.redrawTable(callback=callback)
        self.parentframe.bind("<Configure>", self.redrawVisible)
        self.tablecolheader.xview("moveto", 0)
        self.xview("moveto", 0)
        return

    def getVisibleRegion(self):
        """Get visible region of table to display"""

        x1, y1 = self.canvasx(0), self.canvasy(0)
        #w, h = self.winfo_width(), self.winfo_height()
        w,h= self.master.winfo_width(), self.master.winfo_height()
        if w <= 1.0 or h <= 1.0:
            w, h = self.master.winfo_width(), self.master.winfo_height()
        x2, y2 = self.canvasx(w), self.canvasy(h)
        return x1, y1, x2, y2

    def getRowPosition(self, y):
        """Get current row from canvas position"""

        h = self.rowheight
        #y_start = self.y_start
        #row = (int(y)-y_start)/h
        #if row < 0:
        #    return 0
        #if row > self.rows:
        #    row = self.rows
        #return row
        i=0
        row=0
        for r in self.row_positions:
            row = i
            if r+h>=y:
                break
            i+=1
        return row

    def getColPosition(self, x):
        """Get current col from canvas position"""

        x_start = self.x_start
        w = self.cellwidth
        i=0
        col=0
        for c in self.col_positions:
            col = i
            if c+w>=x:
                break
            i+=1
        return col

    def getVisibleRows(self, y1, y2):
        """Get the visible row range"""

        start = int(self.getRowPosition(y1))
        end = int(self.getRowPosition(y2))+1
        if end > self.rows:
            end = self.rows
        return start, end

    def getVisibleCols(self, x1, x2):
        """Get the visible column range"""

        start = self.getColPosition(x1)
        end = self.getColPosition(x2)+1
        if end > self.cols:
            end = self.cols
        return start, end

    def redrawVisible(self, event=None, callback=None):
        """Redraw the visible portion of the canvas"""

        model = self.model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()

        self.tablewidth = (self.cellwidth) * self.cols
        self.tableheight = (self.rowheight) * self.rows
        self.configure(bg=self.bgcolor)
        self.setColPositions()
        self.setRowPositions()

        #are we drawing a filtered subset of the recs?
        if self.filtered == True and self.model.filteredrecs != None:
            self.rows = len(self.model.filteredrecs)
            self.delete('colrect')

        self.rowrange = range(0,self.rows)
        self.configure(scrollregion=(0,0, self.tablewidth+self.x_start,
                self.tableheight+self.y_start))

        x1, y1, x2, y2 = self.getVisibleRegion()
        startvisiblerow, endvisiblerow = self.getVisibleRows(y1, y2)
        self.visiblerows = range(max(0, startvisiblerow-1), min(self.rows, endvisiblerow+1))
        startvisiblecol, endvisiblecol = self.getVisibleCols(x1, x2)
        self.visiblecols = range(max(0, startvisiblecol-1), min(endvisiblecol+1, self.cols))

        if self.cols == 0 or self.rows == 0:
            self.delete('entry')
            self.delete('rowrect')
            self.delete('currentrect')
            self.delete('gridline','text')
            self.tablerowheader.redraw()
            return

        self.drawGrid(startvisiblerow, endvisiblerow)
        align = self.align
        self.delete('fillrect')
        for row in self.visiblerows:
            if callback != None:
                callback()
            for col in self.visiblecols:
                colname = model.getColumnName(col)
                bgcolor = model.getColorAt(row,col, 'bg')
                fgcolor = model.getColorAt(row,col, 'fg')
                text = model.getValueAt(row,col)
                self.drawText(row, col, text, fgcolor, align)
                if bgcolor != None:
                    self.drawRect(row,col, color=bgcolor)
        self.rowUpdate()
        
        self.tablecolheader.redraw()
        self.tablerowheader.redraw(align=self.align, showkeys=self.showkeynamesinheader)
        #self.setSelectedRow(self.currentrow)
        self.drawSelectedRow()
        if self.find_withtag('colrect') != ():
            self.drawSelectedCol()
        self.drawSelectedRect(self.currentrow, self.currentcol)
        #print self.multiplerowlist

        if len(self.multiplerowlist)>1:
            self.tablerowheader.drawSelectedRows(self.multiplerowlist)
            self.drawMultipleRows(self.multiplerowlist)
            self.drawMultipleCells()
        return

    def redrawTable(self, event=None, callback=None):
        self.redrawVisible(event, callback)
        return

    def redraw(self, event=None, callback=None):
        self.redrawVisible(event, callback)
        return

    def deletePopups(self):
        if hasattr(self, 'rightmenu'):
            self.rightmenu.destroy()
        if hasattr(self.tablecolheader, 'rightmenu'):
            self.tablecolheader.rightmenu.destroy()

        if hasattr(self, 'cellentry'):
            self.cellentry.destroy()

    def redrawCell(self, row=None, col=None, recname=None, colname=None):
        """Redraw a specific cell only"""

        if row == None and recname != None:
            row = self.model.getRecordIndex(recname)
        if col == None and colname != None:
            col = self.model.getColumnIndex(colname)
        bgcolor = self.model.getColorAt(row,col, 'bg')
        fgcolor = self.model.getColorAt(row,col, 'fg')
        text = self.model.getValueAt(row,col)
        self.drawText(row, col, text, fgcolor)
        self.rowUpdate()
        if bgcolor != None:
            self.drawRect(row,col, color=bgcolor)
        return

    def adjustColumnWidths(self):
        """Optimally adjust col widths to accomodate the longest entry
            in each column - usually only called  on first redraw"""

        #self.cols = self.model.getColumnCount()
        self.requireRowHeightReset()
        try:
            fontsize = self.thefont[1]
        except:
            fontsize = self.fontsize
        scale = 8.5 * float(fontsize)/12
        for col in range(self.cols):
            colname = self.model.getColumnName(col)
            if colname in self.model.columnwidths:
                w = self.model.columnwidths[colname]
            else:
                w = self.cellwidth
            maxlen = self.model.getlongestEntry(col)
            size = maxlen * scale
            if size < w:
                continue
            #print col, size, self.cellwidth
            if size > self.maxcellwidth[colname]:
                size = self.maxcellwidth[colname]
            if size < self.mincellwidth:
                size = self.mincellwidth
            self.model.columnwidths[colname] = size + float(fontsize)/12*6
        return

    def autoResizeColumns(self):
        """Automatically set nice column widths and draw"""

        self.requireRowHeightReset()
        self.adjustColumnWidths()
        self.redrawTable()
        return

    def adjustRowHeights(self):
        for row in range(self.rows):
            if row in self.model.rowheights and self.model.rowheights[row] > self.minrowheights[row]:
                self.model.rowheights[row] = self.minrowheights[row]
                self.rowUpdateRequired = True
        return

    def setColumnTooltip(self, columnname=None, enable=True):
        if columnname is None:
            columnname = self.get_currentColName()
        self.columnTooltipEnable[columnname] = enable
        return

    def setMaxCellWidth(self, columnname=None, newmaxcellwidth=None):
        if columnname is None:
            columnname = self.get_currentColName()
        if newmaxcellwidth is None:
            self.maxcellwidth.pop(columnname)
        else:
            self.maxcellwidth[columnname] = max(self.mincellwidth, newmaxcellwidth)

    def setColPositions(self):
        """Determine current column grid positions"""

        self.col_positions=[]
        w=self.cellwidth
        x_pos=self.x_start
        self.col_positions.append(x_pos)
        for col in range(self.cols):
            colname=self.model.getColumnName(col)
            if colname in self.model.columnwidths:
                x_pos=x_pos+self.model.columnwidths[colname]
            else:
                x_pos=x_pos+w
            self.col_positions.append(x_pos)
        self.tablewidth = self.col_positions[len(self.col_positions)-1]
        return

    def setRowPositions(self):
        """Determine current row grid positions"""

        self.row_positions=[]
        h=self.rowheight
        y_pos=self.y_start
        self.row_positions.append(y_pos)
        for row in range(self.rows):
            if row in self.model.rowheights:
                y_pos=y_pos+self.model.rowheights[row]
            else:
                y_pos=y_pos+h
            self.row_positions.append(y_pos)
        self.tableheight = self.row_positions[-1]
        return

    def sortTable(self, columnIndex=0, columnName=None, reverse=0):
        """Set up sort order dict based on currently selected field"""

        self.model.setSortOrder(columnIndex, columnName, reverse)
        self.redrawTable()
        return

    def set_xviews(self,*args):
        """Set the xview of table and col header"""

        self.xview(*args)
        self.tablecolheader.xview(*args)
        self.redrawVisible()
        return

    def set_yviews(self,*args):
        """Set the xview of table and row header"""

        self.yview(*args)
        self.tablerowheader.yview(*args)
        self.redrawVisible()
        return

    def addRow(self, key=None, **kwargs):
        """Add new row"""

        key = self.model.addRow(key, **kwargs)
        self.redrawTable()
        self.setSelectedRow(self.model.getRecordIndex(key))
        return

    def addRows(self, num=None):
        """Add new rows"""

        if num == None:
            num = simpledialog.askinteger("Now many rows?",
                                            "Number of rows:",initialvalue=1,
                                             parent=self.parentframe)
        if not num:
            return
        keys = self.model.autoAddRows(num)
        self.redrawTable()
        self.setSelectedRow(self.model.getRecordIndex(keys[0]))
        return

    def addColumn(self, newname=None):
        """Add a new column"""

        if newname == None:

            coltypes = self.getModel().getDefaultTypes()
            d = MultipleValDialog(title='New Column',
                                    initialvalues=(coltypes, ''),
                                    labels=('Column Type','Name'),
                                    types=('list','string'),
                                    parent=self.parentframe)
            if d.result == None:
                return
            else:
                coltype = d.results[0]
                newname = d.results[1]

        if newname != None:
            if newname in self.getModel().columnNames:
                messagebox.showwarning("Name exists",
                                         "Name already exists!",
                                         parent=self.parentframe)
            else:
                self.model.addColumn(newname)
                self.parentframe.configure(width=self.width)
                self.redrawTable()
        return

    def deleteRow(self):
        """Delete a row"""

        if len(self.multiplerowlist)>1:
            n = messagebox.askyesno("Delete",
                                      "Delete Selected Records?",
                                      parent=self.parentframe)
            if n == True:
                rows = self.multiplerowlist
                self.model.deleteRows(rows)
                self.clearSelected()
                self.setSelectedRow(0)
                self.redrawTable()
        else:
            n = messagebox.askyesno("Delete",
                                      "Delete This Record?",
                                      parent=self.parentframe)
            if n:
                row = self.getSelectedRow()
                self.model.deleteRow(row)
                self.setSelectedRow(row-1)
                self.clearSelected()
                self.redrawTable()
        return

    def deleteColumn(self):
        """Delete currently selected column"""

        n =  messagebox.askyesno("Delete",
                                   "Delete This Column?",
                                   parent=self.parentframe)
        if n:
            col = self.getSelectedColumn()
            self.model.deleteColumn(col)
            self.currentcol = self.currentcol - 1
            self.redrawTable()
        return

    def deleteCells(self, rows, cols):
        """Clear the cell contents"""

        n =  messagebox.askyesno("Clear Confirm",
                                   "Clear this data?",
                                   parent=self.parentframe)
        if not n:
            return
        for col in cols:
            for row in rows:
                #absrow = self.get_AbsoluteRow(row)
                self.model.deleteCellRecord(row, col)
                self.redrawCell(row,col)
        return

    def clearData(self, evt=None):
        """Delete cells from gui event"""

        rows = self.multiplerowlist
        cols = self.multiplecollist
        self.deleteCells(rows, cols)
        return

    def autoAddColumns(self, numcols=None):
        """Automatically add x number of cols"""

        if numcols == None:
            numcols = simpledialog.askinteger("Auto add rows.",
                                                "How many empty columns?",
                                                parent=self.parentframe)
        self.model.auto_AddColumns(numcols)
        self.parentframe.configure(width=self.width)
        self.redrawTable()
        return

    def getRecordInfo(self, row):
        """Show the record for this row"""

        model = self.model
        #We need a custom dialog for allowing field entries here
        #absrow = self.get_AbsoluteRow(row)
        d = RecordViewDialog(title="Record Details",
                                  parent=self.parentframe, table=self, row=row)
        return

    def findValue(self, searchstring=None, findagain=None):
        """Return the row/col for the input value"""

        if searchstring == None:
            searchstring = simpledialog.askstring("Search table.",
                                               "Enter search value",
                                               parent=self.parentframe)
        found=0
        if findagain == None or not hasattr(self,'foundlist'):
            self.foundlist=[]
        if self.model!=None:
            for row in range(self.rows):
                for col in range(self.cols):
                    text = str(self.model.getValueAt(row,col))
                    if text=='' or text==None:
                        continue
                    cell=row,col
                    if findagain == 1 and cell in self.foundlist:
                        continue
                    if text.lower().find(searchstring.lower())!=-1:
                        print ('found in',row,col)
                        found=1
                        #highlight cell
                        self.delete('searchrect')
                        self.drawRect(row, col, color='red', tag='searchrect', delete=0)
                        self.lift('searchrect')
                        self.lift('celltext'+str(col)+'_'+str(row))
                        #add row/col to foundlist
                        self.foundlist.append(cell)
                        #need to scroll to centre the cell here..
                        x,y = self.getCanvasPos(row, col)
                        self.xview('moveto', x)
                        self.yview('moveto', y)
                        self.tablecolheader.xview('moveto', x)
                        self.tablerowheader.yview('moveto', y)
                        return row, col
        if found==0:
            self.delete('searchrect')
            print ('nothing found')
            return None

    def showAll(self):
        self.model.filteredrecs = None
        self.filtered = False
        self.redrawTable()
        return

    def triggerFiltering(self, doFilterCallback, event=None):
        """Filter the table display by some column values.
        We simply pass the model search function to the the filtering
        class and that handles everything else.
        See filtering frame class for how searching is done.
        """
        if self.model==None:
            return
        rowIds = doFilterCallback(self.model.data, self.model.getColumnDict())
        if rowIds is None:
            if self.model.filteredrecs is not None:
                self.showAll()
        else:
            #create a list of filtered recs
            self.model.filteredrecs = rowIds
            self.filtered = True
            self.redrawTable()
        return

    def triggerSorting(self, doSortCallback):
        """Function that is called when the sorting of the data is triggered."""
        doSortCallback((self.model.data, self.model.reclist), self.model.getColumnDict())
        self.redrawTable()
        return
    
    def resizeColumn(self, col, width):
        """Resize a column by dragging"""

        #print 'resizing column', col
        #recalculate all col positions..
        self.requireRowHeightReset()
        colname=self.model.getColumnName(col)
        self.model.columnwidths[colname]=width
        self.setColPositions()
        self.redrawTable()
        self.drawSelectedCol(self.currentcol)
        return

    def resizeRow(self, row, height):
        """Resize a row by dragging"""
        
        if height < self.minrowheights[row]:
            height = self.minrowheights[row]
        self.model.rowheights[row]=height
        self.setRowPositions()
        self.redrawTable()
        self.drawSelectedRow(self.currentrow)
        return

    def get_currentRecord(self):
        """Get the currently selected record"""

        rec = self.model.getRecordAtRow(self.currentrow)
        return rec

    def get_currentColName(self):
        """Get the currently selected record name"""

        colname = self.mo(self.currentcol)
        return colname

    def get_currentRecordName(self):
        """Get the currently selected record name"""

        recname = self.model.getRecName(self.currentrow)
        return recname

    def get_selectedRecordNames(self):
        """Get a list of the current multiple selection, if any"""

        recnames=[]
        for row in self.multiplerowlist:
            recnames.append(self.model.getRecName(row))
        return recnames

    def get_currentRecCol(self):
        """Get the clicked rec and col names as a tuple"""

        recname = self.get_currentRecordName()
        colname = self.get_currentColName()
        return (recname, colname)

    def get_row_clicked(self, event):
        """get row where event on canvas occurs"""

        h=self.rowheight
        #get coord on canvas, not window, need this if scrolling
        y = int(self.canvasy(event.y))
        y_start=self.y_start

        for idx, rowpos in enumerate(self.row_positions):
            try:
                nextpos = self.row_positions[idx+1]
            except:
                nextpos = self.tableheight
            if y > rowpos and y <= nextpos:
                return idx

    def get_col_clicked(self,event):
        """get col where event on canvas occurs"""

        w=self.cellwidth
        x = int(self.canvasx(event.x))
        x_start=self.x_start
        for idx, colpos in enumerate(self.col_positions):
            try:
                # nextpos=self.col_positions[self.col_positions.index(colpos)+1]
                nextpos = self.col_positions[idx+1]
            except:
                nextpos = self.tablewidth
                
            if x > colpos and x <= nextpos:
                #print 'x=', x, 'colpos', colpos, idx
                return idx
            else:
                #print None
                pass
        #return colc

    def setSelectedRow(self, row):
        """Set currently selected row and reset multiple row list"""

        self.currentrow = row
        self.multiplerowlist = []
        self.multiplerowlist.append(row)
        return

    def setSelectedCol(self, col):
        """Set currently selected column"""

        self.currentcol = col
        self.multiplecollist = []
        self.multiplecollist.append(col)
        return

    def setSelectedCells(self, startrow, endrow, startcol, endcol):
        """Set a block of cells selected"""

        self.currentrow = startrow
        self.currentcol = startcol
        if startrow < 0 or startcol < 0:
            return
        if endrow > self.rows or endcol > self.cols:
            return
        for r in range(startrow, endrow):
            self.multiplerowlist.append(r)
        for c in range(startcol, endcol):
            self.multiplecollist.append(c)
        return

    def getSelectedRow(self):
        """Get currently selected row"""
        return self.currentrow

    def getSelectedColumn(self):
        """Get currently selected column"""
        return self.currentcol

    def select_All(self):
        """Select all rows and cells"""

        self.startrow = 0
        self.endrow = self.rows
        self.multiplerowlist = range(self.startrow,self.endrow)
        self.drawMultipleRows(self.multiplerowlist)
        self.startcol = 0
        self.endcol = self.cols
        self.multiplecollist = range(self.startcol, self.endcol)
        self.drawMultipleCells()
        return

    def getCellCoords(self, row, col):
        """Get x-y coordinates to drawing a cell in a given row/col"""
        colname=self.model.getColumnName(col)
        if colname in self.model.columnwidths:
            w=self.model.columnwidths[colname]
        else:
            w=self.cellwidth
        if row in self.model.rowheights:
            h=self.model.rowheights[row]
        else:
            h=self.rowheight
        x_start=self.x_start
        y_start=self.y_start

        #get nearest rect co-ords for that row/col
        #x1=x_start+w*col
        x1=self.col_positions[col]
        y1=self.row_positions[row]
        x2=x1+w
        y2=y1+h
        return x1,y1,x2,y2

    def getCanvasPos(self, row, col):
        """Get the cell x-y coords as a fraction of canvas size"""
        if self.rows==0:
            return None, None
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        cx=float(x1)/self.tablewidth
        cy=float(y1)/self.tableheight
        return cx, cy

    def isInsideTable(self,x,y):
        """Returns true if x-y coord is inside table bounds"""
        if self.x_start < x < self.tablewidth and self.y_start < y < self.tableheight:
            return 1
        else:
            return 0
        return answer

    def setRowHeight(self, h):
        """Set the row height"""
        if h < self.minrowheight: 
            h = self.minrowheight
        self.rowheight = h
        self.minrowheights.default_factory = lambda: self.rowheight
        return
    
    def setRowMultiline(self, rowId=None, isMultiline=True):
        if rowId is None:
            rowId = self.currentrow
        if isMultiline:
            self.model.multilinerows.add(rowId)
        else:
            self.model.multilinerows.discard(rowId)

    def setColumnMultiline(self, columnName=None, isMultiline=True):
        if columnName is None:
            columnName = self.get_currentColName()
        if isMultiline:
            self.model.multilinecolumns.add(columnName)
        else:
            self.model.multilinecolumns.discard(columnName)

    def isMultiline(self, rowId=None, columnName=None):
        if rowId is None:
            rowId = self.currentrow
        if columnName is None:
            columnName = self.get_currentColName()
        return rowId in self.model.multilinerows or columnName in self.model.multilinecolumns

    def clearSelected(self):
        self.delete('rect')
        self.delete('entry')
        self.delete('tooltip')
        self.delete('searchrect')
        self.delete('colrect')
        self.delete('multicellrect')

        #self.delete('formulabox')
        return

    def gotoprevRow(self):
        """Programmatically set previous row - eg. for button events"""
        self.clearSelected()
        current = self.getSelectedRow()
        self.setSelectedRow(current-1)
        self.startrow = current-1
        self.endrow = current-1
        #reset multiple selection list
        self.multiplerowlist=[]
        self.multiplerowlist.append(self.currentrow)
        self.drawSelectedRect(self.currentrow, self.currentcol)
        self.drawSelectedRow()
        coltype = self.model.getColumnType(self.currentcol)
        if coltype == 'text' or coltype == 'number':
            self.drawCellEntry(self.currentrow, self.currentcol)
        return

    def gotonextRow(self):
        """Programmatically set next row - eg. for button events"""
        self.clearSelected()
        current = self.getSelectedRow()
        self.setSelectedRow(current+1)
        self.startrow = current+1
        self.endrow = current+1
        #reset multiple selection list
        self.multiplerowlist=[]
        self.multiplerowlist.append(self.currentrow)
        self.drawSelectedRect(self.currentrow, self.currentcol)
        self.drawSelectedRow()
        coltype = self.model.getColumnType(self.currentcol)
        if coltype == 'text' or coltype == 'number':
            self.drawCellEntry(self.currentrow, self.currentcol)
        return

    def handle_left_click(self, event):
        """Respond to a single press"""

        #which row and column is the click inside?
        self.clearSelected()
        self.allrows = False
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        self.focus_set()
        if self.mode == 'formula':
            self.handleFormulaClick(rowclicked, colclicked)
            return
        if hasattr(self, 'cellentry'):
            self.cellentry.destroy()
        #ensure popup menus are removed if present
        if hasattr(self, 'rightmenu'):
            self.rightmenu.destroy()
        if hasattr(self.tablecolheader, 'rightmenu'):
            self.tablecolheader.rightmenu.destroy()

        self.startrow = rowclicked
        self.endrow = rowclicked
        self.startcol = colclicked
        self.endcol = colclicked
        #reset multiple selection list
        self.multiplerowlist=[]
        self.multiplerowlist.append(rowclicked)
        if rowclicked is None or colclicked is None:
            return
        if 0 <= rowclicked < self.rows and 0 <= colclicked < self.cols:
            self.setSelectedRow(rowclicked)
            self.setSelectedCol(colclicked)
            self.drawSelectedRect(self.currentrow, self.currentcol)
            self.drawSelectedRow()
            self.tablerowheader.drawSelectedRows(rowclicked)
            coltype = self.model.getColumnType(colclicked)
            if coltype == 'text' or coltype == 'number':
                self.drawCellEntry(rowclicked, colclicked)
        return

    def handle_left_release(self,event):
        self.endrow = self.get_row_clicked(event)
        return

    def handle_left_ctrl_click(self, event):
        """Handle ctrl clicks for multiple row selections"""
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        if 0 <= rowclicked < self.rows and 0 <= colclicked < self.cols:
            if rowclicked not in self.multiplerowlist:
                self.multiplerowlist.append(rowclicked)
            else:
                self.multiplerowlist.remove(rowclicked)
            self.drawMultipleRows(self.multiplerowlist)
            if colclicked not in self.multiplecollist:
                self.multiplecollist.append(colclicked)
            #print self.multiplecollist
            self.drawMultipleCells()
        return

    def handle_left_shift_click(self, event):
        """Handle shift click, for selecting multiple rows"""
        #Has same effect as mouse drag, so just use same method
        self.handle_mouse_drag(event)
        return

    def handle_mouse_drag(self, event):
        """Handle mouse moved with button held down, multiple selections"""

        if hasattr(self, 'cellentry'):
            self.cellentry.destroy()
        rowover = self.get_row_clicked(event)
        colover = self.get_col_clicked(event)
        if colover == None or rowover == None:
            return

        if rowover >= self.rows or self.startrow > self.rows:
            return
        else:
            self.endrow = rowover
        #do columns
        if colover > self.cols or self.startcol > self.cols:
            return
        else:
            self.endcol = colover
            if self.startcol is None or self.endcol is None:
                return
            if self.endcol < self.startcol:
                self.multiplecollist = range(self.endcol, self.startcol+1)
            else:
                self.multiplecollist = range(self.startcol, self.endcol+1)
            #print self.multiplecollist
        #draw the selected rows
        if self.endrow != self.startrow:
            if self.endrow < self.startrow:
                self.multiplerowlist = range(self.endrow, self.startrow+1)
            else:
                self.multiplerowlist = range(self.startrow, self.endrow+1)
            self.drawMultipleRows(self.multiplerowlist)
            self.tablerowheader.drawSelectedRows(self.multiplerowlist)
            #draw selected cells outline using row and col lists
            #print self.multiplerowlist
            self.drawMultipleCells()
        else:
            self.multiplerowlist = []
            self.multiplerowlist.append(self.currentrow)
            if len(self.multiplecollist) >= 1:
                self.drawMultipleCells()
            self.delete('multiplesel')
        #print self.multiplerowlist
        return

    def handle_arrow_keys(self, event):
        """Handle arrow keys press"""
        #print event.keysym

        row = self.get_row_clicked(event)
        col = self.get_col_clicked(event)
        x,y = self.getCanvasPos(self.currentrow, 0)
        if x == None:
            return

        if event.keysym == 'Up':
            if self.currentrow == 0:
                return
            else:
                self.currentrow  = self.currentrow -1
        elif event.keysym == 'Down':
            if self.currentrow >= self.rows-1:
                return
            else:
                self.currentrow  = self.currentrow +1
        elif event.keysym == 'Right' or event.keysym == 'Tab':
            if self.currentcol >= self.cols-1:
                if self.currentrow < self.rows-1:
                    self.currentcol = 0
                    self.currentrow  = self.currentrow +1
                else:
                    return
            else:
                self.currentcol  = self.currentcol +1
        elif event.keysym == 'Left':
            if self.currentcol == 0:
                if self.currentrow == 0:
                    return
                else:
                    self.currentcol = self.cols-1
                    self.currentrow = self.currentrow - 1
            else:
                self.currentcol  = self.currentcol -1
        self.drawSelectedRect(self.currentrow, self.currentcol)
        coltype = self.model.getColumnType(self.currentcol)
        if coltype == 'text' or coltype == 'number':
            self.delete('entry')
            self.drawCellEntry(self.currentrow, self.currentcol)
        return

    def handle_double_click(self, event):
        """Do double click stuff. Selected row/cols will already have
           been set with single click binding"""

        '''row = self.get_row_clicked(event)
        col = self.get_col_clicked(event)
        model=self.getModel()
        cellvalue = model.getCellRecord(row, col)
        if Formula.isFormula(cellvalue):
            self.formula_Dialog(row, col, cellvalue)'''

        return

    def handle_right_click(self, event):
        """respond to a right click"""

        if self.show_popup == False:
            return
        self.delete('tooltip')
        self.tablerowheader.clearSelected()
        if hasattr(self, 'rightmenu'):
            self.rightmenu.destroy()
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        if colclicked == None:
            self.rightmenu = self.popupMenu(event, outside=1)
            return

        if (rowclicked in self.multiplerowlist or self.allrows == True) and colclicked in self.multiplecollist:
            self.rightmenu = self.popupMenu(event, rows=self.multiplerowlist, cols=self.multiplecollist)
        else:
            if 0 <= rowclicked < self.rows and 0 <= colclicked < self.cols:
                self.clearSelected()
                self.allrows = False
                self.setSelectedRow(rowclicked)
                self.setSelectedCol(colclicked)
                self.drawSelectedRect(self.currentrow, self.currentcol)
                self.drawSelectedRow()
            if self.isInsideTable(event.x,event.y) == 1:
                self.rightmenu = self.popupMenu(event,rows=self.multiplerowlist, cols=self.multiplecollist)
            else:
                self.rightmenu = self.popupMenu(event, outside=1)
        return

    def handle_motion(self, event):
        """Handle mouse motion on table"""

        self.delete('tooltip')
        row = self.get_row_clicked(event)
        col = self.get_col_clicked(event)
        if row == None or col == None:
            return
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.drawTooltip(row, col)

        return

    def gotonextCell(self, event):
        """Move highlighted cell to next cell in row or a new col"""
        #print 'next'
        if hasattr(self, 'cellentry'):
            self.cellentry.destroy()
        self.currentcol=self.currentcol+1
        if self.currentcol >= self.cols-1:
            self.currentrow  = self.currentrow +1
            self.currentcol = self.currentcol+1
        self.drawSelectedRect(self.currentrow, self.currentcol)
        return

    def movetoSelectedRow(self, row=None, recname=None):
        """Move to selected row, updating table"""
        row=self.model.getRecordIndex(recname)
        self.setSelectedRow(row)
        self.drawSelectedRow()
        x,y = self.getCanvasPos(row, 0)
        self.yview('moveto', y-0.01)
        self.tablecolheader.yview('moveto', y)
        return

    def handleFormulaClick(self, row, col):
        """Do a dialog for cell formula entry"""

        model = self.getModel()
        cell = list(model.getRecColNames(row, col))
        #absrow = self.get_AbsoluteRow(row)
        self.formulaText.insert(END, str(cell))
        self.formulaText.focus_set()
        self.drawSelectedRect(row, col, color='red')
        return

    def formula_Dialog(self, row, col, currformula=None):
        """Formula dialog"""
        self.mode = 'formula'
        print (self.mode)
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        w=300
        h=h=self.rowheight * 3
        def close():
            if hasattr(self,'formulaWin'):
                self.delete('formulabox')
            self.mode = 'normal'
        def calculate():
            #get text area contents and do formula
            f = self.formulaText.get(1.0, END)
            f = f.strip('\n')
            self.model.setFormulaAt(f,row,col)
            value = self.model.doFormula(f)
            color = self.model.getColorAt(row,col,'fg')
            self.drawText(row, col, value, color)
            self.rowUpdate()
            close()
            self.mode = 'normal'
            return
        def clear():
            self.formulaText.delete(1.0, END)

        self.formulaFrame = Frame(width=w,height=h,bd=3)
        self.formulaText = Text(self.formulaFrame, width=30, height=8, bg='white',relief=GROOVE)
        self.formulaText.pack(side=LEFT,padx=2,pady=2)
        if currformula != None:
            self.formulaText.insert(END, Formula.getFormula(currformula))
        cancelbutton=Button(self.formulaFrame, text='Cancel',
                            bg='#99ccff',command=close)
        cancelbutton.pack(fill=BOTH,padx=2,pady=2)
        donebutton=Button(self.formulaFrame, text='Done',
                          bg='#99ccff',command=calculate)
        donebutton.pack(fill=BOTH,padx=2,pady=2)
        '''clrbutton=Button(self.formulaFrame, text='Clear',
                           bg='#99ccff',command=clear)
        clrbutton.pack(fill=BOTH,padx=2,pady=2) '''
        #add to canvas
        self.formulaWin = self.create_window(x1+self.inset,y1+self.inset,
                                width=w,height=h,
                                window=self.formulaFrame,anchor='nw',
                                tag='formulabox')
        self.formulaText.focus_set()
        return

    def convertFormulae(self, rows, cols=None):
        """Convert the formulas in the cells to their result values"""

        if len(self.multiplerowlist) == 0 or len(self.multiplecollist) == 0:
            return None

        print (rows, cols)
        if cols == None:
            cols = range(self.cols)
        for r in rows:
            #absr=self.get_AbsoluteRow(r)
            for c in cols:
                val = self.model.getValueAt(r,c)
                self.model.setValueAt(val, r, c)
        return

    def paste(self, event=None):
        """Copy from clipboard"""

        print (self.parentframe.clipboard_get())
        return

    def copyCell(self, rows, cols=None):
        """Copy cell contents to a temp internal clipboard"""

        row = rows[0]; col = cols[0]
        #absrow = self.get_AbsoluteRow(row)
        self.clipboard = copy.deepcopy(self.model.getCellRecord(row, col))
        return

    def pasteCell(self, rows, cols=None):
        """Paste cell from internal clipboard"""

        row = rows[0]; col = cols[0]
        #absrow = self.get_AbsoluteRow(row)
        val = self.clipboard
        self.model.setValueAt(val, row, col)
        self.redrawTable()
        return

    def copyColumns(self):
        """Copy current selected cols"""

        M = self.model
        coldata = {}
        for col in self.multiplecollist:
            name = M.columnNames[col]
            coldata[name] = M.getColumnData(columnName=name)
        return coldata

    def pasteColumns(self, coldata):
        """Paste new cols, overwrites existing names"""

        M = self.model
        for name in coldata:
            if name not in M.columnNames:
                M.addColumn(name)
            for r in range(len(coldata[name])):
                val = coldata[name][r]
                col = M.columnNames.index(name)
                if r >= self.rows:
                    break
                M.setValueAt(val, r, col)
        self.redrawTable()
        return coldata

    # --- Some cell specific actions here ---

    def setcellColor(self, rows, cols=None, newColor=None, key=None, redraw=True):
        """Set the cell color for one or more cells and save it in the model color"""

        model = self.getModel()
        if newColor == None:
            ctuple, newColor = tkColorChooser.askcolor(title='pick a color')
            if newColor == None:
                return

        if type(rows) is int:
            x=rows
            rows=[]
            rows.append(x)
        if self.allrows == True:
            #we use all rows if the whole column has been selected
            rows = range(0,self.rows)
        if cols == None:
            cols = range(self.cols)
        for col in cols:
            for row in rows:
                #absrow = self.get_AbsoluteRow(row)
                model.setColorAt(row, col, color=newColor, key=key)
                #setcolor(absrow, col)
        if redraw == True:
            self.redrawTable()
        return

    def popupMenu(self, event, rows=None, cols=None, outside=None):
        """Add left and right click behaviour for canvas, should not have to override
            this function, it will take its values from defined dicts in constructor"""
        
        fdialog = None
        if self.filterdialogfactory is not None:
            fdialog = lambda : self.filterdialogfactory.createFilteringDialog(parent=self, fields=self.model.columnNames)

        defaultactions = {"Set Fill Color" : lambda : self.setcellColor(rows,cols,key='bg'),
                        "Set Text Color" : lambda : self.setcellColor(rows,cols,key='fg'),
                        "Copy" : lambda : self.copyCell(rows, cols),
                        "Paste" : lambda : self.pasteCell(rows, cols),
                        "Fill Down" : lambda : self.fillDown(rows, cols),
                        "Fill Right" : lambda : self.fillAcross(cols, rows),
                        "Add Row(s)" : lambda : self.addRows(),
                        "Delete Row(s)" : lambda : self.deleteRow(),
                        "View Record" : lambda : self.getRecordInfo(row),
                        "Clear Data" : lambda : self.deleteCells(rows, cols),
                        "Select All" : self.select_All,
                        "Auto Fit Columns" : self.autoResizeColumns,
                        "Filter Records" : fdialog,
                        "New": self.new,
                        "Load": self.load,
                        "Save": self.save,
                        "Import text":self.importTable,
                        "Export csv": self.exportTable,
                        "Plot Selected" : self.plotSelected,
                        "Plot Options" : self.plotSetup,
                        "Export Table" : self.exportTable,
                        "Preferences" : self.showtablePrefs,
                        "Formulae->Value" : lambda : self.convertFormulae(rows, cols)}

        if self.filterdialogfactory is None:
            del defaultactions['Filter Records']

        main = ["Set Fill Color","Set Text Color","Copy", "Paste", "View Record", "Fill Down","Fill Right",
                "Clear Data"]
        general = ["Select All", "Add Row(s)" , "Delete Row(s)", "Auto Fit Columns", "Filter Records", "Preferences"]
        if self.filterdialogfactory is None:
            general.remove('Filter Records')
        filecommands = ['New','Load','Save','Import text','Export csv']
        plotcommands = ['Plot Selected','Plot Options']

        def createSubMenu(parent, label, commands):
            menu = Menu(parent, tearoff = 0)
            any = False
            for action in commands:
                if self.showPopupMenuEntry[action]:
                    any = True
                    menu.add_command(label=action, command=defaultactions[action])
            if any:
                popupmenu.add_cascade(label=label,menu=menu)
            else:
                menu = None
            return menu

        def add_commands(fieldtype):
            """Add commands to popup menu for column type and specific cell"""
            functions = self.columnactions[fieldtype]
            for f in functions.keys():
                func = getattr(self, functions[f])
                popupmenu.add_command(label=f, command= lambda : func(row,col))
            return

        popupmenu = Menu(self, tearoff = 0)
        def popupFocusOut(event):
            popupmenu.unpost()

        if outside == None:
            #if outside table, just show general items
            row = self.get_row_clicked(event)
            col = self.get_col_clicked(event)
            coltype = self.model.getColumnType(col)
            def add_defaultcommands():
                """now add general actions for all cells"""
                for action in main:
                    if action == 'Fill Down' and (rows == None or len(rows) <= 1):
                        continue
                    if action == 'Fill Right' and (cols == None or len(cols) <= 1):
                        continue
                    else:
                        if self.showPopupMenuEntry[action]:
                            popupmenu.add_command(label=action, command=defaultactions[action])
                return

            if coltype in self.columnactions:
                add_commands(coltype)
            add_defaultcommands()

        for action in general:
            if self.showPopupMenuEntry[action]:
                popupmenu.add_command(label=action, command=defaultactions[action])

        popupmenu.add_separator()
        createSubMenu(popupmenu, 'File', filecommands)
        createSubMenu(popupmenu, 'Plot', plotcommands)
        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        return popupmenu

    # --- spreadsheet type functions ---

    def fillDown(self, rowlist, collist):
        """Fill down a column, or multiple columns"""
        model = self.model
        #absrow  = self.get_AbsoluteRow(rowlist[0])
        #remove first element as we don't want to overwrite it
        rowlist.remove(rowlist[0])

        #if this is a formula, we have to treat it specially
        for col in collist:
            val = self.model.getCellRecord(row, col)
            f=val #formula to copy
            i=1
            for r in rowlist:
                #absr = self.get_AbsoluteRow(r)
                if Formula.isFormula(f):
                    newval = model.copyFormula(f, r, col, offset=i)
                    model.setFormulaAt(newval, r, col)
                else:
                    model.setValueAt(val, r, col)
                #print 'setting', val, 'at row', r
                i+=1

        self.redrawTable()
        return

    def fillAcross(self, collist, rowlist):
        """Fill across a row, or multiple rows"""
        model = self.model
        #row = self.currentrow
        #absrow  = self.get_AbsoluteRow(collist[0])
        frstcol = collist[0]
        collist.remove(frstcol)

        for row in rowlist:
            #absr = self.get_AbsoluteRow(row)
            val = self.model.getCellRecord(absr, frstcol)
            f=val     #formula to copy
            i=1
            for c in collist:
                if Formula.isFormula(f):
                    newval = model.copyFormula(f, r, c, offset=i, dim='x')
                    model.setFormulaAt(newval, r, c)
                else:
                    model.setValueAt(val, r, c)
                i+=1
        self.redrawTable()
        return

    def getSelectionValues(self):
        """Get values for current multiple cell selection"""
        if len(self.multiplerowlist) == 0 or len(self.multiplecollist) == 0:
            return None
        rows = self.multiplerowlist
        cols = self.multiplecollist
        model = self.model
        if len(rows)<1 or len(cols)<1:
            return None
        #if only one row selected we plot whole col
        if len(rows) == 1:
            rows = self.rowrange
        lists = []

        for c in cols:
            x=[]
            for r in rows:
                #absr = self.get_AbsoluteRow(r)
                val = model.getValueAt(r,c)
                if val == None or val == '':
                    continue
                x.append(val)
            lists.append(x)
        return lists

    def plotSelected(self, graphtype='XY'):
        """Plot the selected data using pylab - if possible"""

        from .Plot import pylabPlotter
        if not hasattr(self, 'pyplot'):
            self.pyplot = pylabPlotter()
        plotdata = []
        for p in self.getSelectionValues():
            x = []
            fail = False
            for d in p:
                try:
                    x.append(float(d))
                except:
                    fail = True
                    continue
            if fail == False:
                plotdata.append(x)

        pltlabels = self.getplotlabels()
        if len(pltlabels) > 2:
            self.pyplot.setDataSeries(pltlabels)
            self.pyplot.showlegend = 1
        self.pyplot.plotCurrent(data=plotdata, graphtype=graphtype)
        return

    def plotSetup(self):
        """Call pylab plot dialog setup, send data if we haven't already
            plotted"""

        from PylabPlot import pylabPlotter
        if not hasattr(self, 'pyplot'):
            self.pyplot = pylabPlotter()
        plotdata = self.getSelectionValues()
        if not self.pyplot.hasData() and plotdata != None:
            print ('has data')
            plotdata = self.getSelectionValues()
            pltlabels = self.getplotlabels()
            self.pyplot.setDataSeries(pltlabels)
            self.pyplot.plotSetup(plotdata)
        else:
            self.pyplot.plotSetup()
        return

    def getplotlabels(self):
        """Get labels for plot series from col labels"""
        pltlabels = []
        for col in self.multiplecollist:
            pltlabels.append(self.model.getColumnLabel(col))
        return pltlabels

    #--- Drawing stuff ---

    def drawGrid(self, startrow, endrow):
        """Draw the table grid lines"""
        self.delete('gridline','text')
        rows=len(self.rowrange)
        cols=self.cols
        x_start=self.x_start
        y_start=self.y_start
        x_pos=x_start

        if self.vertlines==1:
            for col in range(cols+1):
                x=self.col_positions[col]
                self.create_line(x,y_start,x,self.tableheight, tag='gridline',
                                     fill=self.grid_color, width=self.linewidth)
        if self.horizlines==1:
            for row in range(startrow, endrow+1):
                y_pos=self.row_positions[row]
                self.create_line(x_start,y_pos,self.tablewidth,y_pos, tag='gridline',
                                    fill=self.grid_color, width=self.linewidth)
        return

    def drawRowHeader(self):
        """User has clicked to select a cell"""
        self.delete('rowheader')
        x_start=self.x_start
        y_start=self.y_start
        h=self.rowheight
        rowpos=0
        for row in self.rowrange:
            x1,y1,x2,y2 = self.getCellCoords(rowpos,0)
            self.create_rectangle(0,y1,x_start-2,y2,
                                      fill='gray75',
                                      outline='white',
                                      width=1,
                                      tag='rowheader')
            self.create_text(x_start/2,y1+h/2,
                                      text=row+1,
                                      fill='black',
                                      font=self.thefont,
                                      tag='rowheader')
            rowpos+=1
        return

    def drawSelectedRect(self, row, col, color=None):
        """User has clicked to select a cell"""
        if col >= self.cols:
            return
        self.delete('currentrect')
        bg = self.selectedcolor
        if color == None:
            color = 'gray25'
        w=3
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        rect = self.create_rectangle(x1+w/2,y1+w/2,x2-w/2,y2-w/2,
                                  fill=bg,
                                  outline=color,
                                  width=w,
                                  stipple='gray50',
                                  tag='currentrect')
        #self.lower('currentrect')
        #raise text above all
        self.lift('celltext'+str(col)+'_'+str(row))
        return

    def drawRect(self, row, col, color=None, tag=None, delete=1):
        """Cell is colored"""
        if delete==1:
            self.delete('cellbg'+str(row)+str(col))
        if color==None or color==self.bgcolor:
            return
        else:
            bg=color
        if tag==None:
            recttag='fillrect'
        else:
            recttag=tag
        w=1
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        rect = self.create_rectangle(x1+w/2,y1+w/2,x2-w/2,y2-w/2,
                                  fill=bg,
                                  outline=bg,
                                  width=w,
                                  tag=(recttag,'cellbg'+str(row)+str(col)))
        self.lower(recttag)
        return

    def drawCellEntry(self, row, col, text=None):
        """When the user single/double clicks on a text/number cell, bring up entry window"""

        if self.read_only == True:
            return
        #absrow = self.get_AbsoluteRow(row)
        h=self.rowheight
        model=self.getModel()
        cellvalue = self.model.getCellRecord(row, col)
        if Formula.isFormula(cellvalue):
            return
        else:
            text = self.model.getValueAt(row, col)
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        w=x2-x1

        def callback(e):
            if e.widget._name.startswith('!entry'):
                isMultiline = False
            else:
                isMultiline = True
            if isMultiline:
                value = e.widget.get('1.0', 'end')
            else:
                value = txtvar.get()
            if value == '=':
                #do a dialog that gets the formula into a text area
                #then they can click on the cells they want
                #when done the user presses ok and its entered into the cell
                self.cellentry.destroy()
                #its all done here..
                self.formula_Dialog(row, col)
                return

            coltype = self.model.getColumnType(col)
            if coltype == 'number':
                sta = self.checkDataEntry(e, isText=isMultiline)
                if sta == 1:
                    model.setValueAt(value,row,col)
            elif coltype == 'text':
                if e.keysym=='Return' and isMultiline and e.state & 0x0001 == 0:
                    value = value[:-1]
                model.setValueAt(value,row,col)

            color = self.model.getColorAt(row,col,'fg')
            self.drawText(row, col, value, color, align=self.align)
            self.rowUpdate()
            if e.keysym=='Return':
                if not isMultiline or (isMultiline and e.state & 0x0001 == 0):
                    self.delete('entry')
            return
        
        #Draw an entry window
        if self.isMultiline(row, self.model.getColumnName(col)):
            h = model.rowheights[row]
            self.cellentry = Text(self.parentframe, width=20, takefocus=1, font=self.thefont, borderwidth=0)
            self.cellentry.insert(1.0, text)
            self.cellentry.bind('<Return>', callback)
            self.cellentry.bind('<KeyRelease>', callback)
            self.cellentry.focus_set()
            self.entrywin=self.create_window(x1+self.inset,y1+self.inset,
                                    width=w-self.inset*2,height=h,
                                    window=self.cellentry,anchor='nw',
                                    tag='entry')
        else:
            txtvar = StringVar()
            txtvar.set(text)

            self.cellentry=Entry(self.parentframe,width=20,
                            textvariable=txtvar,
                            #bg=self.entrybackgr,
                            #relief=FLAT,
                            takefocus=1,
                            font=self.thefont)
            self.cellentry.icursor(END)
            self.cellentry.bind('<Return>', callback)
            self.cellentry.bind('<KeyRelease>', callback)
            self.cellentry.focus_set()
            self.entrywin=self.create_window(x1+self.inset,y1+self.inset,
                                    width=w-self.inset*2,height=h-self.inset*2,
                                    window=self.cellentry,anchor='nw',
                                    tag='entry')

        return

    def checkDataEntry(self,event=None, isText=False):
        """do validation checks on data entry in a widget"""
        #if user enters commas, change to points
        import re
        if isText:
            value=event.widget.get('1.0', 'end')
        else:
            value=event.widget.get()
        if value!='':
            try:
                value=re.sub(',','.', value)
                value=float(value)

            except ValueError:
                event.widget.configure(bg='red')
                return 0
        elif value == '':
            return 1
        return 1

    def estimateWordLength(self, word: str):
        if len(word) == 0:
            return 0
        lens = list(map(lambda x: self.fontSizeTable[x], word))
        return sum(lens)-(len(word)-1)*2
    
    def estimateWordLengthCumulated(self, word: str):
        if len(word) == 0:
            return []
        lens = list(map(lambda x: self.fontSizeTable[x]-2, word))
        lens[0] += 2
        return np.cumsum(lens)

    def truncateToWidth(self, word: str, width):
        llist = self.estimateWordLengthCumulated(word)
        if bisect_left(llist, width) < len(word):
            idx = bisect_left(llist, width-3*(self.fontSizeTable['.']-2))
            return word[:idx]+"..."
        else:
            return word

    def drawText(self, row, col, celltxt, fgcolor=None, align=None):
        """Draw the text inside a cell area"""

        self.delete('celltext'+str(col)+'_'+str(row))
        h=self.rowheight
        pad=self.xpadding
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        w=x2-x1-2*pad
        wrap = False
        colname = self.model.getColumnName(col)
        multiline = self.isMultiline(row, colname)
        fontsize = self.fontsize
        scale = 8.5 * float(fontsize)/12
        # If celltxt is a number then we make it a string
        if type(celltxt) is float or type(celltxt) is int:
            celltxt=str(celltxt)
        length = len(celltxt)
        if length == 0:
            return
        #if cell width is less than x, print nothing
        if w<=10:
            return

        if fgcolor == None or fgcolor == "None":
            fgcolor = self.fgcolor
        if align == None:
            align = 'w'
        if align == 'w':
            x1 = x1-w/2+pad
        elif align == 'e':
            x1 = x1+w/2-pad

        if w < 18:
            celltxt = '.'
        elif not multiline:
            celltxt = self.truncateToWidth(celltxt, w)
            ##scaling between canvas and text normalised to about font 14
            #scale = 8.5 * float(fontsize)/12
            #size = length * scale
            #if size > w:
            #    newlength = w / scale
            #    #print w, size, length, newlength
            #    celltxt = celltxt[0:int(math.floor(newlength))]

        #if celltxt is dict then we are drawing a hyperlink
        if self.isLink(celltxt) == True:
            haslink=0
            linktext=celltxt['text']
            if len(linktext) > w/scale or w<28:
                linktext=linktext[0:int(w/fontsize*1.2)-2]+'..'
            if celltxt['link']!=None and celltxt['link']!='':
                f,s = self.thefont
                linkfont = (f, s, 'underline')
                linkcolor='blue'
                haslink=1
            else:
                linkfont = self.thefont
                linkcolor=fgcolor

            rect = self.create_text(x1+w/2,y1+h/2,
                                      text=linktext,
                                      fill=linkcolor,
                                      font=linkfont,
                                      tag=('text','hlink','celltext'+str(col)+'_'+str(row)))
            if haslink == 1:
                self.tag_bind(rect, '<Double-Button-1>', self.check_hyperlink)

        #just normal text
        else:
            if multiline:
                rect = self.create_text(x1+w/2,y1+1,
                                      text=celltxt,
                                      fill=fgcolor,
                                      font=self.thefont,
                                      anchor="n"+align,
                                      tag=('text','celltext'+str(col)+'_'+str(row)),
                                      width=w,
                                      justify='left')
                box = self.bbox(rect)
                minh = box[3]-box[1]+2
                self.minrowheights[row] = max(self.minrowheights[row], minh)
                if row not in self.model.rowheights or self.model.rowheights[row] < minh:
                    self.model.rowheights[row] = minh
                    self.rowUpdateRequired = True
                if self.resetToMinRowHeight and self.model.rowheights[row] > self.minrowheights[row]:
                    self.model.rowheights[row] = self.minrowheights[row]
                    self.rowUpdateRequired = True

            else:
                rect = self.create_text(x1+w/2,y1+1,
                                      text=celltxt,
                                      fill=fgcolor,
                                      font=self.thefont,
                                      anchor="n"+align,
                                      tag=('text','celltext'+str(col)+'_'+str(row)))
        return

    def isLink(self, cell):
        """Checks if cell is a hyperlink, without using isinstance"""
        try:
            if 'link' in cell and type(cell) is dict:
                return True
        except:
            return False

    def drawSelectedRow(self, row=None):
        """Draw the highlight rect for the currently selected row"""

        self.delete('rowrect')
        if row==None:
            row = self.currentrow
        x1,y1,x2,y2 = self.getCellCoords(row,0)
        x2 = self.tablewidth
        rect = self.create_rectangle(x1,y1,x2,y2,
                                  fill=self.rowselectedcolor,
                                  outline=self.rowselectedcolor,
                                  tag='rowrect')
        self.lower('rowrect')
        self.lower('fillrect')
        self.tablerowheader.drawSelectedRows(self.currentrow)
        return

    def rowUpdate(self):
        if self.rowUpdateRequired:
            self.rowUpdateRequired = False
            self.resetToMinRowHeight = False
            self.setRowPositions()
            self.redrawTable()
            if self.find_withtag('rowrect') != ():
                self.drawSelectedRow(self.currentrow)
        return
    
    def requireRowHeightReset(self):
        self.resetToMinRowHeight = True
        self.rowUpdateRequired = True
        self.minrowheights.clear()
        self.model.rowheights.clear()
        return

    def drawSelectedCol(self, col=None, delete=1):
        """Draw an outline rect for the current column selection"""

        if delete == 1:
            self.delete('colrect')
        if col == None:
            col=self.currentcol
        w=2
        x1,y1,x2,y2 = self.getCellCoords(0,col)
        y2 = self.tableheight
        rect = self.create_rectangle(x1+w/2,y1+w/2,x2,y2+w/2,
                                     outline='blue',width=w,
                                     tag='colrect')
        return

    def drawMultipleRows(self, rowlist):
        """Draw more than one row selection"""

        self.delete('multiplesel')
        for r in rowlist:
            if r not in self.visiblerows or r > self.rows-1:
                continue
            x1,y1,x2,y2 = self.getCellCoords(r,0)
            x2 = self.tablewidth
            rect = self.create_rectangle(x1,y1,x2,y2,
                                      fill=self.multipleselectioncolor,
                                      outline=self.rowselectedcolor,
                                      tag=('multiplesel','rowrect'))
        self.lower('multiplesel')
        self.lower('fillrect')
        return

    def drawMultipleCells(self):
        """Draw an outline box for multiple cell selection"""

        self.delete('multicellrect')
        rows = self.multiplerowlist
        cols = self.multiplecollist
        w=2
        x1,y1,a,b = self.getCellCoords(rows[0],cols[0])
        c,d,x2,y2 = self.getCellCoords(rows[len(rows)-1],cols[len(cols)-1])
        rect = self.create_rectangle(x1+w/2,y1+w/2,x2,y2,
                             outline='blue',width=w,activefill='red',activestipple='gray25',
                             tag='multicellrect')

        return

    def drawTooltip(self, row, col):
        """Draw a tooltip showing contents of cell"""

        if not self.columnTooltipEnable[self.model.columnNames[col]]:
            return
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        w=x2-x1
        text = self.model.getValueAt(row,col)
        if isinstance(text, dict):
            if 'link' in text:
                text = text['link']

        # If text is a number we make it a string
        if type(text) is float or type is int:
            text = str(text)
        if text == None or text == '' or len(str(text))<=10:
            return

        sfont = font.Font(family='Arial', size=12,weight='bold')
        obj = self.create_text(x1+w/1.5,y2,text=text,
                                anchor='w',
                                font=sfont,tag='tooltip')

        box = self.bbox(obj)
        x1=box[0]-1
        y1=box[1]-1
        x2=box[2]+1
        y2=box[3]+1

        rect = self.create_rectangle(x1+1,y1+1,x2+1,y2+1,tag='tooltip',fill='black')
        rect2 = self.create_rectangle(x1,y1,x2,y2,tag='tooltip',fill='lightyellow')
        self.lift(obj)
        return

    def setbgcolor(self):
        clr = self.getaColor(self.bgcolor)
        if clr != None:
            self.bgcolor = clr
        return

    def setgrid_color(self):
        clr = self.getaColor(self.grid_color)
        if clr != None:
            self.grid_color = clr

        return

    def setrowselectedcolor(self):
        clr = self.getaColor(self.rowselectedcolor)
        if clr != None:
            self.rowselectedcolor = clr
        return

    def getaColor(self, oldcolor):

        ctuple, newcolor = tkColorChooser.askcolor(title='pick a color', initialcolor=oldcolor,
                                                   parent=self.parentframe)
        if ctuple == None:
            return None
        return str(newcolor)

    #--- Preferences stuff ---

    def showtablePrefs(self, prefs=None):
        """Show table options dialog using an instance of prefs"""
        #self.prefs = prefs
        if self.prefs == None:
            self.loadPrefs()
        self.prefswindow=Toplevel()
        x,y,w,h = self.getGeometry(self.master)
        self.prefswindow.geometry('+%s+%s' %(int(x+w/2),int(y+h/2)))
        self.prefswindow.title('Preferences')
        self.prefswindow.resizable(width=FALSE, height=FALSE)

        frame1=Frame(self.prefswindow)
        frame1.pack(side=LEFT)
        frame2=Frame(self.prefswindow)
        frame2.pack()
        def close_prefsdialog():
            self.prefswindow.destroy()
        row=0
        Checkbutton(frame1, text="Show horizontal lines", variable=self.horizlinesvar,
                    onvalue=1, offvalue=0).grid(row=row,column=0, columnspan=2, sticky='news')
        row=row+1
        Checkbutton(frame1, text="Show vertical lines", variable=self.vertlinesvar,
                    onvalue=1, offvalue=0).grid(row=row,column=0, columnspan=2, sticky='news')
        row=row+1
        Checkbutton(frame1, text="Alternate Row Color", variable=self.alternaterowsvar,
                    onvalue=1, offvalue=0).grid(row=row,column=0, columnspan=2, sticky='news')
        row=row+1
        lblrowheight = Label(frame1,text='Row Height:')
        lblrowheight.grid(row=row,column=0,padx=3,pady=2)
        rowheightentry = Spinbox(frame1,from_=12,to=50,width=10,
                            textvariable=self.rowheightvar)
        rowheightentry.grid(row=row,column=1,padx=3,pady=2)
        row=row+1
        lblcellwidth = Label(frame1,text='Cell Width:')
        lblcellwidth.grid(row=row,column=0,padx=3,pady=2)
        cellwidthentry = Spinbox(frame1,from_=20,to=500, width=10,
                             textvariable=self.cellwidthvar)
        cellwidthentry.grid(row=row,column=1,padx=3,pady=2)
        row=row+1

        lbllinewidth = Label(frame1,text='Line Width:')
        lbllinewidth.grid(row=row,column=0,padx=3,pady=2)
        linewidthentry = Spinbox(frame1,from_=0,to=10,width=10,
                            textvariable=self.linewidthvar)
        linewidthentry.grid(row=row,column=1,padx=3,pady=2)
        row=row+1

        rowhdrwidth = Label(frame1,text='Row Header Width:')
        rowhdrwidth.grid(row=row,column=0,padx=3,pady=2)
        rowhdrentry = Spinbox(frame1,from_=0,to=300, width=10,
                            textvariable=self.rowheaderwidthvar)
        rowhdrentry.grid(row=row,column=1,padx=3,pady=2)
        row=row+1

        #fonts
        fts = self.getFonts()
        self.fontvar = StringVar()
        self.fontvar.set(self.prefs.get('celltextfont'))
        def setFont(*args):
            self.thefont = self.fontvar.get()
            return

        self.fontbox = Combobox(frame2,
                        values=(fts),
                        text='Font:',
                        height = 6,
                        textvariable=self.fontvar)
        self.fontvar.trace('w', setFont)
        Label(frame2,text='Font:').grid(row=row,column=0,padx=3,pady=2)
        self.fontbox.grid(row=row,column=1, columnspan=2, sticky='nes', padx=3,pady=2)
        row=row+1

        lblfontsize=Label(frame2,text='Text Size:')
        lblfontsize.grid(row=row,column=0,padx=3,pady=2)
        fontsizeentry = Spinbox(frame2,from_=6,to=50, width=20,
                                textvariable=self.celltextsizevar)

        fontsizeentry.grid(row=row,column=1, sticky='wens',padx=3,pady=2)
        row=row+1

        #cell alignment
        lbl=Label(frame2,text='Alignment:')
        lbl.grid(row=row,column=0,padx=3,pady=2)
        alignentry_button = Menubutton(frame2,textvariable=self.cellalignvar, width=16)
        alignentry_menu = Menu(alignentry_button,tearoff=0)
        alignentry_button['menu'] = alignentry_menu
        alignments=['w','e','center']
        for text in alignments:
            alignentry_menu.add_radiobutton(label=text,
                                            variable=self.cellalignvar,
                                            value=text,
                                            indicatoron=1)
        alignentry_button.grid(row=row,column=1, sticky='nes', padx=3,pady=2)
        row=row+1

        #colors
        style = Style()
        style.configure("cb.TButton", background=self.bgcolor)
        bgcolorbutton = Button(frame2, text='table background', style="cb.TButton", #bg=self.bgcolor,
                                 command=self.setbgcolor)
        bgcolorbutton.grid(row=row,column=0,columnspan=2, sticky='news',padx=3,pady=2)
        row=row+1
        style = Style()
        style.configure("gc.TButton", background=self.grid_color)
        grid_colorbutton = Button(frame2, text='grid color',  style="gc.TButton", #bg=self.grid_color,
                                 command=self.setgrid_color)
        grid_colorbutton.grid(row=row,column=0,columnspan=2,  sticky='news',padx=3,pady=2)
        row=row+1
        style = Style()
        style.configure("rhc.TButton", background=self.rowselectedcolor)
        rowselectedcolorbutton = Button(frame2, text='row highlight color', style="rhc.TButton",
                                 command=self.setrowselectedcolor)
        rowselectedcolorbutton.grid(row=row,column=0,columnspan=2,  sticky='news',padx=3,pady=2)
        row=row+1

        frame=Frame(self.prefswindow)
        frame.pack()
        # Apply Button
        b = Button(frame, text="Apply Settings", command=self.applyPrefs)
        b.grid(row=row,column=1,columnspan=2,sticky='news',padx=4,pady=4)

        # Close button
        c=Button(frame,text='Close', command=close_prefsdialog)
        c.grid(row=row,column=0,sticky='news',padx=4,pady=4)
        self.prefswindow.focus_set()
        self.prefswindow.grab_set()
        self.prefswindow.wait_window()
        return self.prefswindow

    def getFonts(self):
        fonts = set(list(font.families()))
        fonts = sorted(list(fonts))
        return fonts

    def loadPrefs(self, prefs=None):
        """Load table specific prefs from the prefs instance used
           if they are not present, create them."""

        if prefs == None:
            prefs=Preferences('Table',{'check_for_update':1})
        self.prefs = prefs
        defaultprefs = {'horizlines':self.horizlines, 'vertlines':self.vertlines,
                        'alternaterows':self.alternaterows,
                        'rowheight':self.rowheight,
                        'cellwidth':100,
                        'autoresizecols': 0,
                        'align': 'w',
                        'celltextsize':11, 'celltextfont':'Arial',
                        'bgcolor': self.bgcolor, 'grid_color': self.grid_color,
                        'linewidth' : self.linewidth,
                        'rowselectedcolor': self.rowselectedcolor,
                        'rowheaderwidth': self.rowheaderwidth}

        #print (self.prefs.__dict__)
        for prop in defaultprefs:
            if not prop in self.prefs.prefs:
                #print (defaultprefs[prop])
                if defaultprefs[prop] != 'None':
                    self.prefs.set(prop, defaultprefs[prop])

        self.defaultprefs = defaultprefs

        #Create tkvars for dialog
        self.rowheightvar = IntVar()
        self.rowheightvar.set(self.prefs.get('rowheight'))
        self.rowheight = self.rowheightvar.get()
        self.cellwidthvar = IntVar()
        self.cellwidthvar.set(self.prefs.get('cellwidth'))
        self.cellwidth = self.cellwidthvar.get()
        self.cellalignvar = StringVar()
        self.cellalignvar.set(self.prefs.get('align'))
        self.align = self.cellalignvar.get()
        self.linewidthvar = IntVar()
        self.linewidthvar.set(self.prefs.get('linewidth'))
        self.horizlinesvar = IntVar()
        self.horizlinesvar.set(self.prefs.get('horizlines'))
        self.vertlinesvar = IntVar()
        self.vertlinesvar.set(self.prefs.get('vertlines'))
        self.alternaterowsvar = IntVar()
        self.alternaterowsvar.set(self.prefs.get('alternaterows'))
        self.celltextsizevar = IntVar()
        self.celltextsizevar.set(self.prefs.get('celltextsize'))
        self.bgcolor = self.prefs.get('bgcolor')
        self.grid_color = self.prefs.get('grid_color')
        self.rowselectedcolor = self.prefs.get('rowselectedcolor')
        self.fontsize = self.celltextsizevar.get()
        self.thefont = (self.prefs.get('celltextfont'), self.prefs.get('celltextsize'))
        self.rowheaderwidthvar = IntVar()
        self.rowheaderwidthvar.set(self.prefs.get('rowheaderwidth'))
        self.rowheaderwidth = self.rowheaderwidthvar.get()
        return

    def savePrefs(self):
        """Save and set the prefs"""

        try:
            self.prefs.set('horizlines', self.horizlinesvar.get())
            self.horizlines = self.horizlinesvar.get()
            self.prefs.set('vertlines', self.vertlinesvar.get())
            self.vertlines = self.vertlinesvar.get()
            self.prefs.set('alternaterows', self.alternaterowsvar.get())
            self.alternaterows = self.alternaterowsvar.get()
            self.prefs.set('rowheight', self.rowheightvar.get())
            self.rowheight = self.rowheightvar.get()
            self.prefs.set('cellwidth', self.cellwidthvar.get())
            self.cellwidth = self.cellwidthvar.get()
            self.prefs.set('align', self.cellalignvar.get())
            self.align = self.cellalignvar.get()
            self.prefs.set('linewidth', self.linewidthvar.get())
            self.linewidth = self.linewidthvar.get()
            self.prefs.set('celltextsize', self.celltextsizevar.get())
            self.prefs.set('celltextfont', self.fontvar.get())
            self.prefs.set('bgcolor', self.bgcolor)
            self.prefs.set('grid_color', self.grid_color)
            self.prefs.set('rowselectedcolor', self.rowselectedcolor)
            self.prefs.set('rowheaderwidth', self.rowheaderwidth)
            self.rowheaderwidth = self.rowheaderwidthvar.get()
            self.thefont = (self.prefs.get('celltextfont'), self.prefs.get('celltextsize'))
            self.fontsize = self.prefs.get('celltextsize')

        except ValueError as e:
            print (e)
            pass
        self.prefs.save_prefs()
        return

    def applyPrefs(self):
        """Apply prefs to the table by redrawing"""

        self.savePrefs()
        self.redrawTable()
        return

    def AskForColorButton(self, frame, text, func):
        def SetColor():
            ctuple, variable = tkColorChooser.askcolor(title='pick a color',
                                                       initialcolor=self.bgcolor)

            return
        bgcolorbutton = Button(frame, text=text,command=SetColor)
        return  bgcolorbutton

    def check_hyperlink(self,event=None):
        """Check if a hyperlink was clicked"""

        row = self.get_row_clicked(event)
        col = self.get_col_clicked(event)
        #absrow = self.get_AbsoluteRow(row)
        recdata = self.model.getValueAt(row, col)
        try:
            link = recdata['link']
            import webbrowser
            webbrowser.open(link,autoraise=1)
        except:
            pass
        return

    def show_progressbar(self,message=None):
        """Show progress bar window for loading of data"""
        progress_win=Toplevel() # Open a new window
        progress_win.title("Please Wait")
        #progress_win.geometry('+%d+%d' %(self.parentframe.rootx+200,self.parentframe.rooty+200))
        #force on top
        progress_win.grab_set()
        progress_win.transient(self.parentframe)
        if message==None:
            message='Working'
        lbl = Label(progress_win,text=message,font='Arial 16')

        lbl.grid(row=0,column=0,columnspan=2,sticky='news',padx=6,pady=4)
        progrlbl = Label(progress_win,text='Progress:')
        progrlbl.grid(row=1,column=0,sticky='news',padx=2,pady=4)
        import ProgressBar
        self.bar = ProgressBar.ProgressBar(progress_win)
        self.bar.frame.grid(row=1,column=1,columnspan=2,padx=2,pady=4)

        return progress_win

    def updateModel(self, model):
        """Call this method to update the table model"""

        self.model = model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()
        self.tablewidth = (self.cellwidth)*self.cols
        self.tablecolheader = ColumnHeader(self.parentframe, self)
        self.tablerowheader = RowHeader(self.parentframe, self)
        self.createTableFrame()
        return

    def new(self):
        """Clears all the data and makes a new table"""

        mpDlg = MultipleValDialog(title='Create new table',
                                    initialvalues=(10, 4),
                                    labels=('rows','columns'),
                                    types=('int','int'),
                                    parent=self.parentframe)

        if mpDlg.result == True:
            rows = mpDlg.results[0]
            cols = mpDlg.results[1]
            model = TableModel(rows=rows,columns=cols)
            self.updateModel(model)
        return

    def load(self, filename=None):
        """load from a file"""

        if filename == None:
            filename = filedialog.askopenfilename(parent=self.master,
                                                      defaultextension='.table',
                                                      initialdir=os.getcwd(),
                                                      filetypes=[("pickle","*.table"),
                                                        ("All files","*.*")])
        if not os.path.exists(filename):
            print ('file does not exist')
            return
        if filename:
            self.model.load(filename)
            self.redrawTable()
        return

    def save(self, filename=None):
        """Save model to pickle file"""

        if filename == None:
            filename = filedialog.asksaveasfilename(parent=self.master,
                                                        defaultextension='.table',
                                                        initialdir=os.getcwd(),
                                                        filetypes=[("pickle","*.table"),
                                                          ("All files","*.*")])
        if filename:
            self.model.save(filename)
        return

    def importTable(self):
        self.importCSV()

    def importCSV(self, filename=None, sep=','):
        """Import from csv file"""

        if filename is None:
            from .Tables_IO import TableImporter
            importer = TableImporter()
            importdialog = importer.import_Dialog(self.master)
            self.master.wait_window(importdialog)
            model = TableModel()
            model.importDict(importer.data)
        else:
            model = TableModel()
            model.importCSV(filename, sep=sep)
        self.updateModel(model)
        return

    def exportTable(self, filename=None):
        """Do a simple export of the cell contents to csv"""

        from .Tables_IO import TableExporter
        exporter = TableExporter()
        exporter.ExportTableData(self)
        return

    @classmethod
    def checkOSType(cls):
        """Check the OS we are in"""

        ostyp=''
        var_s=['OSTYPE','OS']
        for var in var_s:
            if var in os.environ:
                try:
                    ostyp = str.lower(os.environ[var])
                except:
                    ostyp = os.environ[var].lower()

        ostyp=ostyp.lower()
        if ostyp.find('windows')!=-1:
            ostyp='windows'
        elif ostyp.find('darwin')!=-1 or ostyp.find('apple')!=-1:
            ostyp='mac'
        elif ostyp.find('linux')!=-1:
            ostyp='linux'
        else:
            ostyp='unknown'
            try:
                info=os.uname()
            except:
                pass
            ostyp=info[0].lower()
            if ostyp.find('darwin')!=-1:
                ostyp='mac'
        return ostyp

    def getGeometry(self, frame):
        """Get frame geometry"""
        return frame.winfo_rootx(), frame.winfo_rooty(), frame.winfo_width(), frame.winfo_height()
    
    @staticmethod
    def within(val, l, d):
        """Utility funtion to see if val is within d of any
            items in the list l"""
        for idx, v in enumerate(l):
            if abs(val-v) <= d:
                return idx
        return -1

class ColumnHeader(Canvas):
    """Class that takes it's size and rendering from a parent table
        and column names from the table model."""

    def __init__(self, parent=None, table=None):
        Canvas.__init__(self, parent, bg='gray25', width=500, height=20)
        self.thefont='Arial 14'
        self.atdivider = -1

        if table != None:
            self.table = table
            self.height = 20
            self.model = self.table.getModel()
            self.config(width=self.table.width)
            #self.colnames = self.model.columnNames
            self.columnlabels = self.model.columnlabels
            self.bind('<Button-1>',self.handle_left_click)
            self.bind("<ButtonRelease-1>", self.handle_left_release)
            self.bind('<B1-Motion>', self.handle_mouse_drag)
            self.bind('<Motion>', self.handle_mouse_move)
            self.bind('<Shift-Button-1>', self.handle_left_shift_click)
            if self.table.ostyp=='mac':
                #For mac we bind Shift, left-click to right click
                self.bind("<Button-2>", self.handle_right_click)
                self.bind('<Shift-Button-1>',self.handle_right_click)
            else:
                self.bind("<Button-3>", self.handle_right_click)
            self.thefont = self.table.thefont
        return

    def redraw(self):

        cols = self.model.getColumnCount()
        self.tablewidth=self.table.tablewidth
        self.configure(scrollregion=(0,0, self.table.tablewidth+self.table.x_start, self.height))
        self.delete('gridline','text')
        self.delete('rect')
        self.atdivider = -1
        align='w'
        pad=4
        h=self.height
        #x_start=self.table.x_start

        if cols == 0:
            return
        for col in self.table.visiblecols:
            colname = self.model.columnNames[col]
            if not colname in self.model.columnlabels:
                self.model.columnlabels[colname]=colname
            collabel = self.model.columnlabels[colname]
            if colname in self.model.columnwidths:
                w = self.model.columnwidths[colname]
            else:
                w = self.table.cellwidth
            x = self.table.col_positions[col]

            if len(collabel)>w/10:
                collabel = collabel[0:int(w/12)]+'.'
            line = self.create_line(x, 0, x, h, tag=('gridline', 'vertline'),
                                 fill='white', width=2)

            self.create_text(x+pad,h/2,
                            text=collabel,
                            anchor=align,
                            fill='white',
                            font=self.thefont,
                            tag='text')


        x=self.table.col_positions[col+1]
        self.create_line(x,0, x,h, tag='gridline',
                        fill='white', width=2)

        return

    def handle_left_click(self,event):
        """Does cell selection when mouse is clicked on canvas"""

        self.delete('rect')
        self.table.delete('entry')
        self.table.delete('multicellrect')
        colclicked = self.table.get_col_clicked(event)
        if colclicked == None:
            return
        #set all rows selected
        self.table.allrows = True
        self.table.setSelectedCol(colclicked)

        if self.atdivider >= 0:
            return
        self.drawRect(self.table.currentcol)
        #also draw a copy of the rect to be dragged
        self.draggedcol = None
        self.drawRect(self.table.currentcol, tag='dragrect',
                        color='red', outline='white')
        if hasattr(self, 'rightmenu'):
            self.rightmenu.destroy()
        #finally, draw the selected col on the table
        self.table.drawSelectedCol()
        return

    def handle_left_release(self,event):
        """When mouse released implement resize or col move"""

        self.delete('dragrect')
        if self.atdivider >= 0:
            x=int(self.canvasx(event.x))
            #col = self.table.get_col_clicked(event)
            #col = self.table.currentcol
            col = self.atdivider
            x1,y1,x2,y2 = self.table.getCellCoords(0,col)
            newwidth = x-x1
            if newwidth < self.table.mincellwidth:
                newwidth = self.table.mincellwidth
            maxcellwidth = self.table.maxcellwidth[self.table.model.getColumnName(col)]
            if newwidth > maxcellwidth:
                newwidth = maxcellwidth
            self.table.resizeColumn(col, newwidth)
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.delete('resizesymbol')
            self.atdivider = -1
            return
        self.delete('resizesymbol')
        #move column
        if self.draggedcol != None and self.table.currentcol != self.draggedcol:
            self.model.moveColumn(self.table.currentcol, self.draggedcol)
            self.table.setSelectedCol(self.draggedcol)
            self.table.redrawTable()
            self.table.drawSelectedCol(self.table.currentcol)
            self.drawRect(self.table.currentcol)
        return

    def handle_mouse_drag(self, event):
        """Handle column drag, will be either to move cols or resize"""

        x=int(self.canvasx(event.x))
        if self.atdivider >= 0:
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.table.create_line(x, 0, x, self.table.rowheight*self.table.rows,
                                width=2, fill='gray', tag='resizeline')
            self.create_line(x, 0, x, self.height,
                                width=2, fill='gray', tag='resizeline')
            return
        else:
            w = self.table.cellwidth
            self.draggedcol = self.table.get_col_clicked(event)
            x1, y1, x2, y2 = self.coords('dragrect')
            x=int(self.canvasx(event.x))
            y = self.canvasy(event.y)
            self.move('dragrect', x-x1-w/2, 0)

        return

    # def within(self, val, l, d):
    #     """Utility funtion to see if val is within d of any
    #         items in the list l"""
    #     for v in l:
    #         if abs(val-v) <= d:
    #             return 1
    #     return 0
    

    def handle_mouse_move(self, event):
        """Handle mouse moved in header, if near divider draw resize symbol"""

        self.delete('resizesymbol')
        w=self.table.cellwidth
        h=self.height
        x_start=self.table.x_start
        #x = event.x
        x=int(self.canvasx(event.x))
        if x > self.table.tablewidth+w:
            return
        
        #if event x is within x pixels of divider, draw resize symbol
        if x!=x_start:
            divider_idx = self.table.within(x, self.table.col_positions, 2)
            if divider_idx > 0:
                self.draw_resize_symbol(divider_idx-1)
                self.atdivider = divider_idx-1
                return

        self.atdivider = -1
        return

    def handle_right_click(self, event):
        """respond to a right click"""

        self.handle_left_click(event)
        if self.table.show_popup == True:
            pm = self.popupMenu(event)
            if pm is not None:
                self.rightmenu = pm
        return

    def handle_right_release(self, event):
        self.rightmenu.destroy()
        return

    def handle_left_shift_click(self, event):
        """Handle shift click, for selecting multiple cols"""

        self.table.delete('colrect')
        self.delete('rect')
        currcol = self.table.currentcol
        colclicked = self.table.get_col_clicked(event)
        if colclicked > currcol:
            self.table.multiplecollist = range(currcol, colclicked+1)
        elif colclicked < currcol:
            self.table.multiplecollist = range(colclicked, currcol+1)
        else:
            return

        #print self.table.multiplecollist
        for c in self.table.multiplecollist:
            self.drawRect(c, delete=0)
            self.table.drawSelectedCol(c, delete=0)
        return

    def popupMenu(self, event):
        """Add left and right click behaviour for column header"""

        colname = self.model.columnNames[self.table.currentcol]
        collabel = self.model.columnlabels[colname]
        currcol = self.table.currentcol
        popupmenu = Menu(self, tearoff = 0)
        def popupFocusOut(event):
            popupmenu.unpost()
        any = False
        if self.table.showPopupMenuEntry["Rename Column"]:
            popupmenu.add_command(label="Rename Column", command=self.relabel_Column)
            any = True
        if self.table.showPopupMenuEntry["Sort by"]:
            popupmenu.add_command(label="Sort by "+ collabel, command=lambda : self.table.sortTable(currcol))
            popupmenu.add_command(label="Sort by "+ collabel +' (descending)', command=lambda : self.table.sortTable(currcol,reverse=1))
            any = True
        if self.table.showPopupMenuEntry["Delete This Column"]:
            popupmenu.add_command(label="Delete This Column", command=self.table.deleteColumn)
            any = True
        if self.table.showPopupMenuEntry["Add New Column"]:
            popupmenu.add_command(label="Add New Column", command=self.table.addColumn)
            any = True
        if not any:
            return None

        popupmenu.bind("<FocusOut>", popupFocusOut)
        #self.bind("<Button-3>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        return popupmenu

    def relabel_Column(self):
        col=self.table.currentcol
        ans = simpledialog.askstring("New column name?", "Enter new name:")
        if ans !=None:
            if ans == '':
                messagebox.showwarning("Error", "Name should not be blank.")
                return
            else:
                self.model.relabel_Column(col, ans)
                self.redraw()
        return

    def draw_resize_symbol(self, col):
        """Draw a symbol to show that col can be resized when mouse here"""

        self.delete('resizesymbol')
        w=self.table.cellwidth
        h=self.height
        wdth=1
        hfac1=0.2
        hfac2=0.4
        x_start=self.table.x_start
        x1,y1,x2,y2 = self.table.getCellCoords(0,col)

        self.create_polygon(x2-3,h/4, x2-10,h/2, x2-3,h*3/4, tag='resizesymbol',
            fill='white', outline='gray', width=wdth)
        self.create_polygon(x2+2,h/4, x2+10,h/2, x2+2,h*3/4, tag='resizesymbol',
            fill='white', outline='gray', width=wdth)
        return

    def drawRect(self,col, tag=None, color=None, outline=None, delete=1):
        """User has clicked to select a col"""

        if tag==None:
            tag='rect'
        if color==None:
            color='#0099CC'
        if outline==None:
            outline='gray25'
        if delete == 1:
            self.delete(tag)
        w=2
        x1,y1,x2,y2 = self.table.getCellCoords(0,col)
        rect = self.create_rectangle(x1,y1-w,x2,self.height,
                                  fill=color,
                                  outline=outline,
                                  width=w,
                                  stipple='gray50',
                                  tag=tag)
        self.lower(tag)
        return

class RowHeader(Canvas):
    """Class that displays the row headings on the table
       takes it's size and rendering from the parent table
       This also handles row/record selection as opposed to cell
       selection"""

    def __init__(self, parent=None, table=None, width=40):
        Canvas.__init__(self, parent, bg='gray75', width=width, height=None)
        self.atrowdivider = -1

        if table != None:
            self.table = table
            self.width = width
            self.x_start = 0
            self.inset = 1
            self.config(height = self.table.height)
            self.startrow = self.endrow = None
            self.model = self.table.getModel()
            self.bind('<Button-1>',self.handle_left_click)
            self.bind("<ButtonRelease-1>", self.handle_left_release)
            self.bind("<Control-Button-1>", self.handle_left_ctrl_click)
            self.bind('<Button-3>',self.handle_right_click)
            self.bind('<B1-Motion>', self.handle_mouse_drag)
            self.bind('<Motion>', self.handle_mouse_move)
            #self.bind('<Shift-Button-1>', self.handle_left_shift_click)
        return

    def redraw(self, align='w', showkeys=False):
        """Redraw row header"""

        rows = self.model.getRowCount()
        self.height = self.table.tableheight #+10 ??
        self.configure(scrollregion=(0,0, self.width, self.height))
        self.delete('rowheader','text')
        self.delete('rect')
        w = float(self.width)
        x = self.x_start+w/2
        if align == 'w':
            x = x-w/2+3
        elif align == 'e':
            x = x+w/2-3
        if rows == 0:
            return
        for row in self.table.visiblerows:
            if showkeys == True:
                text = self.model.getRecName(row)
            else:
                text = row+1
            x1,y1,x2,y2 = self.table.getCellCoords(row,0)
            if row in self.model.rowheights:
                h = self.model.rowheights[row]
            else:
                h = self.table.rowheight
            self.create_rectangle(0,y1,w-1,y2,
                                      fill='gray75',
                                      outline='white',
                                      width=1,
                                      tag='rowheader')
            self.create_text(x,y1+h/2,
                                      text=text,
                                      fill='black',
                                      font=self.table.thefont,
                                      tag='text', anchor=align)
        return

    def setWidth(self, w):
        """Set width"""
        self.width = w
        self.redraw()
        return

    def clearSelected(self):
        self.delete('rect')
        return

    def handle_left_click(self, event):
        rowclicked = self.table.get_row_clicked(event)
        self.startrow = rowclicked
        if 0 <= rowclicked < self.table.rows:
            self.delete('rect')
            self.table.delete('entry')
            self.table.delete('multicellrect')
            #set row selected
            self.table.setSelectedRow(rowclicked)
            self.table.drawSelectedRow()
            self.drawSelectedRows(self.table.currentrow)
        return

    def handle_left_release(self,event):
        """When mouse released implement resize"""

        self.delete('dragrect')
        if self.atrowdivider >= 0:
            y=int(self.canvasy(event.y))
            #col = self.table.get_col_clicked(event)
            #col = self.table.currentcol
            row = self.atrowdivider
            x1,y1,x2,y2 = self.table.getCellCoords(row, 0)
            newheight= y-y1
            self.table.resizeRow(row, newheight) # may use larger newheight if newheight < minrowheight
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.delete('resizesymbol')
            self.atrowdivider = -1
            return
        self.delete('resizesymbol')
        return

    def handle_left_ctrl_click(self, event):
        """Handle ctrl clicks - for multiple row selections"""

        rowclicked = self.table.get_row_clicked(event)
        multirowlist = self.table.multiplerowlist
        if 0 <= rowclicked < self.table.rows:
            if rowclicked not in multirowlist:
                multirowlist.append(rowclicked)
            else:
                multirowlist.remove(rowclicked)
            self.table.drawMultipleRows(multirowlist)
            self.drawSelectedRows(multirowlist)
        return

    def handle_right_click(self,event):

        return

    def handle_mouse_drag(self, event):
        """Handle mouse moved with button held down, for either row resize or multirow selection"""

        if self.atrowdivider >= 0:
            y=int(self.canvasy(event.y))
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.table.create_line(0, y, self.table.tableheight, y, 
                                width=2, fill='gray', tag='resizeline')
            self.create_line(0, y, self.width, y,
                                width=2, fill='gray', tag='resizeline')
            return
        else:
            if hasattr(self, 'cellentry'):
                self.cellentry.destroy()
            rowover = self.table.get_row_clicked(event)
            colover = self.table.get_col_clicked(event)
            if rowover == None:
                return
            if rowover >= self.table.rows or self.startrow > self.table.rows:
                return
            else:
                self.endrow = rowover
            #draw the selected rows
            if self.endrow != self.startrow:
                if self.endrow < self.startrow:
                    rowlist=range(self.endrow, self.startrow+1)
                else:
                    rowlist=range(self.startrow, self.endrow+1)
                self.drawSelectedRows(rowlist)
                self.table.multiplerowlist = rowlist
                self.table.drawMultipleRows(rowlist)
            else:
                self.table.multiplerowlist = []
                self.table.multiplerowlist.append(rowover)
                self.drawSelectedRows(rowover)
                self.table.drawMultipleRows(self.table.multiplerowlist)
            return

    def handle_mouse_move(self, event):
        """Handle mouse moved in header, if near divider draw resize symbol"""

        self.delete('resizesymbol')
        h=self.height
        y_start=self.table.y_start
        y=int(self.canvasy(event.y))
        if y > self.table.tableheight+h:
            return
        
        #if event y is within y pixels of divider, draw resize symbol
        if y!=y_start:
            divider_idx = self.table.within(y, self.table.row_positions, 1)
            if divider_idx > 0:
                self.draw_row_resize_symbol(divider_idx-1)
                self.atrowdivider = divider_idx-1
                return

        self.atrowdivider = -1
        return

    def drawSelectedRows(self, rows=None):
        """Draw selected rows, accepts a list or integer"""

        self.delete('rect')
        if type(rows) is not list:
            rowlist=[]
            rowlist.append(rows)
        else:
           rowlist = rows
        for r in rowlist:
            if r not in self.table.visiblerows:
                continue
            self.drawRect(r, delete=0)
        return

    def draw_row_resize_symbol(self, row):
        """Draw a symbol to show that row can be resized when mouse here"""

        self.delete('resizesymbol')
        w=self.width
        wdth=1
        hfac1=0.2
        hfac2=0.4
        x_start=self.table.x_start
        x1,y1,x2,y2 = self.table.getCellCoords(row,0)

        self.create_polygon(w/2-6,y2-3, w/2,y2-9, w/2+6,y2-3, tag='resizesymbol',
            fill='white', outline='gray', width=wdth)
        self.create_polygon(w/2-6,y2+2, w/2,y2+8, w/2+6,y2+2, tag='resizesymbol',
            fill='white', outline='gray', width=wdth)

    def drawRect(self, row=None, tag=None, color=None, outline=None, delete=1):
        """Draw a rect representing row selection"""

        if tag==None:
            tag='rect'
        if color==None:
            color='#0099CC'
        if outline==None:
            outline='gray25'
        if delete == 1:
            self.delete(tag)
        w=0
        i = self.inset
        x1,y1,x2,y2 = self.table.getCellCoords(row, 0)
        rect = self.create_rectangle(0+i,y1+i,self.width-i,y2,
                                      fill=color,
                                      outline=outline,
                                      width=w,
                                      tag=tag)
        self.lift('text')
        return

class AutoScrollbar(Scrollbar):
    """a scrollbar that hides itself if it's not needed.  only
       works if you use the grid geometry manager."""

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    #def pack(self, **kw):
    #    raise TclError, "cannot use pack with this widget"
    #def place(self, **kw):
    #    raise TclError, "cannot use place with this widget"
