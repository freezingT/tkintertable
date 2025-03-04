from .FilterDialog import FilterDialog
from .FilterDialogFactoryInterface import FilterDialogFactoryInterface as FDFI

from tkinter import Toplevel
import tkinter as tk


class FilterDialogFactory(FDFI):
    def __init__(self):
        self.callback_doFilter = None
        self.callback_showAll = None
        
        self.__geometry = None # (x,y,w,h)
        self.__fields = None

        self.filterwin = None
        return

    def subscribe(self, doFilter, showAll):
        self.callback_doFilter = doFilter
        self.callback_showAll = showAll
        return

    def createFilteringDialog(self, parent: tk.Tk, fields: list[str]):        
        """
        Create and show new Filtering Dialog
        Args:
            parent: the parent Frame (to get the geometry)
            fields: the names of the fields to show (column names in which a filter can be applied)
        """

        noExistentWindow = not hasattr(self, 'filterwin') or self.filterwin == None
        if not noExistentWindow and self.__fields != fields: # close the existing window if the fields are no longer the same
            self.__closeFilterFrame()
            noExistentWindow = True

        if noExistentWindow:
            self.__getGeometry(parent) # get current geometry of the parent frame
            self.__fields = fields
            self.filterwin = self.__createFilteringBar()
            self.filterwin.protocol("WM_DELETE_WINDOW", self.__closeFilterFrame)
        else:
            self.filterwin.lift()
        return
        

    def __createToplevelWindow(self):
        window = Toplevel()
        window.title('Filter Records')
        x,y,w,h = self.__geometry
        window.geometry('+%s+%s' %(x,y+h))
        return window

    def __createFilteringBar(self):
        """Add a filter frame"""

        window = self.__createToplevelWindow()

        if self.callback_doFilter is None:
            raise RuntimeError("Subscribe the FilterDialogFactory first to provide a callback method called to trigger the filtering.")
        filterdialog = FilterDialog(window, fields=self.__fields, callback=self.callback_doFilter, closecallback=self.__closeFilterFrame)
        filterdialog.pack()
        return window    

    def __getGeometry(self, parent):
        self.__geometry = parent.getGeometry(parent.master)
        return
        
    def __closeFilterFrame(self):
        """Callback for closing filter frame"""
        self.filterwin.destroy()
        self.filterwin = None
        if self.callback_showAll is not None:
            self.callback_showAll()
        return