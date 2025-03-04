
from abc import ABC, abstractmethod
from collections.abc import Callable

# provide when this module is imported:
from .CellContentOperators import operatornames, doFiltering

class TableFilter(ABC):
    
    def __init__(self, callback: Callable[[Callable], None] = None):
        """
        Create an interface to filter the table data
        Args:
            callback: Called when a filter operation is triggered in the interface. Call TableFilter.doFiltering in the function provided as callback.
                    Args:   self.doFiltering
                    Return: None
        """
        super().__init__()
        self._filter_callback = lambda *args: callback(self.doFiltering)
        return


    @abstractmethod
    def doFiltering(self, searchfun: Callable[[str, str, str], list[str]]):
        """
        Perform the actual filtering after the filter operation is triggered.
        Args:
            searchfun: A handle to the function that applies the filters provided by the TableFilter
                    Args:   columnLabel:    the label of the column from which the element for this operator is  taken
                            value:          the value that is compared with the element
                            operator:       one of the binary operators defined in CellContentOperators that compares the element to the given value
                    Return: a list of row labels for which the binary operator returns True
        """
        pass