import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
import jutils
import data_summary

# just some comment

ps = argparse.ArgumentParser()

ps.add_argument("exp",
        help="the experiment, e.g. CXI/cxic0114")

ps.add_argument("run",type=int,
        help="run to process, e.g. 111")

ps.add_argument("--max-events-per-node","-M",type=int,default=500,dest='max_events',
        help="maximum events to process per node")

ps.add_argument("--plot-vs","-X",action='append',default=['time',], dest="x_axes",
        help="pass in channels to plot against, can be passed multiple times")

ps.add_argument("--verbose", '-v', action='count', default=4, dest="verbosity",
        help="verbosity level of logging, default is 4 (INFO), choices are 1-5 (CRITICAL, ERROR, WARNING, INFO, DEBUG), can pass -v multiple times")

ps.add_argument("--xkcd", "-x", action="store_true", default=False, dest="xkcd",
        help="use XKCD plot sytle")

args = ps.parse_args()

verbosity_levels = ["CRITICAL","ERROR","WARNING","INFO","DEBUG"]
if args.verbosity != 4:
    args.verbosity -= 4
data_summary.set_logger_level(verbosity_levels[ args.verbosity-1 ]) # choose one of DEBUG INFO WARNING ERROR CRITICAL

if args.xkcd:
    matplotlib.pyplot.xkcd() # 

myMPIrunner = data_summary.job()

myMPIrunner.set_datasource(exp=args.exp,run=args.run)
myMPIrunner.set_maxEventsPerNode(args.max_events)
myMPIrunner.set_x_axes(args.x_axes)
# other choices are (for CXI): CXI:INS:CLC:DIAT1 (transmission first harmonic)
#                              CXI:INS:CLC:DIAT2 (2nd harmonic)
#                              CXI:INS:CLC:DIAT3 (3rd harmonic)

# add some standard stuff that other event processors may use
myMPIrunner.add_event_process( data_summary.counter()                       )
myMPIrunner.add_event_process( data_summary.evr()                           )
myMPIrunner.add_event_process( data_summary.time_fiducials()                )
myMPIrunner.add_event_process( data_summary.add_available_data()            )

myMPIrunner.add_event_process( data_summary.add_elog()                      )

# this one automatically picks up the devices that are in both the devices_dict and the data source
myMPIrunner.add_event_process( 
        data_summary.add_all_devices( data_summary.devices['device_sets'] ) )

# this has to be at the end
myMPIrunner.add_event_process( data_summary.store_report_results()          )
# this has to really last
myMPIrunner.add_event_process( data_summary.build_html()                    ) 

# do the job
myMPIrunner.dojob()
