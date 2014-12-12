import jutils
#from mpi4py import MPI
import data_summary
import data_summary.data_summary_utils as dsu
import psana
import numpy
import matplotlib
matplotlib.use('Agg')

import pylab
#import jinja2 # for producing the report


#
# to run parallel: mpirun -n 12 python myDS.py
#

#ds = psana.DataSource('exp=CXI/cxic0114:run=37:idx')
#ds = psana.DataSource('exp=CXI/cxif7214:run=205:idx')


myMPIrunner = data_summary.job()
myMPIrunner.set_datasource(exp='CXI/cxif7214',run=205)

myMPIrunner.add_event_process('ep1',dsu.mk_counter())
#myMPIrunner.set_output_directory('./cxic0114_run37')

# get the mean and rms of the gases
# make a trend of the 

ep2 = dsu.mk_mean_rms_hist(
    psana.Source('BldInfo(FEEGasDetEnergy)'),
    psana.Bld.BldDataFEEGasDetEnergyV1,
    ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',],
    'detectors',
    'Gas Detectors',
        )
myMPIrunner.add_event_process('ep2',ep2)


# add the EVR to the data getting routines
ep3 = dsu.mk_evr()
myMPIrunner.add_event_process('ep3',ep3)



ep4 = data_summary.event_process()
ep4.data = {}
ep4.set_reduction_step('gather')
ep4.set_reduction_args(ep4.data)
ep4.set_reduction_kwargs(root=0)
ep4.src = psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')
ep4.in_report = 'detectors'
ep4.title = 'Acqiris'

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
        print "{:} mean: {:0.2f}, std: {:0.2f}, min {:0.2f}, max {:0.2f}".format( evr, newdata.mean(), newdata.std(), newdata.min(), newdata.max() )
        ss.results['table'][evr] = {}
        ss.results['table'][evr]['Mean Arrival Bin'] = newdata.mean()
        ss.results['table'][evr]['RMS'] = newdata.std()
        ss.results['table'][evr]['min'] = newdata.min()
        ss.results['table'][evr]['max'] = newdata.max()

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

ep5 = dsu.mk_mean_rms_hist(
    psana.Source('BldInfo(EBeam)'),
    psana.Bld.BldDataEBeamV6,
    ['ebeamCharge','ebeamPhotonEnergy'],
    'detectors',
    'EBeam',
    histranges={'ebeamCharge':(0,.3), 'ebeamPhotonEnergy': (9000,10000)}
        )
myMPIrunner.add_event_process('ep5',ep5)

myMPIrunner.mpirun()

myMPIrunner.mk_output_html()
