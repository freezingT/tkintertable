import re

def contains(v1,v2):
    if v1 in v2:
        return True

def excludes(v1, v2):
    if not v1 in v2:
        return True

def equals(v1,v2):
    if v1==v2:
        return True

def notequals(v1,v2):
    if v1!=v2:
        return True

def greaterthan(v1,v2):
    if v2>v1:
        return True
    return False

def lessthan(v1,v2):
    if v2<v1:
        return True
    return False

def startswith(v1,v2):
    if v2.startswith(v1):
        return True

def endswith(v1,v2):
    if v2.endswith(v1):
        return True

def haslength(v1,v2):
    if len(v2)>v1:
        return True

def isnumber(v1,v2):
    try:
        float(v2)
        return True
    except:
        return False

def regex(v1,v2):
    """Apply a regular expression"""
    print (re.findall(v1,v2))
    return

operatornames = {'=':equals,'!=':notequals,
                   'contains':contains,'excludes':excludes,
                   '>':greaterthan,'<':lessthan,
                   'starts with':startswith,
                   'ends with':endswith,
                   'has length':haslength,
                   'is number':isnumber}