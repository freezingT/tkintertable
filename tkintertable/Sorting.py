from abc import ABC, abstractmethod
from operator import itemgetter


def __getDictComprehension(lst):
    return {k: k for k, _ in lst}

def __sortList(data, spec, columndict):
    for key, rvrsed in reversed(spec):
        data.sort(key=itemgetter(columndict[key]), reverse=rvrsed)
    return

def __sortfun(k, key, columndict, thedict):
    # this function is necessary since it is not ensured that all row dicts contain all column name keys
    columnId = columndict[key]
    if columnId in thedict[k].keys():
        return (0, thedict[k][columndict[key]])
    else:
        return (1, 0)

def __sortDict(thedict, keylist, spec, columndict):
    for key, rvrsed in reversed(spec):
        keylist.sort(key=lambda k: __sortfun(k, key, columndict, thedict), reverse=rvrsed)
    return

def doSorting(data, spec, columndict=None):
    """Perform the inplace sorting of the data, potentially in multiple passes."""
    if spec is None or len(spec) == 0:
        return # do nothing
    if columndict is None:
        columndict = __getDictComprehension(spec)

    if not isinstance(data, tuple):
        __sortList(data, spec, columndict)
    else:
        __sortDict(data[0], data[1], spec, columndict)
    return
        

class TableSorter(ABC):
    @abstractmethod
    def getSortSpecification(self):
        """Get a struct spec the describes the sorting. Each element in spec is a tuple of the column name and a "descend"-flag."""
        pass

    def doSorting(self, data, columndict=None):
        """Performs the sorting inplace on the given data."""
        specs = self.getSortSpecification()
        doSorting(data, specs, columndict)
        return

