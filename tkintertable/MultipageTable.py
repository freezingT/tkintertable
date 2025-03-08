
from tkinter import Frame
from .FilterPanel import FilterPanel
from .CellContentOperators import doFiltering
from operator import itemgetter
import pandas

from .Tables import TableCanvas
from .NavigationPanel import NavigationPanel

class MultipageTable(Frame):
    def __init__(self, parent, data, columnTitles, dataparam=(), nPerPage=100, fieldtypes=None, dataconstructors={}, filterdialogfactory=None):
        """ 
        Table that displays its rows on multiple pages. Navigation is possible using buttons at the bottom.

        Args:
        parent (tk object)
        data (list, pandas frame, [list to be extended])
        dataparam (tuple): provide additional information for the setData-method, depending on the data type provided
        nPerPage (int): how many rows to show per page
        columnTitles (list[str]): list of column labels
        """
        
        Frame.__init__(self, parent)
        self._outerFrame = Frame(self)
        self._outerFrame.pack(side="top", fill="both", expand=True, anchor="n")

        [self._data, ndata, self._ncols] = self._parseData(data, datainfo=dataparam, dataconstructors=dataconstructors)
        self._filteredData = None
        nrows = 0


        self._table = TableCanvas(self._outerFrame, 
                                  showkeynamesinheader=True, 
                                  rowheaderwidth=55, 
                                  read_only=True,
                                  show_popup=True,
                                  rows=nrows, 
                                  cols=self._ncols,
                                  filterdialogfactory=filterdialogfactory)
        self.__setPopupMenuEntries()
        self._table.show()


        self._navtab = NavigationPanel(self, ndata, nPerPage, command=self._changePage)
        self._navtab.pack(side="bottom", expand=False, fill="none")

        datrange = self._getPageDataRange()
        rownames = list(map(lambda x: str(x+1), list(range(datrange[0], datrange[1]))))

        if columnTitles is not None:
            self.setColumnNames(columnTitles)
        self.__table_setData(self._data[datrange[0]:datrange[1]], rownames=rownames)

        self._table.adjustColumnWidths()
        return

    def __setPopupMenuEntries(self):
        T = self._table.showPopupMenuEntry

        T["Paste"] = False
        T["Fill Down"] = False
        T["Fill Right"] = False
        T["Add Row(s)"] = False
        T["Delete Row(s)"] = False
        T["View Record"] = False
        T["Clear Data"] = False
        T["Auto Fit Columns"] = False
        T["New"] = False
        T["Load"] = False
        T["Save"] = False
        T["Import text"] = False
        T["Plot Selected"] = False
        T["Plot Options"] = False
        T["Export Table"] = False
        T["Preferences"] = False
        T["Formulae->Value"] = False
        T["Rename Column"] = False
        T["Sort by"] =  False
        T["Delete This Column"] = False
        T["Add New Column"] = False
        self._table.showPopupMenuEntry = T


    def setColumnNames(self, columnTitles): 
        columnTitles = columnTitles+['']*max(0, self._ncols - len(columnTitles)) # ensure column_data length
        columnTitles = columnTitles[0:self._ncols]
        self._columnTitles = columnTitles
        for idx, title in enumerate(columnTitles):
            self._table.model.relabel_Column(idx, title)
        return

    def getColumnNames(self):
        return self._columnTitles
    
    def getColumnDict(self):
        """ Return the dictionary that maps column labels to column names """
        return {y: x for x, y in self._table.model.columnlabels.items()}

    def setMultilineCells(self, multilinerows: list[int], multilinecolumns: list[str]):
        coldict = self.getColumnDict()
        for c in multilinecolumns:
            self._table.setColumnMultiline(coldict[c])
        for r in multilinerows:
            self._table.setRowMultiline(r)
        return

    def setMaxCellwidths(self, maxcellwidths: dict[str, int]):
        coldict = self.getColumnDict()
        for col in maxcellwidths:
            self._table.setMaxCellWidth(coldict[col], maxcellwidths[col])
        return

    def setTooltipEnabled(self, tooltipenable: dict[str, bool]):
        coldict = self.getColumnDict()
        for clabel in tooltipenable:
            self._table.setColumnTooltip(coldict[clabel], tooltipenable[clabel])
        return

    def replaceTableData(self, data, rownames=None):
        self.__table_setData(data, rownames=rownames)
        self._table.redraw()
        return

    def _getPageDataRange(self):
        navtabdata = self._navtab.getStateData()
        return navtabdata['page_range']

    def _changePage(self):
        datrange = self._getPageDataRange()
        rownames = list(map(lambda x: str(x+1), list(range(datrange[0], datrange[1]))))
        
        self._table.deletePopups()
        self._table.requireRowHeightReset()
        if self._filteredData is not None:
           self.replaceTableData(self._filteredData[datrange[0]:datrange[1]], rownames=rownames)
        else:
            self.replaceTableData(self._data[datrange[0]:datrange[1]], rownames=rownames)
        self._table.set_yviews('moveto', 0) # reset view to first line
        return

    def _parseData(self, data, datainfo=(), dataconstructors={}):
        """
        Transform the given data into the format described below and return the data in the new format and the number of rows and columns

        Args:
        data (str or list[list[str]]): given data
        datainfo (tuple): additional information, depending on input data format

        Return:
        data (list[dict]): Each element in the list represents a row in the table, the dict gives the cell entries/columns in a specific row
        ndata (int): number of rows in the table
        ncols (int): number of columns in the table
        """
        if isinstance(data, str) and data.endswith('.csv'):
            lst = []
            if len(datainfo) == 0:
                raise RuntimeError('Datainfo required if data is loaded from csv-file.')
            else:
                columntitles = datainfo[0]
            df = pandas.read_csv(data)
            for idx, row in df.iterrows():
                rowdat = {}
                for idxcol, colname in enumerate(columntitles):
                    if colname in dataconstructors:
                        rowdat[str(idxcol+1)] = dataconstructors[colname](row[colname])
                    else:
                        rowdat[str(idxcol+1)] = row[colname]
                lst.append(rowdat)
            return lst, len(lst), len(columntitles) # return data, ndata, ncols
        
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], list):
                clen = len(data[0])
                lst = []
                for idx, e in enumerate(data):
                    rowdat = {}
                    for idxcol, r in enumerate(e):
                        rowdat[str(idxcol+1)] = r
                    lst.append(rowdat)
                return lst, len(lst), clen
            
        else: # TODO other ways to provide data?
            return [], 0, 0 
        
    def __table_setData(self, data, rownames=None):        
        #remove unrequired columns:
        if len(data) > 0:
            self._table.model.deleteColumns(list(reversed(range(len(data[0]), self._table.model.getColumnCount()))))

        if rownames is not None:
            self._table.model.deleteRows()
        else:
            rname = None
        nTableRows = self._table.model.getRowCount()
        for idx, d in enumerate(data):
            if idx < nTableRows:
                self.__table_replaceRow(d, idx)
            else:
                if rownames is not None:
                    rname = rownames[idx]
                self.__table_addRow(d, keyname=rname)

        # remove unrequired rows:
        self._table.model.deleteRows(list(reversed(range(len(data), self._table.model.getRowCount()))))
        return
        
    def __table_replaceRow(self, dictdata, idx):
        if idx >= self._table.model.getRowCount():
            raise ValueError("Row to be replaced does not exist.")
        for lbl in dictdata:
            ic = self._table.model.getColumnIndex(lbl)
            self._table.model.setValueAt(dictdata[lbl], idx, ic)
        return

    def __table_addRow(self, dictdata, keyname=None):
        self._table.model.addRow(keyname, **dictdata)
        return

    def _setFilteredData(self, rowids) -> int:
        if rowids is None:
            if self._filteredData is not None:
                self.showAll()
            return len(self._data)
        elif len(rowids) == 0:
            self._filteredData = []
            self._navtab.updateN(0)
            n = 0
        elif len(rowids) == 1:
            self._filteredData = [self._data[rowids[0]]]
            self._navtab.updateN(1)
            n = 1
        else:
            self._filteredData = list(itemgetter(*rowids)(self._data))
            self._navtab.updateN(len(self._filteredData))
            n = len(rowids)
        self._changePage()
        return n

    def showAll(self):
        self._filteredData = None
        self._navtab.updateN(len(self._data))
        self._changePage()
        return

    def triggerFiltering(self, doFilterCallback):
        rowids = doFilterCallback(self._data, self.getColumnDict())
        n = self._setFilteredData(rowids)
        return n

    def filterData(self, filters) -> int:
        rowids = doFiltering(self.data, self.getColumnDict(), filters)
        n = self._setFilteredData(rowids)
        return n
    
    def triggerSorting(self, doSortCallback):
        """Function that is called when the sorting of the data is triggered."""
        doSortCallback(self._data, self.getColumnDict())
        if self._filteredData is not None:
            doSortCallback(self._filteredData, self.getColumnDict())        
        self._changePage()
        return
    