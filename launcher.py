import argparse
import matplotlib
matplotlib.use('Agg')
import jutils
import data_summary

ps = argparse.ArgumentParser()


ps.add_argument("exp",help="the experiment, e.g. CXI/cxic0114")
ps.add_argument("run",help="run to process, e.g. 111",type=int)
ps.add_argument("--max-events-per-node","-M",type=int,help="maximum events to process per node",default=500,dest='max_events')
args = ps.parse_args()

data_summary.set_logger_level('INFO') # choose one of DEBUG INFO WARNING ERROR CRITICAL
myMPIrunner = data_summary.job()

myMPIrunner.set_datasource(exp=args.exp,run=args.run)
myMPIrunner.set_maxEventsPerNode(args.max_events)

myMPIrunner.add_event_process( data_summary.counter() )
myMPIrunner.add_event_process( data_summary.evr() )
myMPIrunner.add_event_process( data_summary.time_fiducials() )
myMPIrunner.add_event_process( data_summary.add_available_data() )
myMPIrunner.add_event_process( data_summary.add_elog() )

myMPIrunner.add_event_process( data_summary.add_all_devices( data_summary.devices['device_sets'] ) )


#for dev in sorted(data_summary.devices['device_sets']):
#    print dev, ":"
#    if 'summary_report' in data_summary.devices['device_sets']:
#        print data_summary.devices['device_sets']['summary_report']
#
myMPIrunner.add_event_process( data_summary.store_report_results() )
myMPIrunner.add_event_process( data_summary.build_html() ) # this has to be last

myMPIrunner.dojob()
