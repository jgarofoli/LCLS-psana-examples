from event_process import *
from mpi4py import MPI 

class AddEventProcessError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


def mk_counter():
    import numpy           # would like to remove this
    import psana           # and this
    ep1 = event_process()
    ep1.data       = numpy.array([0,])
    ep1.mergeddata = numpy.array([0,])
    ep1.set_reduction_step('Reduce')
    ep1.set_reduction_args([ep1.data, MPI.DOUBLE], [ep1.mergeddata, MPI.DOUBLE])
    ep1.set_reduction_kwargs(op=MPI.SUM,root=0)
    def ep1proc(ss,pp,evt):
        id = evt.get(psana.EventId)
        #print 'rank', pp.rank, 'analyzed event with fiducials', id.fiducials()
        ss.data[0] += 1
        return
    def ep1fin(ss):
        print "total events processed by all ranks", ss.mergeddata[0]
        return
    ep1.set_process_event(ep1proc)
    ep1.set_finish(ep1fin)
    ep1.in_report = 'meta'
    return ep1

def mk_mean_rms_hist(src,obj,attrs,in_report,title,histranges={}):
    import numpy
    import psana           # and this
    import pylab
    ep2 = event_process()
    ep2.data = []
    ep2.set_reduction_step('gather')
    ep2.set_reduction_args(ep2.data)
    ep2.set_reduction_kwargs(root=0)
    ep2.src = src
    ep2.obj = obj
    ep2.attrs = attrs
    ep2.in_report = in_report
    ep2.title = title
    ep2.histranges = histranges

    # http://mpi4py.scipy.org/docs/usrman/tutorial.html (gathering python objects)
    # get the gas detector energy and store it in the data array
    def get_det(ss,pp,evt):
        gas = evt.get(ss.obj,ss.src)
        if gas is None:
            return
        ss.data.append([])
        for attr in ss.attrs:
            ss.data[-1].append( getattr(gas,attr)() )
        return

    # calculate the mean and standard deviation of the distribution
    def reduce_det(ss):
        ss.alldata = {}
        for ii in xrange(len(ss.attrs)):
            ss.alldata[ii] = [] 
        for gath in ss.gathered:
            for chnk in gath:
                for ii,val in enumerate(chnk):
                    ss.alldata[ii].append(val)

        ss.results['table'] = {}
        ss.results['figures'] = {}
        for key in sorted(ss.alldata):
            newdata = numpy.array( ss.alldata[key] )
            print "{:} mean: {:0.2f}, std: {:0.2f}, min: {:0.2f}, max {:0.2f}".format( ss.attrs[key], newdata.mean(), newdata.std(), newdata.min(), newdata.max() )
            ss.results['table'][ss.attrs[key]] = {}
            ss.results['table'][ss.attrs[key]]['Mean'] = newdata.mean()
            ss.results['table'][ss.attrs[key]]['RMS'] = newdata.std()
            ss.results['table'][ss.attrs[key]]['min'] = newdata.min()
            ss.results['table'][ss.attrs[key]]['max'] = newdata.max()

            ss.results['figures'][key] = {}
            fig = pylab.figure()
            if ss.attrs[key] in ss.histranges:
                thisrange = ss.histranges[ ss.attrs[key] ]
            else:
                thisrange = (0,5)
            pylab.hist(newdata,bins=100,range=thisrange)
            pylab.title( ss.attrs[key] )
            pylab.xlim(*thisrange)
            pylab.savefig( 'figure_{:}.pdf'.format( ss.attrs[key] ) )
            pylab.savefig( 'figure_{:}.png'.format( ss.attrs[key] ) )
            ss.results['figures'][key]['png'] = 'figure_{:}.png'.format( ss.attrs[key] )
            ss.results['figures'][key]['pdf'] = 'figure_{:}.pdf'.format( ss.attrs[key] )
        return

    ep2.set_process_event(get_det)
    ep2.set_finish(reduce_det)
    ep2.set_reduction_step('gather')
    ep2.set_reduction_args(ep2.data)
    ep2.set_reduction_kwargs(root=0)
    return ep2

def mk_evr():
    import psana
    ep3 = event_process()
    ep3.data = []
    ep3.src = psana.Source('DetInfo(NoDetector.0:Evr.0)')

    def get_evr(ss,pp,evt):
        evr = evt.get(psana.EvrData.DataV3, ss.src)
        if evr is None:
            ss.data = []
        else:
            ss.data = [ff.eventCode() for ff in evr.fifoEvents()]
    ep3.set_process_event(get_evr)
    return ep3

