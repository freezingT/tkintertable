"""
Module defines TableFilter interface for classes providing filtering 
functionality for a Table object and provides the doFiltering method
to perform a filtering.
"""

from abc import ABC, abstractmethod

# provide when this module is imported:
from .CellContentOperators import doFiltering

class TableFilter(ABC):
    """Abstract class that provides filter functionality for Table objects"""

    @abstractmethod
    def updateResults(self, rownames: list[str]) -> None:
        """
        Update the internal data if necessary when a filtering has been performed.
        Args:
            rownames:   the result of the filtering. Can be None if no filtering has been performed.
        """

    @abstractmethod
    def getFilterStructure(self) -> list[(str, str, str, bool)]:
        """Return the structure containing information on  the filters applied to the table."""

    def doFiltering(self, data, columnDict=None) -> list[str]:
        """
        ...
        Args:
            ...
        Return returns a list of row IDs, can be None if no filter is applied
        """
        filter_structure = self.getFilterStructure()
        row_ids = doFiltering(data, columnDict, filter_structure)
        if row_ids is None:
            self.updateResults(list(range(len(data))))
        return row_ids
    