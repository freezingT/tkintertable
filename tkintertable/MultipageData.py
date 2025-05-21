"""
(c) 2025
"""

from typing import Union, Callable
import pandas


class UserInterruptException(Exception):
    """User requested interruption."""
    def __init__(self, *args):
        super().__init__(*args)


def _nonefun(num):
    return None


def _read_from_file(data, datainfo, dataconstructors, progresscallback):
    df = pandas.read_csv(data)
    return _parse_pandas_frame(df, datainfo, dataconstructors, progresscallback)


def _parse_list_list(data, progresscallback: Callable[[float], None]):
    datlen = len(data)
    clen = len(data[0])
    lst = []
    for i, e in enumerate(data):
        rowdat = {}
        for idxcol, r in enumerate(e):
            rowdat[str(idxcol+1)] = r
        lst.append(rowdat)
        progresscallback(i/(datlen-1))
    return lst, len(lst), clen


def _parse_dict_list(data, progresscallback):
    datlen = len(data)
    clen = len(data[0].keys())
    if progresscallback is not None:
        progresscallback(1.0)
    return data, datlen, clen


def _parse_pandas_frame(data: pandas.DataFrame, datainfo, dataconstructors, progresscallback):
    lst = []
    if len(datainfo) == 0:
        raise RuntimeError('Datainfo required if data is loaded from csv-file.')
    else:
        columntitles = datainfo[0]
    data.fillna("", inplace=True)
    nrows = data.shape[0]
    for i, row in data.iterrows():
        rowdat = {}
        for idxcol, colname in enumerate(columntitles):
            if colname in dataconstructors:
                rowdat[str(idxcol+1)] = dataconstructors[colname](row[colname])
            else:
                rowdat[str(idxcol+1)] = row[colname]
        lst.append(rowdat)
        cancel_triggered = progresscallback(i/(nrows-1))
        if cancel_triggered:
            raise UserInterruptException()

    return lst, len(lst), len(columntitles) # return data, ndata, ncols


def parse_data(data, datainfo=None, dataconstructors=None, progresscallback: Union[Callable[[float], None], None]=None):
    """
    Transform the given data into the format described below and return the
    data in the new format and the number of rows and columns.

    Args:
    data (str or list[list[str]]): given data
    datainfo (tuple): additional information, depending on input data format

    Return:
    data (list[dict]): Each element in the list represents a row in the
                        table, the dict gives the cell entries/columns
                        in a specific row.
    ndata (int): number of rows in the table
    ncols (int): number of columns in the table
    """
    if progresscallback is None:
        progresscallback = _nonefun
    if dataconstructors is None:
        dataconstructors = {}
    if datainfo is None:
        datainfo = ()

    if isinstance(data, str) and data.endswith('.csv'):
        return _read_from_file(data, datainfo, dataconstructors, progresscallback)

    if isinstance(data, list):
        datlen = len(data)
        if datlen > 0:
            if isinstance(data[0], list):
                return _parse_list_list(data, progresscallback)
            elif isinstance(data[0], dict):
                return _parse_dict_list(data, progresscallback)

    if isinstance(data, pandas.DataFrame):
        return _parse_pandas_frame(data, datainfo, dataconstructors, progresscallback)

    return [], 0, 0
