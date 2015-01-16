import psana
import logging

logger = logging.getLogger('acqirisFilter')
logger.setLevel(logging.DEBUG)

class myDataSource(object):
    def __init__(self,source):
        self._ds = psana.DataSource(source)
        self._itr = self._ds.events()
        self._evt = None
        self._at_end = False
        self._eventN = 0
        self._detectors = {}
        #self.Neventsinrun = len(self._ds.run.times()) # only works if idx data source is specified
        return


    def next_event(self):
        if self._at_end:
            return False

        try:
            self._evt = self._itr.next()
            if self._evt is None:
                return False
        except StopIteration :
            self.at_end = True
            return False
        except Exception as e:
            raise
        self._eventN += 1
        self.load_data()
        return True

    def load_event(self,n):
        self._evt = elf._ds.event( n )
        self._eventN = n
        if self._evt is None:
            return False
        self.load_data()
        return True

    def load_data(self):
        for det in self._detectors:
            self._detectors[det]['rawdata'] = self._evt.get(self._detectors[det]['cls'], self._detectors[det]['src'])
            if self._detectors[det]['handler']:
                self._detectors[det]['data'] = self._detectors[det]['handler']( self._detectors[det]['rawdata'] )
            else :
                self._detectors[det]['data'] = self._detectors[det]['rawdata']
            for algname in self._detectors[det]['algorithms_order']:
                alg = self._detectors[det]['algorithms'][algname]
                alg['results'] = alg['algorithm'](self, self._detectors[det]['data'], *alg['args'], **alg['kwargs'] )
            setattr(self,det,self._detectors[det]['data'])
        return 

    def add_detector(self,name,cls,src,handler=None,algorithms=[]):
        self._detectors[name] = { 'cls': cls,
                'src': src,
                'data': None,
                'rawdata': None,
                'handler': handler,
                'algorithms_order': [],
                'algorithms': {},
                }
        for alg in algorithms:
            if 'args' not in alg:
                alg['args'] = []
            if 'kwargs' not in alg:
                alg['kwargs'] = {}
            self._detectors[name]['algorithms'].append( alg )
        return

    def add_detector_handler(self,name,handler):
        self._detectors[name]['handler'] = handler
        return

    def add_detector_algorithm(self,detector_name,alg_name,position,*algorithms):
        """
        detector algorithms must accept 2 arguments: self and data, and return nothing
        Any data storage is done in self.  How to protect against collisions?
        Don't care what order?  just pass None for position
        """
        if not position:
            position = len( self._detectors[detector_name]['algorithms'] )
        for alg in algorithms:
            if 'args' not in alg:
                alg['args'] = []
            if 'kwargs' not in alg:
                alg['kwargs'] = {}
            self._detectors[detector_name]['algorithms_order'].insert(position,alg_name)
            self._detectors[detector_name]['algorithms'][alg_name] = alg
        return


if __name__ == "__main__":
    import time
    import pylab
    import numpy
    #import jutils

    if len(logging.root.handlers) == 0:
        logger_console_handler = logging.StreamHandler()
        logger_console_handler.setFormatter( logging.Formatter("LOG %(name)s %(levelno)s: %(message)s") )
        logger.addHandler( logger_console_handler )

    srcacq = psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')
    srcevr = psana.Source('DetInfo(NoDetector.0:Evr.0)')

    acq_handler = lambda YY: getattr(YY,'data')(5).waveforms()[0]
    evr_handler = lambda YY: sorted([ff.eventCode() for ff in YY.fifoEvents()])

    thisrun = 205
    ds2 = myDataSource('exp=CXI/cxif7214:run={:}:idx'.format(thisrun))
    #ds2 = myDataSource('exp=CXI/cxitut13:run={:}'.format(22))

    ds2.add_detector('acqiris',psana.Acqiris.DataDescV1,srcacq,handler=acq_handler)
    ds2.add_detector('evr'    ,psana.EvrData.DataV3    ,srcevr,handler=evr_handler)

#    def find_edge(*args,**kwargs):
#        threshold=kwargs.get('threshold',1000)
#        data = args[1]
#        above_thresh = [ int(el>threshold) for el in data ]
#        try:
#            edge = above_thresh.index(1)
#        except: 
#            edge = 0
#        return edge
#
#    ds2.add_detector_algorithm('acqiris','find_edge', None, {'algorithm': find_edge, 'args':[], 'kwargs':{ 'threshold': 800} } )

#    def find_peak(*args, **kwargs):
#        data = args[1]
#        ref  = kwargs.get('reference',False)
#        conv = list(numpy.convolve(data,ref))
#        result = conv.index(max(conv)) - sum( [ int( f!=0 ) for f in ref] )/2. # not general, valid for this signal shape
#        return result
#
#    fe2_ref = [0,1000,900,800,700,600,500,400,300,200,100,0] # signal shape prototype
#    ds2.add_detector_algorithm('acqiris','find_peak', None, {'algorithm': find_peak, 'args':[], 'kwargs':{ 'reference': fe2_ref} } )

    def find_max(*args, **kwargs):
        data = list(args[1])
        return data.index( max(data) )

    ds2.add_detector_algorithm('acqiris','find_max', None, {'algorithm': find_max, 'args':[], 'kwargs':{ } } )

    lines = []
    edges = {}
    reftime = time.time()
    for x in xrange(15):
        if ds2.next_event():
            if x % 10 == 0:
                logger.debug( "{:} {:} {:} {:}".format(repr(ds2._eventN), ds2._evt.run(),ds2._detectors['acqiris']['algorithms']['find_max']['results'], repr(ds2.evr) ))
            edges.setdefault( repr(ds2.evr), []).append(ds2._detectors['acqiris']['algorithms']['find_max']['results'])
            #lines.append(pylab.plot(ds2.acqiris,label='{:}'.format(ds2.evr[0]),linewidth=2))
            if 183 in ds2.evr:
                edges.setdefault( 183, []).append( ds2._detectors['acqiris']['algorithms']['find_max']['results']) 
            elif 184 in ds2.evr:
                edges.setdefault( 184, []).append( ds2._detectors['acqiris']['algorithms']['find_max']['results']) 
        else :
            logger.debug("ran out of events in loop")
            break
    logger.debug("spent %0.2f seconds iterating",time.time()-reftime)

    arrays = {}
    figures = []
#    for k in [183, 184] :
#        figures.append( pylab.figure() )
#        pylab.title('run={:} {:}'.format(ds2._evt.run(),k))
#        arrays[k] = numpy.array( edges[k] )
#        pylab.hist( arrays[k], bins=99, range=(1,100),label='{:}\n[m={:0.1f} +- {:0.1f}]\n[N={:}]\n[std={:0.1f}]'.format( k, arrays[k].mean(), arrays[k].std()/numpy.sqrt(arrays[k].size),arrays[k].size, arrays[k].std() ) )
#        logger.debug(  '{:} : [m={:0.1f} +- {:0.1f}] [N={:}] [std={:0.1f}]'.format( k, arrays[k].mean(), arrays[k].std()/numpy.sqrt(arrays[k].size),arrays[k].size, arrays[k].std() ) ) 
#        pylab.legend()
#        pylab.xlim(1,99)
#        pylab.ylim(ymax=pylab.ylim()[1]*1.2)
#        pylab.grid()
#        pylab.draw()

    figures.append( pylab.figure() )
    pylab.title('run {:}'.format(ds2._evt.run()))
    k = 184
    arrays[k] = numpy.array( edges[k] )
    pylab.hist( arrays[k], bins=99, range=(1,100),label='{:}\n[m={:0.1f} +- {:0.1f}]\n[N={:}]\n[std={:0.1f}]'.format( k, arrays[k].mean(), arrays[k].std()/numpy.sqrt(arrays[k].size),arrays[k].size, arrays[k].std() ) )
    pylab.legend()
    pylab.xlim(1,99)
    pylab.ylim(ymax=pylab.ylim()[1]*1.2)
    pylab.grid()
    pylab.draw()




    figures.append( pylab.figure() )
    pylab.title('run {:}'.format(ds2._evt.run()))
    k = 183
    arrays[k] = numpy.array( edges[k] )
    pylab.hist( arrays[k], bins=99, range=(1,100),label='{:}\n[m={:0.1f} +- {:0.1f}]\n[N={:}]\n[std={:0.1f}]'.format( k, arrays[k].mean(), arrays[k].std()/numpy.sqrt(arrays[k].size),arrays[k].size, arrays[k].std() ) )
    pylab.legend()
    pylab.xlim(1,99)
    pylab.ylim(ymax=pylab.ylim()[1]*1.2)
    pylab.grid()
    pylab.draw()


    figures.append( pylab.figure() )
    pylab.step(numpy.arange(ds2.acqiris.size),ds2.acqiris,label='data')
    pylab.title('run {:}, evr={:}'.format(ds2._evt.run(), ds2.evr))
#    res = numpy.convolve( ds2.acqiris, fe2_ref) 
#    res2 = numpy.amax(ds2.acqiris)/float(numpy.amax(res))*res
#    pylab.plot( res2 , label='convolved, scaled')
    pylab.grid()
#
#    pylab.figure()
#    pylab.plot(fe2_ref)
#    pylab.ylim(-100,1100)
#    pylab.xlim(xmin=-3)
#    pylab.grid()
#
    print " "
    print " "
    print "evr 184 time - evr 183 time = {:0.1f}".format( numpy.array(edges[184]).mean() - numpy.array(edges[183]).mean() )

    pylab.ion()
    pylab.show()


    for ii, fig in enumerate(figures):
        fig.savefig('acqiris_run{:}_{:}.pdf'.format(ds2._evt.run(),ii))
