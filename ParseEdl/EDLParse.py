VERBOSE = False

# Author: Justin Garofoli
# Email : justing@SLAC.stanford.edu
# Date  : 2014 October 27

def parser(lines, verbose=VERBOSE, symbols={}):
    """

    Parses a SLAC edl file, and returns a dictionary of elements in the file.
    If symbols kwarg is passed, the key symbols will be replaced with the values.
    
    Example:
      with open('some.edl') as edl:
          edl_lines = edl.readlines()

      mydict = edl_parser( edl_lines )


    """
    nu= 0
    spaces = 0
    name = None
    blockname = None
    BEGIN = False
    BLOCK = False
    data = {}

    myiter = lines.__iter__()
    token = next(myiter,False)

    while token:
        nu += 1
        fmt = token.strip().lstrip()
        for sy in symbols:
            fmt = fmt.replace('$({:})'.format(sy),symbols[sy])
        if fmt == '' or fmt[0] == '#':
            token = next(myiter, False)
            continue
        if fmt[0:3] == 'end':
            name = None
            BEGIN = False
        if fmt[-1] == "}":
            blockname = None
            BLOCK = False
        if verbose:
            print "[ {:4.0f} {:30} {:15} {:5} {:5} {:5} {:5} ] | {:}".format(nu, name, blockname, repr(BEGIN), repr(BLOCK), repr(bool(name)), repr(bool(blockname)), token.rstrip())
        if name and not blockname:
            __ = fmt.split(' ',1)
            if len(__) == 2:
                k,v = __
                k=k.replace('"','')
                v=v.replace('"','')
                data[name][-1][k]=v
            elif len(__) == 1 :
                k = __[0]
                k.replace('"','')
                if k != '}': # I think this could be handling more elegantly 
                    data[name][-1][k]=True
            else :
                print "some parsing error:", token
        elif name and blockname:
            __ = fmt.split(' ',1)
            if len(__) == 2:
                k,v = __
                k=k.replace('"','')
                v=v.replace('"','')
                data[name][-1][blockname][k]=v
            elif len(__) == 1 :
                k = __[0]
                k=k.replace('"','')
                if k != '}': # I think this could be handling more elegantly
                    data[name][-1][blockname][k]=True
            else :
                print "some parsing error:", token
        if fmt[-1] == "{":
            blockname = str(fmt.split()[0])
            BLOCK = True
            data[name][-1][blockname] = {}
        if fmt[0:5] == 'begin':
            if 'object ' in prev_token:
                name = str(prev_token.split()[-1])
            else :
                name = str(prev_token)
            BEGIN = True
            data.setdefault(name,[]).append({})
        prev_token = str(fmt)
        token = next(myiter, False)

    return data

def symbols(symbs):
    """
    pass in a symbols string extracted from an edl file, returns a dictionary of key:value pairs.
    """
    symbs = symbs.replace('"','')
    symbs = symbs.replace("'",'')
    los = symbs.split(',')
    symbsdict = {}
    for l in los:
        k,v = l.split('=',1)
        symbsdict[k] = v
    return symbsdict
