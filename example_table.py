"""
Test script for the Tables class
"""

from __future__ import absolute_import, division, print_function
try:
	from tkinter import *
	from tkinter.ttk import *
except:
	from Tkinter import *
	from ttk import *
import random, string
from tkintertable import TableCanvas
from tkintertable import TableModel
from tkintertable import SortingPanel

"""Testing general functionality of tables"""

class App:
	def __init__(self, master):
		self.main = Frame(master)
		self.main.pack(fill=BOTH,expand=1)
		master.geometry('600x400+200+100')

def sampledata():
	"""Return a sample dictionary for creating a table"""

	data={}
	cols = ['a','b','c','d','e']
	for i in range(10):
		data[i] = {i:round(random.random(),2) for i in cols}
	return data

def createRandomStrings(l,n):
	"""create list of l random strings, each of length n"""

	names = []
	for i in range(l):
		val = ''.join(random.choice(string.ascii_lowercase) for x in range(n))
		names.append(val)
	return names

def createData(rows=20, cols=5):
	"""Creare random dict for test data"""

	data = {}
	names = createRandomStrings(rows,16)
	colnames = createRandomStrings(cols,5)
	for n in names:
		data[n]={}
		data[n]['label'] = n
	for c in range(0,cols):
		colname=colnames[c]
		vals = [round(random.normalvariate(100,50),2) for i in range(0,len(names))]
		vals = sorted(vals)
		i=0
		for n in names:
			data[n][colname] = vals[i]
			i+=1
	return data

def createTable(model, **kwargs):
	t=Toplevel()
	app = App(t)
	master = app.main
	table = TableCanvas(master, model,rowheaderwidth=50, **kwargs)
	table.createTableFrame()
	return table

def test1(root):
    """Setup a table and populate it with data"""
    app = App(root)
    master = app.main
    model = TableModel()
    data = createData(40)
    model.importDict(data)
    oframe = Frame(master)
    table = TableCanvas(oframe, model,
                        cellwidth=60, cellbackgr='#e3f698',
                        thefont=('Arial',12),rowheight=18, rowheaderwidth=30,
                        rowselectedcolor='yellow', editable=True)
    table.createTableFrame()
    model.deleteColumns([0])
    model.deleteRows(range(0,2))
    table.addRow(1,label='aaazzz')
    table.addRow(label='bbb')
    table.addRow(**{'label':'www'})
    table.addColumn('col6')
    oframe.pack(side="top", fill="both", expand=True)
	
    columns = list(table.model.getColumnDict().values())
    sorting = SortingPanel(master, fields=columns, callback=table.triggerSorting)
    sorting.pack(side="top", fill="x")
    return




def GUITests():
	"""Run standard tests"""

	root = Tk()
	test1(root)
	return root

def main():
	root = GUITests()
	root.mainloop()
	#loadSaveTest()

if __name__ == '__main__':
	main()
