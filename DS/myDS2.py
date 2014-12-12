import jutils
import data_summary
from mpi4py import MPI
import psana

myMPIrunner = data_summary.job_v2()
myMPIrunner.set_datasource(exp='CXI/cxif7214',run=205)

myMPIrunner.add_event_process( data_summary.counter() )
myMPIrunner.add_event_process( data_summary.evr() )
myMPIrunner.add_event_process( data_summary.time_fiducials() )

ebeam = data_summary.simple_stats()
ebeam.set_stuff(
    psana.Source('BldInfo(EBeam)'),
    psana.Bld.BldDataEBeamV6,
    ['ebeamCharge','ebeamPhotonEnergy'],
    {'ebeamCharge':(100,0,.3), 'ebeamPhotonEnergy': (500,9000,10000)}
    )
myMPIrunner.add_event_process(ebeam)

gasdets = data_summary.simple_stats()
gasdets.set_stuff(
    psana.Source('BldInfo(FEEGasDetEnergy)'),
    psana.Bld.BldDataFEEGasDetEnergyV1,
    ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',],
    {'f_11_ENRC': (100,0,5), 'f_12_ENRC': (100,0,5),'f_21_ENRC': (100,0,5),'f_22_ENRC': (100,0,5),'f_63_ENRC': (100,0,5),'f_64_ENRC': (100,0,5),},
    )
myMPIrunner.add_event_process(gasdets)


gasdets_trends = data_summary.simple_trends()
gasdets_trends.set_stuff(
    psana.Source('BldInfo(FEEGasDetEnergy)'),
    psana.Bld.BldDataFEEGasDetEnergyV1,
    ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',],
    1.0
    )
myMPIrunner.add_event_process(gasdets_trends)


acqiris = data_summary.acqiris() 
acqiris.set_stuff( 
    psana.Source('DetInfo(CxiEndstation.0:Acqiris.0)')
        )
myMPIrunner.add_event_process( acqiris )



#myMPIrunner.add_event_process( mk_output ) # not written yet
myMPIrunner.dojob()
