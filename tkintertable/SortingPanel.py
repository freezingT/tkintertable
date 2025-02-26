try:
    import tkinter as tk # type: ignore
    from tkinter import Menubutton, Menu, Canvas # type: ignore
except:
    import Tkinter as tk # type: ignore
    from Tkinter import Menubutton, Menu, Canvas # type: ignore

try:
    from customtkinter import CTkFrame as Frame
except:
    Frame = tk.Frame

from bisect import bisect
from functools import partial
import math

class SortingBarMoveManager:
    '''Contains information required for dragging/moving SortingBars'''

    def __init__(self, columnIndex: int, widths: list[int], positionIndex: int, barDistance:int=0):
        '''
        Create new SortingBarMoveManager
        Args:
            columnIndex     : the index of the associated column
            widths          : list of widths of all sortingBars, in the current order of the sorting bars
            positionIndex   : the current position of the associated column bar
            barDistance     : the distance between SortingBars (2*padx in the pack manager)
        '''
        self._accumWidths = self._createCumsum(widths, barDistance)
        self._sbColumnIndex = columnIndex
        self._posIndex = positionIndex
        self._poscorrection = 0
        return

    def getOrderChanged(self, dx):
        '''Return 0 if order did not change, <0 if moved to left and >0 if moved to right.'''
        x = dx + self._accumWidths[self._posIndex] # dx + pos
        newIdx = self._computeNewIdx(x, dx)
        return newIdx - self._posIndex

    def performOrderChange(self, diff):
        '''Update internal data after an order change to keep track of the right order.'''
        newIdx = self._posIndex + diff
        self._poscorrection = self._accumWidths[newIdx] - self._accumWidths[self._posIndex]
        while diff != 0:
            self._switchWidthOrder(int(min(self._posIndex, self._posIndex+diff)))
            diff -= math.copysign(1, diff)
        self._posIndex = newIdx
        return

    def getColumnIndex(self):
        return self._sbColumnIndex

    def _switchWidthOrder(self, i):
        '''Switch the accumWidths array to give accumulated widths for switched width[i] <-> width[i+1]'''
        wi = self._accumWidths[i+2] - self._accumWidths[i+1]
        self._accumWidths[i+1] = self._accumWidths[i] + wi
        return 

    def _computeNewIdx(self, x, dx):
        if dx < 0:
            for i, w in enumerate(self._accumWidths):
                if x < w:
                    return i
        elif dx > 0:
            length = len(self._accumWidths)
            for j, w in enumerate(reversed(self._accumWidths), start=1):
                i = length - j
                if x > w:
                    if i == length-1:
                        return i-1 # restrict to largest index
                    else:
                        return i # "normal" case
        else:
            return self._posIndex

    @staticmethod
    def _createCumsum(A, bdist):
        s = 0
        cA = [s]
        for a in A:
            s += a+bdist
            cA.append(s)
        return cA


class SortingFrame(Frame):
    """Base class for the panel that enables sorting the Table."""
    def __init__(self, parent: tk.Tk, fields: list[str], callback=None):
        """
        Create gui frame for sorting
        Args:
            parent:     parent widget
            fields:     list of column names
            callback:   function that gets called when a sort is triggered. It is called with one argument, providing the sort specification in the following format:
                        [(key0_colname, key0_isReversed), (key1_colname, key1_isReversed), ...]
        """
        Frame.__init__(self, parent)

        self._fields = fields
        self._sortCallback = callback

        self._outerframe = Frame(self, height=30)
        self._outerframe.pack(side=tk.LEFT, fill="x", expand=True, padx=2, pady=2)

        #self._add_button = OptionMenu(self, values=['Option 1', 'Option 2', 'Option 3'], command=self.addNewSortingBar, width=10)
        self._add_button = Menubutton(self, text="+")
        self._add_button.pack(side=tk.LEFT, fill="none", expand=False, padx=2, pady=2)
        self._add_button.menu = Menu(self._add_button, tearoff=0)
        self._add_button["menu"]= self._add_button.menu 
        for i in range(len(fields)):
            self._add_button.menu.add_command(label=fields[i], command=partial(self.addSortingBarToPanel, i))

        self._sortingBars = [] # list of SortingBar objects
        self._panelColumnIndexList = [] # column indices in the panel objects
        self._menuColumnIndexList = list(range(len(fields))) # column indices in the MenuItem list
        self._moveManager = None
        self._xpad_bar = 4
        return

    def addSortingBarToPanel(self, column_index):
        '''Create a new sorting item to the panel and trigger the removal of the respective MenuItem'''
        self._deleteButtonMenuItem(column_index)

        thetext = self._fields[column_index]
        sortingBar = SortingBar(self._outerframe, thetext, column_index, deletionCallback=self.deleteSortingBarFromPanel, moveCallback=self._moveCallbackHandle, statusChangedCallback=self._triggerSorting)
        sortingBar.pack(side=tk.LEFT, fill="none", expand=False, padx=self._xpad_bar, pady=4)
        self._sortingBars.append(sortingBar)
        return

    def deleteSortingBarFromPanel(self, column_index):
        '''Remove the SortinBar element at index field_index from the panel and trigger the creation of the respective MenuItem'''
        panelList_index = self._panelColumnIndexList.index(column_index)
        del self._sortingBars[panelList_index]
        self._addButtonMenuItem(column_index)
        self._triggerSorting()
        return

    def _addButtonMenuItem(self, column_index):
        '''Remove an index from the _sortingIndices list, insert it in the sorted _indexList and create the respective menu item in the dropdown menu'''
        if column_index in self._panelColumnIndexList:
            index = bisect(self._menuColumnIndexList, column_index)
            self._add_button.menu.insert_command(index, label=self._fields[column_index], command=partial(self.addSortingBarToPanel, column_index))
            self._menuColumnIndexList.insert(index, column_index)
            self._panelColumnIndexList.remove(column_index)
        return

    def _deleteButtonMenuItem(self, column_index):
        '''Remove an index from the sorted _indexList list, insert it in the _sortingIndices and remove the respective menu item in the dropdown menu'''
        if column_index not in self._panelColumnIndexList:
            index = self._menuColumnIndexList.index(column_index)
            self._add_button.menu.delete(index, index)
            self._menuColumnIndexList.remove(column_index)
            self._panelColumnIndexList.append(column_index)
        return

    def _triggerSorting(self):
        '''Calls the given sort callback with a list of sort specs. Each spec is a tuple of the column name and a "descend"-flag.'''
        specs = []
        for sb in self._sortingBars:
            specs.append((self._fields[sb.getIndex()], sb.getStatus=="descending"))
        self._sortCallback(specs)
        return
    
    def _getAllWidths(self):
        widths = []
        for i, sb in enumerate(self._sortingBars):
            widths.append(sb.getCurrentWidth())
        return widths

    def _moveCallbackHandle(self, status, arg):
        if status == 0:
            widths = self._getAllWidths()
            posIndex = self._panelColumnIndexList.index(arg)
            self._moveManager = SortingBarMoveManager(arg, widths, posIndex, barDistance=2*self._xpad_bar)
        elif self._moveManager is not None:
            if status == 1:
                panelList_index = self._panelColumnIndexList.index(self._moveManager.getColumnIndex())
                orderchange = self._moveManager.getOrderChanged(arg)
                if orderchange != 0:
                    self._moveOrder(orderchange, panelList_index)
                    self._moveManager.performOrderChange(orderchange)
            elif status == 2:
                self._moveManager = None
        return

    def _moveOrder(self, diff, index):
        while diff != 0:
            if diff > 0:
                self._sortingBars[index].forget()
                self._sortingBars[index].pack(after=self._sortingBars[index+1], side=tk.LEFT)
                self._sortingBars[index+1], self._sortingBars[index] = self._sortingBars[index], self._sortingBars[index+1]
                self._panelColumnIndexList[index+1], self._panelColumnIndexList[index] = self._panelColumnIndexList[index], self._panelColumnIndexList[index+1]
                index += 1
                #self._sortingBars[index].setIndex(index)
                diff -= 1
            else: # diff < 0
                self._sortingBars[index].forget()
                self._sortingBars[index].pack(before=self._sortingBars[index-1], side=tk.LEFT)
                self._sortingBars[index-1], self._sortingBars[index] = self._sortingBars[index], self._sortingBars[index-1]
                self._panelColumnIndexList[index-1], self._panelColumnIndexList[index] = self._panelColumnIndexList[index], self._panelColumnIndexList[index-1]
                index -= 1
                #self._sortingBars[index].setIndex(index)
                diff += 1
        return


class SortingBar(Frame):
    def __init__(self, parent, text: str, index: int, maxWidth: int=0, deletionCallback=None, moveCallback=None, statusChangedCallback=None):
        """
        Create a new SortingBar
        Args:
            parent:                 the parent tkinter object
            text:                   the text to be displayed on the SortingBar
            index:                  the index that identifies this SortingBar
            maxWidth:               the maximum width for this element, set to 0 to ignore
            deletionCallback:       called if the SortingBar is deleted, takes one argument: the index that identifies the SortingBar
            moveCallback:           called if the object is moved, takes two arguments:
                                        first: the status, is 0, 1 or 2 
                                        second: argument, depending on status:
                                        | status   | 0                 | 1                           | 2                           |
                                        |----------+-------------------+-----------------------------+-----------------------------|
                                        | meaning  | pressed           | dragged                     | released                    |
                                        | argument | self._index (int) | change in x-direction (int) | change in x-direction (int) |
            statusChangeCallback:   called if the sort direction changes, takes no arguments
        """
        Frame.__init__(self, parent)
        self._loadRessources()

        self._text = text
        self._index = index
        self._cb_move = moveCallback
        self._cb_status = statusChangedCallback
        self._cb_delete = deletionCallback

        self._height = 24
        self._width = 150
        self._isDescending = True
        self._canvas = Canvas(self, width=self._width, height=self._height, bg="white")
        self._createGrabber()
        self._createText(maxWidth)        
        self._createArrow()
        
        self._canvas.pack(side="left")

        self.enforceWidth()
        return

    def getCurrentWidth(self):
        """Get the current total width of the SortingBar"""
        return self._width
    
    def enforceWidth(self, newWidth: int=None):
        """Set a maximal width of the SortingBar to reduce the text width if possible"""
        if newWidth is None:
            newWidth = self.getRequiredWidth()
            self._canvas.configure(width=newWidth)
            dx = newWidth - self._width
            self._canvas.move(self._arrow, dx, 0)
            self._width = newWidth
        else:
            pass
        return
    
    def getRequiredWidth(self):
        """Get the width required to display the full text"""
        return self._textWidth + self._imgAD_width + self._imgG_width + 10

    def getIndex(self):
        return self._index

    def getStatus(self) -> str:
        """Get the current sort direction 'ascending' or 'descending' of the SortingBar"""
        if self._isDescending:
            return "descending"
        else:
            return "ascending"

    def changeStatus(self):
        """Change the status from 'ascending' to 'descending' and vise versa"""
        if self._isDescending:
            self._isDescending = False
            self._canvas.itemconfigure(self._arrow, image=self._imgA)
        else:
            self._isDescending = True
            self._canvas.itemconfigure(self._arrow, image=self._imgD)

        if self._cb_status is not None:
            self._cb_status()
        return
    
    def close(self):
        """Destroy and remove from parent"""
        self._cb_delete(self._index)
        self.destroy()
        return
        
    def _loadRessources(self):
        """Load images"""
        self._imgA = tk.PhotoImage(name="img_ascending", file="gui/assets/ascending.png")
        self._imgD = tk.PhotoImage(name="img_descending", file="gui/assets/descending.png")
        self._imgAD_width = max(self._imgA.width(), self._imgD.width())
        self._imgG = tk.PhotoImage(name="img_grabber", file="gui/assets/grabbing-v2.png")
        self._imgG_width = self._imgG.width()
        return

    def _createGrabber(self):
        """Create the grabber on the left to move the sorting bar"""
        self._grabber = self._canvas.create_image(2, self._height/2, image=self._imgG, anchor="w")
        self._grabberX = 0

        self._canvas.bind('<Button-1>',self._grabber_mouse_click)
        self._canvas.bind("<ButtonRelease-1>", self._grabber_mouse_release)
        self._canvas.bind('<B1-Motion>', self._grabber_mouse_drag)
        
        return

    def _createArrow(self):
        """Create the arrow on the right that indicates the sorting direction"""
        if self._isDescending:
            self._arrow = self._canvas.create_image(self._width-2, self._height/2, image=self._imgD, anchor="e")
        else:
            self._arrow = self._canvas.create_image(self._width-2, self._height/2, image=self._imgA, anchor="e")
        self._canvas.tag_bind(self._arrow, '<Button-1>', lambda event: self.changeStatus())
        return

    def _createText(self, maxWidth: int):
        """Create the text label"""
        self._txt = self._canvas.create_text(self._imgAD_width+4, self._height/2, anchor="w", text=self._text)
        
        box = self._canvas.bbox(self._txt)
        self._textWidth = box[2]-box[0]
        if maxWidth > 0 and self._textWidth > maxWidth:
            #TODO
            self._isReducedWidth = True
        self._canvas.tag_bind(self._txt, '<Button-1>', lambda event: self.close())
        return

    def _grabber_mouse_click(self, event):
        self._grabberX = int(self._canvas.canvasx(event.x))
        if self._cb_move is not None:
            self._cb_move(0, self._index)
        return
     
    def _grabber_mouse_drag(self, event):
        x = int(self._canvas.canvasx(event.x))
        dx = x - self._grabberX

        if self._cb_move is not None:
            self._cb_move(1, dx)
        return 
    
    def _grabber_mouse_release(self, event):
        x = int(self._canvas.canvasx(event.x))
        dx = x - self._grabberX

        if self._cb_move is not None:
            self._cb_move(2, dx)
        return 
