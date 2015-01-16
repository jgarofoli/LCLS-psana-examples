import psana
import jutils

src    = psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')
srcevr = psana.Source('DetInfo(NoDetector.0:Evr.0)')

ds1 = psana.DataSource('exp=CXI/cxif7214:run=203')
ds1_itr = ds1.events()
ds1_evt = ds1_itr.next()
ds1_acqiris = ds1_evt.get(psana.Acqiris.DataDescV1,src)
ds1_evr     = ds1_evt.get(psana.EvrData.DataV3,srcevr)
ds1_evr_fifo=[ff.eventCode() for ff in ds1_evr.fifoEvents()]
acdata1 = ds1_acqiris.data(0).waveforms()[0]

ds2 = psana.DataSource('exp=CXI/cxif7214:run=205')
ds2_itr = ds1.events()
ds2_evt = ds1_itr.next()
ds2_acqiris = ds2_evt.get(psana.Acqiris.DataDescV1,src)
ds2_evr     = ds2_evt.get(psana.EvrData.DataV3,srcevr)
ds2_evr_fifo=[ff.eventCode() for ff in ds1_evr.fifoEvents()]
acdata2 = ds2_acqiris.data(0).waveforms()[0]


import pylab
pylab.ion()

pylab.figure()
pylab.plot(acdata1,label='run 203',color='r',linewidth=2)
pylab.title('run={:}, evr={:}'.format(203,ds1_evr_fifo))

pylab.figure()
pylab.plot(acdata2,label='run 205',color='g',linewidth=2)
pylab.title('run={:}, evr={:}'.format(205,ds1_evr_fifo))



pylab.draw()
pylab.show()

