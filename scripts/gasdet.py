import psana
import numpy
import jutils
from mpi4py import MPI
import pprint

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


#ds = psana.DataSource('exp=CXI/cxif7214:run=205:idx')
ds = psana.DataSource('exp=CXI/cxic0114:run=37:idx')
src = psana.Source('BldInfo(FEEGasDetEnergy)')

maxEventsPerNode=100

gas11 = lambda : gas.f_11_ENRC()
gas12 = lambda : gas.f_12_ENRC()
gas21 = lambda : gas.f_21_ENRC()
gas22 = lambda : gas.f_22_ENRC()
gas63 = lambda : gas.f_63_ENRC()
gas64 = lambda : gas.f_64_ENRC()
vals = {gas11: None, gas12: None, gas21: None, gas22: None, gas63: None, gas64: None,}

for run in ds.runs():
    times = run.times()
    mylength = len(times)/size
    if mylength>maxEventsPerNode: 
        mylength=maxEventsPerNode
    mytimes = times[rank*mylength:(rank+1)*mylength]

    for i in range(mylength):
        evt = run.event(mytimes[i])
        if evt is None:
            print '**** event fetch failed'
            continue

        # generic stuff goes here, move all specific functions to outside of this and call those here in a generic way.
        gas = evt.get(psana.Bld.BldDataFEEGasDetEnergyV1,src)
        if 'data' in locals():
            for k in vals:
                data[k].append( k() )
        else:
            data = {}
            for k in vals:
                data[k] = [ k() ]

        id = evt.get(psana.EventId)
        print 'rank', rank, 'analyzed event with fiducials', id.fiducials()

hists = {}
allhists = {}
for k in data:
    hists[k] = numpy.histogram( data[k], bins=100, range=(0,5))
    allhists[k] = numpy.empty_like( hists[k][0] )


def get_hists_mean(bins,vals):
    binw = bins[1]-bins[0]
    total = 0.
    mysum = 0.
    for b,v in zip(bins,vals):
        mysum += v*(b+binw/2.)
        total += 1
    return mysum/total




for k in hists:
    comm.Reduce(hists[k][0], allhists[k] )

if rank==0:
    import pylab
    pylab.ion()
    for ii,jk in enumerate(sorted(allhists)):
        pylab.figure()
        pylab.bar(hists[k][1][:-1],allhists[k],width=hists[k][1][1]-hists[k][1][0])
        pylab.xlim(0,5)
        print k, get_hists_mean(hists[k][1],allhists[k])
        pylab.savefig('figure_{:}.pdf'.format(ii))
        #pprint.pprint(allhists[k]) 
    print len(times), 'events in run'

