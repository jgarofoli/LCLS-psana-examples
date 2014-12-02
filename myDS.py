import jutils
from mpi4py import MPI
import data_summary
import data_summary.data_summary_utils as dsu
import psana
import numpy
import pylab
#import jinja2 # for producing the report


#
# to run parallel: mpirun -n 12 python myDS.py
#

#ds = psana.DataSource('exp=CXI/cxic0114:run=37:idx')
ds = psana.DataSource('exp=CXI/cxif7214:run=205:idx')


myMPIrunner = data_summary.mpi_runner()
myMPIrunner.set_datasource(ds)
myMPIrunner.add_event_process('ep1',dsu.mk_counter())
myMPIrunner.set_output_directory('./cxic0114_run37')

# get the mean and rms of the gases
# make a trend of the 

ep2 = data_summary.event_process()
ep2.data = []
ep2.set_reduction_step('gather')
ep2.set_reduction_args(ep2.data)
ep2.set_reduction_kwargs(root=0)
ep2.src = psana.Source('BldInfo(FEEGasDetEnergy)')
ep2.obj = psana.Bld.BldDataFEEGasDetEnergyV1
ep2.attrs = ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',]

# http://mpi4py.scipy.org/docs/usrman/tutorial.html (gathering python objects)
# get the gas detector energy and store it in the data array
def get_gas_det(ss,pp,evt):
    gas = evt.get(ss.obj,ss.src)
    if gas is None:
        return
    ss.data.append([])
    for attr in ss.attrs:
        ss.data[-1].append( getattr(gas,attr)() )
    return

# calculate the mean and standard deviation of the distribution
def reduce_gas_det(ss):
    ss.alldata = {0: [], 1:[], 2:[], 3:[], 4:[], 5:[], }
    for gath in ss.gathered:
        for chnk in gath:
            for ii,val in enumerate(chnk):
                ss.alldata[ii].append(val)

    for key in sorted(ss.alldata):
        newdata = numpy.array( ss.alldata[key] )
        print "{:} mean: {:0.2f}, std: {:0.2f}".format( ss.attrs[key], newdata.mean(), newdata.std() )
        fig = pylab.figure()
        pylab.hist(newdata,bins=100,range=(0,5))
        pylab.title( ss.attrs[key] )
        pylab.xlim(0,5)
        pylab.savefig( 'figure_{:}.pdf'.format( ss.attrs[key] ) )
        pylab.savefig( 'figure_{:}.png'.format( ss.attrs[key] ) )
    return

ep2.set_process_event(get_gas_det)
ep2.set_finish(reduce_gas_det)
ep2.set_reduction_step('gather')
ep2.set_reduction_args(ep2.data)
ep2.set_reduction_kwargs(root=0)
myMPIrunner.add_event_process('ep2',ep2)

# add the EVR to the data getting routines
ep3 = data_summary.event_process()
ep3.data = []
ep3.src = psana.Source('DetInfo(NoDetector.0:Evr.0)')

def get_evr(ss,pp,evt):
    evr = evt.get(psana.EvrData.DataV3, ss.src)
    if evr is None:
        ss.data = []
    else:
        ss.data = [ff.eventCode() for ff in evr.fifoEvents()]
ep3.set_process_event(get_evr)

myMPIrunner.add_event_process('ep3',ep3)



ep4 = data_summary.event_process()
ep4.data = {}
ep4.set_reduction_step('gather')
ep4.set_reduction_args(ep4.data)
ep4.set_reduction_kwargs(root=0)
ep4.src = psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')

def find_peak(ss,pp,evt):
    traces = evt.get(psana.Acqiris.DataDescV1,ss.src)
    if traces is None:
        return
    trace = list(traces.data(5).waveforms()[0])
    peak = trace.index( max(trace) )
    for evr in pp.event_processes['ep3'].data:
        ss.data.setdefault( evr, []).append( peak )

ep4.set_process_event(find_peak)

def reduce_acqiris_peaks(ss):
    ss.alldata = {}
    for gath in ss.gathered:
        for evr in gath:
            ss.alldata.setdefault(evr,[]).extend( gath[evr] )

    ss.results['table'] = {}
    ss.results['figures'] = {}
    for evr in sorted(ss.alldata):
        newdata = numpy.array( ss.alldata[evr] )
        print "{:} mean: {:0.2f}, std: {:0.2f}".format( evr, newdata.mean(), newdata.std() )
        ss.results['table'][evr] = {}
        ss.results['table'][evr]['Mean Arrival Bin'] = newdata.mean()
        ss.results['table'][evr]['RMS'] = newdata.std()

        ss.results['figures'][evr] = {}
        fig = pylab.figure()
        hh = pylab.hist(newdata,bins=100,range=(0,100))
        pylab.title( 'evr '+repr(evr) )
        pylab.xlim(0,100)
        pylab.savefig( 'figure_evr_{:}.pdf'.format( evr ) )
        pylab.savefig( 'figure_evr_{:}.png'.format( evr ) )
        ss.results['figures'][evr]['png'] = 'figure_evr_{:}.png'.format( evr )
        ss.results['figures'][evr]['pdf'] = 'figure_evr_{:}.pdf'.format( evr )

ep4.set_finish(reduce_acqiris_peaks)

myMPIrunner.add_event_process('ep4',ep4)


myMPIrunner.mpirun()

myMPIrunner.mk_output_html()
