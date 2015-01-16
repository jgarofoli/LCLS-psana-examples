import sys
import time
import pylab
import numpy
import code
pylab.ion()

import psdata
import jutils

import logging
logger = logging.getLogger('draw')
logger.setLevel(logging.DEBUG)
if len(logging.root.handlers) == 0 :
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("LOG %(name)s %(levelno)s: %(message)s"))
logger.addHandler(console_handler)

def find_leading_edge(a,threshold=1000):
    return [ el>threshold for el in a ].index(True) 

def get_separation(a,b,threshold=1000.):
    edge_a = find_leading_edge(a,threshold=threshold)
    edge_b = find_leading_edge(b,threshold=threshold)
    return edge_b - edge_a

def acqiris_data(data):
    __ = data.Acqiris.data(5)
    return __.waveforms()[0] 


def myfun3(data):

    blocks = []
    blocks.append( { 183 : [], 184 : [], 'evr183': [], 'evr184': [] } )
    
    ii = 0
    while ii < 10:
        ii += 1
        data.next_event()
        if 184 in data.Evr.eventCodes:
            logger.debug(repr(ii)+' found 184')
            blocks.append( { 183 : [], 184 : [], 'evr183': [], 'evr184': []} )
            blocks[-1][184].append( acqiris_data( data ) )
            blocks[-1]['evr184'].append( data.Evr.eventCodes )
            continue

        if 183 in data.Evr.eventCodes:
            logger.debug(repr(ii)+' found 183')
            blocks[-1][183].append( acqiris_data( data ) )
            blocks[-1]['evr183'].append( data.Evr.eventCodes )
            continue

    return blocks

def myplotter(d183,d184,threshold=800,new_figure=False,reset=False):
    if reset:
        pylab.gca().clear()
    if new_figure:
        pylab.figure()

    lines183 = []
    lines184 = []
    for x in d183:
        lines183.append(pylab.plot(x,color='0.8',linestyle='--',label='183'))
    for x in d184:
        lines184.append(pylab.plot(x,color='0.7',linestyle='-',label='184'))

    # make averages
    z183 = numpy.zeros(len( d183[0] ) )
    #code.interact(None,None,locals())
    z184 = numpy.zeros(len( d184[0] ) )

    data_edges = []
    for r in d183:
        z183 += r/float( len( d183) )
        data_edges.append( find_leading_edge(r,threshold=threshold) )

    for r in d184:
        z184 += r/float( len( d184) )
        edge_ref = find_leading_edge(r,threshold=threshold)

    edge_seps = [ edge_ref - de for de in data_edges ]
    print edge_seps
        


    avgs183 = pylab.plot(z183,color='.01',linestyle='--',linewidth=2)
    avgs184 = pylab.plot(z184,color='.01',linestyle='-',linewidth=2)

    pylab.legend((lines183[0][0], lines184[0][0],avgs183[0],avgs184[0]),('183','184','avg 183','avg 184'))
    sep = get_separation(z183,z184,threshold=threshold)

    thresh = pylab.plot([0,len(x)],[threshold,threshold],color='r',label='threshold')
    text = pylab.figtext(0.3,0.8,'edge sep = {:0.0f}'.format(sep),color='r')

    pylab.draw()
    pylab.grid(True)
    pylab.show()
    return


def myfun2(data,reset=False,new_figure=False,avg_events=30,threshold=1000):
    if reset:
        pylab.gca().clear()
    if new_figure:
        pylab.figure()

    xx183d = []
    xx184d = []

    timeaxis = []

    ii = 0
    while len(xx183d) < avg_events or len(xx184d) < avg_events :
        if 183 in data.Evr.eventCodes and len(xx183d) < avg_events :
            __ = data.Acqiris.data(5)
            xx183d.append( __.waveforms()[0] )
            logger.debug(repr(ii) + " found 183:   "+repr(data.Evr.eventCodes))
        elif 184 in data.Evr.eventCodes and len(xx184d) < avg_events :
            __ = data.Acqiris.data(5)
            xx184d.append( __.waveforms()[0] )
            logger.debug(repr(ii) + " found 184:   "+repr(data.Evr.eventCodes))
        else :
            logger.debug(repr(ii) + " found other: "+repr(data.Evr.eventCodes))

        ii += 1

        if len(xx183d) == avg_events and len(xx184d) == avg_events:
            break

        if ii > 100:
            logger.warning("too many next_event calls")
            break

        data.next_event()

    logger.info('stepped through {:} events'.format(ii))
    logger.info('found {:} events with evr code 183'.format(len(xx183d)))
    logger.info('found {:} events with evr code 184'.format(len(xx184d)))

    lines183 = []
    lines184 = []
    for x in xx183d:
        lines183.append(pylab.plot(x,color='0.8',linestyle='--',label='183'))
    for x in xx184d:
        lines184.append(pylab.plot(x,color='0.7',linestyle='-',label='184'))

    # make averages
    z183 = numpy.zeros(len( xx183d[0] ) )
    #code.interact(None,None,locals())
    z184 = numpy.zeros(len( xx184d[0] ) )

    for r in xx183d:
        z183 += r/float( len( xx183d) )

    for r in xx184d:
        z184 += r/float( len( xx184d) )


    if avg_events > 1:
        avgs183 = pylab.plot(z183,color='.01',linestyle='--',linewidth=2)
        avgs184 = pylab.plot(z184,color='.01',linestyle='-',linewidth=2)

        pylab.legend((lines183[0][0], lines184[0][0],avgs183[0],avgs184[0]),('183','184','avg 183','avg 184'))
        sep = get_separation(z183,z184,threshold=threshold)
    else:
        pylab.legend((lines183[0][0], lines184[0][0]),('183','184'))
        sep = get_separation(xx183d[0],xx184d[0],threshold=threshold)

    thresh = pylab.plot([0,len(x)],[threshold,threshold],color='r',label='threshold')
    text = pylab.figtext(0.3,0.8,'edge sep = {:0.0f}'.format(sep),color='r')

    pylab.draw()
    pylab.grid(True)
    pylab.show()

    return
    #return locals()

if __name__ == "__main__":
    ids = 203

    ds = psdata.psdata(exp='cxif7214',run=203)
    #datablocks = myfun3(ds)
    #myplotter(datablocks[1][183], datablocks[1][184], new_figure=True )

    ds2 = psdata.psdata(exp='cxif7214',run=205)
    #datablocks2 = myfun3(ds2)
    #myplotter(datablocks2[1][183], datablocks2[1][184], new_figure=True )

    a = ds.Acqiris.data(5)
    a2= ds2.Acqiris.data(5)
    print sum(a.waveforms()[0] - a2.waveforms()[0])

    import pprint
    import inspect
    import clint
    mypp = lambda D: pprint.pprint(sorted(D.keys()))


    for kk in sorted(ds.__dict__) :
        mybool = not bool(id(ds.__dict__[kk])-id(ds2.__dict__[kk]))
        if mybool:
            print "{:20} {:20} {:20} {:}".format(kk, id(ds.__dict__[kk]), id(ds2.__dict__[kk]), clint.textui.colored.red(repr(mybool)))
        else:
            print "{:20} {:20} {:20} {:}".format(kk, id(ds.__dict__[kk]), id(ds2.__dict__[kk]), mybool)

    for z in zip(inspect.getmembers(ds),inspect.getmembers(ds2)):
        mybool = not bool( id(z[0][1]) - id(z[1][1]))
        if mybool:
            print "{:25} {:25} {:<20s}  {:.150s}".format( z[0][0], z[1][0], clint.textui.colored.red( repr(mybool) ), repr(z[0][1])+' '+repr(z[1][1]))
        else :
            print "{:25} {:25} {:^5s} {:.150s}".format( z[0][0], z[1][0], repr(mybool), repr(z[0][1])+' '+repr(z[1][1]))

