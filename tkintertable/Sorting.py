from abc import ABC, abstractmethod
from operator import itemgetter


def __getDictComprehension(lst):
    return {k: k for k, _ in lst}

def doSorting(data, spec, columndict=None):
    """Perform the inplace sorting of the data, potentially in multiple passes."""
    if spec is None or len(spec) == 0:
        return # do nothing
    if columndict is None:
        columndict = __getDictComprehension(spec)

    for key, rvrsed in reversed(spec):
        data.sort(key=itemgetter(columndict[key]), reverse=rvrsed)
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

