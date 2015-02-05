import logging
logger = logging.getLogger(__name__+'.packer')

"""
this library packs unhashable objects (dict, list) to tuples
and provides the unpacking algorithm.

...if there is a library to do this already, I'd rather use that.

"""

def pack(oo):
    logger.debug( 'pack ' + repr( oo ) )
    if isinstance(oo,dict):
        return ('dict', tuple([ (k, pack(oo[k])) for k in oo ]))
    elif isinstance(oo,list):
        return ('list', tuple([ pack(o) for o in oo ]))
    elif isinstance(oo,tuple):
        return ('tuple', tuple([ pack(o) for o in oo]))
    else: # for ints, floats, strings, and other unknown types (that will probably not work with the intinded use)
        return (type(oo).__name__,oo)
    return 'should never get here'

def unpack(pp):
    logger.debug( 'unpack ' + repr( pp ) )
    if pp is None:
        return pp
    if pp[0] == 'dict':
        return dict( [(p[0],unpack(p[1])) for p in pp[1]] )
    elif pp[0] == 'list':
        return list(  [unpack(p) for p in pp[1]] )
    elif pp[0] == 'tuple':
        return tuple( [unpack(p) for p in pp[1]] )
    else:
        return pp[1]
    return oo



if __name__ == "__main__":

    tst = lambda x: unpack( pack( x ) )
    o1 = {'a':1,'b':2 }

    o2 = ('a','some',1,3 )

    o3 = 'some string'

    o4 = [1,2,3,4,5]

    o5 = [1,2,'a','b',{'a':1, 'b':2}]

    print 'testing', o1 == tst( o1 )  , repr(o1)
    print 'testing', o2 == tst( o2 )  , repr(o2)
    print 'testing', o3 == tst( o3 )  , repr(o3)
    print 'testing', o4 == tst( o4 )  , repr(o4)
    print 'testing', o5 == tst( o5 )  , repr(o5)

    o6 = [o1, o2, o3, o4, o5 ]
    o7 = {'a':o1, 'b':o2, 'c':o3, 'd':o4, 'e':o5 }

    print 'testing', o6 == tst( o6 ), repr(o6)
    print 'testing', o7 == tst( o7 ), repr(o7)
