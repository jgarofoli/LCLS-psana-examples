import psana
import jutils


class myDataSource(object):
    def __init__(self,source):
        self._ds = psana.DataSource(source)
        self._itr = self._ds.events()
        self._detectors = {}


    def next_event(self):
        self._evt = self._itr.next()
        for det in self._detectors:
            self._detectors[det]['rawdata'] = self._evt.get(self._detectors[det]['cls'], self._detectors[det]['src'])
            self._detectors[det]['data'] = self._detectors[det]['handler']( self._detectors[det]['rawdata'] )
            setattr(self,det,self._detectors[det]['data'])

    def add_detector(self,name,cls,src,handler):
        self._detectors[name] = { 'cls': cls,
                'src': src,
                'data': None,
                'rawdata': None,
                'handler': handler,
                }


if __name__ == "__main__":

    srcacq = psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')
    srcevr = psana.Source('DetInfo(NoDetector.0:Evr.0)')

    acq_handler = lambda YY: getattr(YY,'data')(5).waveforms()[0]
    evr_handler = lambda YY: [ff.eventCode() for ff in YY.fifoEvents()]

    ds1 = myDataSource('exp=CXI/cxif7214:run=203')
    ds2 = myDataSource('exp=CXI/cxif7214:run=205')

    ds1.add_detector('acqiris',psana.Acqiris.DataDescV1,srcacq,acq_handler)
    ds1.add_detector('evr'    ,psana.EvrData.DataV3    ,srcevr,evr_handler)

    ds2.add_detector('acqiris',psana.Acqiris.DataDescV1,srcacq,acq_handler)
    ds2.add_detector('evr'    ,psana.EvrData.DataV3    ,srcevr,evr_handler)

    ds1.next_event()
    ds2.next_event()
    ds1.next_event()
    ds2.next_event()

    import pylab
    pylab.ion()

    pylab.figure()
    pylab.plot(ds1.acqiris,label='run 203',color='r',linewidth=2)
    pylab.title('run={:}, evr={:}'.format(203,ds1.evr))

    pylab.figure()
    pylab.plot(ds2.acqiris,label='run 205',color='g',linewidth=2)
    pylab.title('run={:}, evr={:}'.format(205,ds1.evr))



    pylab.draw()
    pylab.show()

