import matplotlib
matplotlib.use('Agg')

import jutils
import data_summary
import psana

"""
$> mpirun -n 4 python myDS.py
"""


myMPIrunner = data_summary.job()
myMPIrunner.set_datasource(exp='CXI/cxif7214',run=205)
myMPIrunner.set_maxEventsPerNode(500)

myMPIrunner.add_event_process( data_summary.counter() )
myMPIrunner.add_event_process( data_summary.evr() )
myMPIrunner.add_event_process( data_summary.time_fiducials() )
myMPIrunner.add_event_process( data_summary.add_available_data() )
myMPIrunner.add_event_process( data_summary.add_elog() )

ebeam = data_summary.simple_stats()
ebeam.set_stuff(
    'BldInfo(EBeam)',
    psana.Bld.BldDataEBeamV6,
    ['ebeamCharge','ebeamPhotonEnergy'],
    {'ebeamCharge':(100,0,.3), 'ebeamPhotonEnergy': (500,9000,10000)},
    in_report='detectors',
    in_report_title = 'Ebeam Stats'
    )
myMPIrunner.add_event_process(ebeam)

gasdets = data_summary.simple_stats()
gasdets.set_stuff(
    'BldInfo(FEEGasDetEnergy)',
    psana.Bld.BldDataFEEGasDetEnergyV1,
    ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',],
    {'f_11_ENRC': (100,0,5), 'f_12_ENRC': (100,0,5),'f_21_ENRC': (100,0,5),'f_22_ENRC': (100,0,5),'f_63_ENRC': (100,0,5),'f_64_ENRC': (100,0,5),},
    in_report='detectors',
    in_report_title = 'Gas Detector Stats'
    )
myMPIrunner.add_event_process(gasdets)


gasdets_trends = data_summary.simple_trends()
gasdets_trends.set_stuff(
    'BldInfo(FEEGasDetEnergy)',
    psana.Bld.BldDataFEEGasDetEnergyV1,
    ['f_11_ENRC', 'f_12_ENRC','f_21_ENRC','f_22_ENRC','f_63_ENRC','f_64_ENRC',],
    1.0,
    in_report='detectors',
    in_report_title='Gas Detector Trends'
    )
myMPIrunner.add_event_process(gasdets_trends)

ebeam_trends = data_summary.simple_trends()
ebeam_trends.set_stuff(
    'BldInfo(EBeam)',
    psana.Bld.BldDataEBeamV6,
    ['ebeamCharge','ebeamPhotonEnergy'],
    1.0,
    in_report='detectors',
    in_report_title='Ebeam Trends'
    )
myMPIrunner.add_event_process(ebeam_trends)

acqiris = data_summary.acqiris() 
acqiris.set_stuff( 
    'DetInfo(CxiEndstation.0:Acqiris.0)',
    in_report='detectors',
    in_report_title='Acqiris Stats'
        )
myMPIrunner.add_event_process( acqiris )


myMPIrunner.add_event_process( data_summary.store_report_results() )
myMPIrunner.add_event_process( data_summary.build_html() ) # this has to be last

myMPIrunner.dojob()
