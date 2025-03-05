
from abc import ABC, abstractmethod
from collections.abc import Callable

# provide when this module is imported:
from .CellContentOperators import operatornames, doFiltering

class TableFilter(ABC):

    @abstractmethod
    def updateResults(self, rownames: list[str]) -> None:
        """
        Update the internal data if necessary when a filtering has been performed.
        Args:
            rownames:   the result of the filtering. Can be None if no filtering has been performed.
        """
        pass

    @abstractmethod
    def getFilterStructure(self):
        """"""
        pass


    def doFiltering(self, data, columnDict) -> list[str]:
        """
        ...
        Args:
            ...
        Return returns a list of row IDs, can be None if no filter is applied
        """
        F = self.getFilterStructure();
        rowIds = doFiltering(data, columnDict, F)
        if rowIds is None:
            self.updateResults(list(range(len(data))))        
        return rowIds