import re

def contains(value, entry):
    return value in entry

def contains_ci(v1,v2):
    return v1.lower() in v2.lower()

def excludes(v1, v2):
    return not v1 in v2

def equals(v1,v2):
    return v1==v2

def notequals(v1,v2):
    return v1!=v2

def greaterthan(v1,v2):
    return v2>v1

def lessthan(v1,v2):
    return v2<v1

def startswith(v1,v2):
    return v2.startswith(v1)
    
def startswith_ci(v1,v2):
    return v2.lower().startswith(v1.lower())

def endswith(v1,v2):
    return v2.endswith(v1)

def endswith_ci(v1,v2):
    return v2.lower().endswith(v1.lower())

def haslength(v1,v2):
    if len(v2)>v1:
        return True

def isnumber(v1,v2):
    try:
        float(v2)
        return True
    except:
        return False

def onDateTime(v1, v2):
    return v2 == v1

def beforeDateTime(v1, v2):
    return v2 < v1

def sinceDateTime(v1, v2):
    return v2 > v1

def regex(value, entry):
    """Apply a regular expression"""
    return len(re.findall(value, entry)) > 0

operatornames = {'=': equals,
                '!=': notequals,
                '>': greaterthan,
                '<': lessthan,
                'contains': contains,
                'excludes': excludes,
                'starts with': startswith,
                'ends with': endswith,
                'contains (c.ins.)': contains_ci, 
                'starts with (c.ins.)': startswith_ci, 
                'ends with (c.ins.)': endswith_ci,
                'has length': haslength, 
                'is number': isnumber,
                'regex': regex,
                'on': onDateTime,
                'before': beforeDateTime,
                'since': sinceDateTime}

def _filterBy(data, filtercol, value, op='contains', columndict=None, userecnames=False,
                    progresscallback=None):
    """The searching function that we apply to the model data.
        This is used in Filtering.doFiltering to find the required recs
        according to column, value and an operator"""

    funcs = operatornames
    floatops = ['=','>','<']
    func = funcs[op]
    if columndict is not None:
        filtercolname = columndict[filtercol]
    else:
        filtercolname = filtercol
    rowIds=[]
    
    if isinstance(data, dict):
        keylist = data.keys()
    elif isinstance(data, list):
        keylist = range(len(data))
    else:
        raise RuntimeError("Unexpected data type.")

    for rec in keylist:
        if filtercolname in data[rec]:
            #try to do float comparisons if required
            if op in floatops:
                try:
                    #print float(data[rec][filtercolname])
                    item = float(data[rec][filtercolname])
                    v = float(value)
                    if func(v, item) == True:
                        rowIds.append(rec)
                    continue
                except:
                    pass
            item = str(data[rec][filtercolname])
            if func(value, item):
                rowIds.append(rec)
    return rowIds

def doFiltering(data, columndict=None, filters=None):
    """Module level method. Filter recs by several filters using a user provided
       search function.
       filters is a list of tuples of the form (key,value,operator,bool)
       returns: found record keys or None to reset the filtering
    """

    if filters == None or len(filters) == 0:
        return None
    F = filters
    sets = []
    for f in F:
        col, val, op, boolean = f
        rowIds = _filterBy(data, col, val, op, columndict)
        sets.append((set(rowIds), boolean))
    rowIds = sets[0][0]
    for s in sets[1:]:
        b=s[1]
        if b == 'AND':
            rowIds = rowIds & s[0]
        elif b == 'OR':
            rowIds = rowIds | s[0]
        elif b == 'NOT':
            rowIds = rowIds - s[0]
        #print len(names)
    rowIds = list(rowIds)
    return rowIds


