import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Callable

class FilterDialogFactoryInterface(ABC):

    @abstractmethod
    def createFilteringDialog(self, parent: tk.Tk, fields: list[str]):        
        """
        Create and show new Filtering Dialog
        Args:
            parent: the parent Frame (to get the geometry)
            fields: the names of the fields to show (column names in which a filter can be applied)
        """
        pass
        
    @abstractmethod
    def subscribe(self, doFilter : Callable[[Callable], None], showAll : Callable[[None], None] = None):
        """
        Provide a doFilter and a showAll callback function.
        Args:
            doFilter: function handle that is called when the filtering is triggered. It itself provides a function handle that must be called to get the filter result.
                    Args:   Callback function: Callable[[str, str, str], list[str]]. For more details see description in Filtering.TableFilter.doFiltering
                    Return: None
        """
        pass