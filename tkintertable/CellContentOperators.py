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


