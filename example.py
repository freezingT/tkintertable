import tkinter as tk
from tkinter import Frame

from tkintertable import Tables
#from tkintertable.Multipagetable import MultipageTable
import tkintertable as tktab

import pandas

def get_data():
    """Read the sample file containing tabular data and organize in a nested list"""
    lst = []
    df = pandas.read_csv('sample-top-500-novels.csv', comment='#')
    
    columns =  []
    for c in df.columns:
        columns.append(c)

    for row in df.iterrows():
        L = []
        for cname in columns:
            L.append(row[1][cname])
        lst.append(L)
    
    return lst, (), columns


def start_app():
    root = tk.Tk()
    root.geometry("800x600")
    masterframe = Frame(root)
    masterframe.pack(fill="both", expand=True)

    thedata, datainfo, columns = get_data()

    #Tables.TableCanvas(masterframe, data=thedata)
    example = tktab.MultipageTable(masterframe, thedata, dataparam=datainfo, columnTitles=columns)
    filtering = tktab.FilterPanel(masterframe, columns, fieldtypes=None, callback=example.triggerFiltering)
    sorting = tktab.SortingPanel(masterframe, fields=columns, callback=example.triggerSorting)

    filtering.pack(side="top", expand=False, fill="x")
    sorting.pack(side="top", expand=False, fill="x")
    example.pack(side="top", fill="both", expand=True)

    root.mainloop()
    return


if __name__ == "__main__":
    start_app()