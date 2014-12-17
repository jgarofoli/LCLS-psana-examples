import os
import time
import logging

import event_process
import output_html
import toolbox

import pylab
import numpy
import psana

from mpi4py import MPI
import pprint

#import code
#code.interact(None,None,locals())
#logger = logging.getLogger('data_summary.event_process_lib')

class epics_trend(event_process.event_process):
    def __init__(self):
        self.logger = logging.getLogger('data_summary.event_process_lib.epics_trend')
        self.output = {}
        self.reducer_rank = 0
        self.period_window = 1.
        self.channels_to_trend = []
        self.output['in_report'] = None
        self.output['in_report_title'] = None

    def beginJob(self):
        self.epics = self.parent.ds.env().epicsStore()
        self.allPvs = self.epics.names()
        self.trends = {}
        for chan in self.channels_to_trend:
            self.trends[chan] = toolbox.mytrend(self.period_window)
        return

    def add_pv_trend(self,chan):
        if chan not in self.channels_to_trend:
            self.channels_to_trend.append(chan)
        return

    def event(self,evt):
        this_ts = self.parent.shared['timestamp'][0] + self.parent.shared['timestamp'][1]/1.0e9
        for chan in self.channels_to_trend:
            val = self.epics.value(chan)     
            self.trends[chan].add_entry( this_ts, val )
        return


    def endJob(self):
        self.reduced_trends = {}
        for chan in self.channels_to_trend:
            self.reduced_trends[chan] = self.trends[chan].reduce(self.parent.comm,self.reducer_rank)

        if self.parent.rank == self.reducer_rank:
            self.output['figures'] = {}
            self.output['table'] = {}
            self.output['text'] = []
            self.output['text'].append('All available PVs in the EPICS store: <select><option>--</option>\n')
            for chan in self.allPvs:
                self.output['text'][-1] += '<option>{:}</option>\n'.format(chan)
            self.output['text'][-1] += '</select>\n'
            self.output['text'].append('PVs trended below the fold: <br/>\n<pre>')
            for chan in self.channels_to_trend:
                self.output['text'][-1] += chan+'\n'
            self.output['text'][-1] += '</pre>'
            fig = pylab.figure()
            for chan in self.channels_to_trend:
                self.output['figures'][chan] = {}
                fig.clear()
                thisxs    = self.reduced_trends[chan].getxs()
                thismeans = self.reduced_trends[chan].getmeans()
                thismins = self.reduced_trends[ chan].getmins()
                thismaxs = self.reduced_trends[ chan].getmaxs()
                pylab.plot(thisxs,thismeans,'k')
                pylab.plot(thisxs,thismaxs,'r')
                pylab.plot(thisxs,thismins,'b')
                pylab.title(chan)
                pylab.savefig( os.path.join( self.parent.output_dir, 'figure_trend_{:}.png'.format(chan.replace(':','_')) ))
                self.output['figures'][chan]['png'] = os.path.join( self.parent.output_dir, 'figure_trend_{:}.png'.format( chan.replace(':','_') ))
                # finish this section
            del fig
            self.parent.output.append(self.output)
        return

class counter(event_process.event_process):
    def __init__(self ):
        self.data  = numpy.array([0,])
        self.mergeddata = numpy.array([0,]) 
        self.logger = logging.getLogger('data_summary.event_process_lib.counter')
        return

    def event(self,evt):
        #id = evt.get(psana.EventId)
        #print 'rank', pp.rank, 'analyzed event with fiducials', id.fiducials()
        self.data[0] += 1
        return

    def endJob(self):
        self.parent.comm.Reduce([self.data, MPI.DOUBLE], [self.mergeddata, MPI.DOUBLE],op=MPI.SUM,root=self.reducer_rank)
        self.logger.info( "rank {:} events processed: {:}".format(self.parent.rank,self.data[0]) )
        if self.parent.rank == 0: #self.reducer_rank:
            self.logger.info( "total events processed: {:}".format(self.mergeddata[0]) )
            self.parent.shared['total_processed'] = self.mergeddata[0]
        return

class evr(event_process.event_process):
    def __init__(self):
        self.evr = []
        self.src = psana.Source('DetInfo(NoDetector.0:Evr.0)')
        self.logger = logging.getLogger('data_summary.event_process_lib.evr')
        return

    def beginJob(self):
        self.parent.evr = self.evr #maybe there is a better way? some sort of registry?
        self.parent.shared['evr'] = self.evr
        return

    def event(self,evt):
        evr = evt.get(psana.EvrData.DataV3, self.src)
        if evr is None:
            self.evr = []
        else:
            self.evr = [ff.eventCode() for ff in evr.fifoEvents()]

        self.parent.shared['evr'] = self.evr
        return

class time_fiducials(event_process.event_process):
    def __init__(self):
        self.timestamp = ()
        self.src = psana.EventId
        self.logger = logging.getLogger('data_summary.event_process_lib.time_fiducials')

    def beginJob(self):
        self.parent.timestamp = self.timestamp
        self.parent.shared['timestamp'] = self.timestamp

    def event(self,evt):
        ts = evt.get(self.src)
        if ts is None:
            self.timestamp = ()
        else :
            self.timestamp = ts.time()

        self.parent.shared['timestamp'] = self.timestamp
        return

class simple_trends(event_process.event_process):
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.logger = logging.getLogger('data_summary.event_process_lib.simple_trends')
        return

    def set_stuff(self,psana_src,psana_device,device_attrs,period_window,in_report=None,in_report_title=None):
        self.src         = psana.Source(psana_src)
        self.dev         = psana_device
        self.dev_attrs   = device_attrs
        self.period_window = period_window
        self.output['in_report'] = in_report
        self.output['in_report_title'] = in_report_title
        return

    def beginJob(self):
        self.trends = {}
        for attr in self.dev_attrs:
            self.trends[attr] = toolbox.mytrend(self.period_window)
        return

    def event(self, evt):
        gas = evt.get(self.dev,self.src)
        if gas is None:
            return
        this_ts = self.parent.shared['timestamp'][0] + self.parent.shared['timestamp'][1]/1.0e9
        for attr in self.dev_attrs:
            val = getattr(gas,attr)()     
            self.trends[attr].add_entry( this_ts, val )

    def endJob(self):
        self.reduced_trends = {}
        for attr in self.dev_attrs:
            self.reduced_trends[attr] = self.trends[attr].reduce(self.parent.comm,self.reducer_rank)

        if self.parent.rank == self.reducer_rank:
            self.output['figures'] = {}
            self.output['table'] = {}
            fig = pylab.figure()
            for attr in self.dev_attrs:
                self.output['figures'][attr] = {}
                fig.clear()
                thisxs    = self.reduced_trends[attr].getxs()
                thismeans = self.reduced_trends[attr].getmeans()
                thismins = self.reduced_trends[ attr].getmins()
                thismaxs = self.reduced_trends[ attr].getmaxs()
                pylab.plot(thisxs,thismeans,'k')
                pylab.plot(thisxs,thismaxs,'r')
                pylab.plot(thisxs,thismins,'b')
                pylab.title(attr)
                pylab.savefig( os.path.join( self.parent.output_dir, 'figure_trend_{:}.png'.format(attr) ))
                self.output['figures'][attr]['png'] = os.path.join( self.parent.output_dir, 'figure_trend_{:}.png'.format( attr ))
                # finish this section
            del fig
            self.parent.output.append(self.output)
        return

class simple_stats(event_process.event_process):
    def set_stuff(self,psana_src,psana_device,device_attrs,hist_ranges,in_report=None,in_report_title=None):
        self.src         = psana.Source(psana_src)
        self.dev         = psana_device
        if len(device_attrs) != len(hist_ranges):
            raise Exception('lenght mismatch between psana_device and hist_ranges')
        self.dev_attrs   = device_attrs # must be a list
        self.hist_ranges = hist_ranges  # must be a dict of the same length as dev_attrs
        self.output['in_report'] = in_report
        self.output['in_report_title'] = in_report_title
        self.logger = logging.getLogger('data_summary.event_process_lib.simple_stats')

    def beginJob(self):
        self.histograms = {}
        for attr in self.dev_attrs:
            self.histograms[attr] = toolbox.myhist(*self.hist_ranges[attr])
        return


    def event(self,evt):
        gas = evt.get(self.dev,self.src)
        if gas is None:
            return
        for attr in self.dev_attrs:
            val = getattr(gas,attr)()
            #print attr, val
            self.histograms[attr].fill( getattr(gas,attr)() )

    def endJob(self):
        self.reduced_histograms = {}
        for attr in self.dev_attrs:
            self.reduced_histograms[attr] = self.histograms[attr].reduce(self.parent.comm,self.reducer_rank)

        if self.parent.rank == self.reducer_rank:
            # plot those histograms
            self.output['figures'] = {}
            self.output['table'] = {}
            fig = pylab.figure()
            for attr in self.dev_attrs:
                self.output['figures'][attr] = {}
                fig.clear()
                #self.step = pylab.step( self.histograms[attr].edges, self.reduced_histograms[attr])
                # do this to make a filled step plot of the histogram
                newX, newY = self.reduced_histograms[attr].mksteps()
                pylab.fill_between( newX, 0, newY[:-1] )
                pylab.title( attr )
                pylab.xlim( self.histograms[attr].minrange, self.histograms[attr].maxrange )
                pylab.ylim( 0 , max(self.reduced_histograms[attr].binentries)*1.1 )
                pylab.savefig( os.path.join( self.parent.output_dir, 'figure_{:}.png'.format( attr ) ))
                self.output['figures'][attr]['png'] = os.path.join( self.parent.output_dir, 'figure_{:}.png'.format( attr ))

                self.output['table'][attr] = {}
                self.output['table'][attr]['Mean'] = self.reduced_histograms[attr].mean()
                self.output['table'][attr]['RMS'] = self.reduced_histograms[attr].std()
                self.output['table'][attr]['min'] = self.reduced_histograms[attr].minval
                self.output['table'][attr]['max'] = self.reduced_histograms[attr].maxval
            del fig
            self.parent.output.append(self.output)
        return


class acqiris(event_process.event_process):
    def __init__(self):
        self.data = {}
        self.output = {}
        self.logger = logging.getLogger('data_summary.event_process_lib.acqiris')
        return

    def set_stuff(self,src,in_report=None,in_report_title=None,histmin=400,histmax=450):
        self.src = psana.Source(src)
        self.output['in_report'] = in_report
        self.output['in_report_title'] = in_report_title
        self.histmin = histmin
        self.histmax = histmax
        return

    def event(self,evt):
        traces = evt.get(psana.Acqiris.DataDescV1,self.src)
        if traces is None:
            return
        trace = list(traces.data(5).waveforms()[0])
        peak = trace.index( max(trace) )
        for evr in self.parent.shared['evr']:
            #print "rank {:} evr {:} peak {:}".format(self.parent.rank, evr, peak )
            self.data.setdefault( evr, toolbox.myhist(500,0,500)).fill( peak )
        return

    def endJob(self):
        # do the stuff on all the other nodes (e.g. send stuff to reducer_rank)
        self.reduced_data = {}
        for evr in self.data:
            self.reduced_data[evr] = self.data[evr].reduce(self.parent.comm,self.reducer_rank)


        if self.parent.rank == self.reducer_rank:
            self.output['table'] = {}
            self.output['figures'] = {}
            fig = pylab.figure()
            for evr in sorted(self.reduced_data):
                fig.clear()
                #newdata = numpy.array( self.reduced_data[evr] )
                newdata = self.reduced_data[evr]
                self.logger.info( "{:} mean: {:0.2f}, std: {:0.2f}, min {:0.2f}, max {:0.2f}".format( evr, newdata.mean(), newdata.std(), newdata.minval, newdata.maxval ) )
                self.output['table'][evr] = {}
                self.output['table'][evr]['Mean Arrival Bin'] = newdata.mean()
                self.output['table'][evr]['RMS'] = newdata.std()
                self.output['table'][evr]['min'] = newdata.minval
                self.output['table'][evr]['max'] = newdata.maxval

                self.output['figures'][evr] = {}
                #hh = pylab.hist(newdata,bins=100,range=(0,100))
                newX, newY = self.reduced_data[evr].mksteps()
                hh = pylab.fill_between( newX, 0, newY[:-1] )
                pylab.title( 'evr '+repr(evr) )
                pylab.xlim(self.histmin,self.histmax)
                pylab.ylim( 0 , max(self.reduced_data[evr].binentries)*1.1 )
                #pylab.savefig( os.path.join( self.parent.output_dir, 'figure_evr_{:}.pdf'.format( evr ) ) )
                #self.output['figures'][evr]['pdf'] = os.path.join( self.parent.output_dir, 'figure_evr_{:}.pdf'.format( evr ) )
                pylab.savefig( os.path.join( self.parent.output_dir, 'figure_evr_{:}.png'.format( evr ) ) )
                self.output['figures'][evr]['png'] = os.path.join( self.parent.output_dir, 'figure_evr_{:}.png'.format( evr ) )
            del fig
            self.parent.output.append(self.output)
        return

class add_available_data(event_process.event_process):
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.event_keys = []
        self.config_keys = []
        self.logger = logging.getLogger('data_summary.event_process_lib.add_available_data')
        return

    def event(self,evt):
        if self.parent.rank == self.reducer_rank and len(self.event_keys) == 0:
            self.event_keys = evt.keys()
        if self.parent.rank == self.reducer_rank and len(self.config_keys) == 0:
            self.config_keys = self.parent.ds.env().configStore().keys()
        return

    def endJob(self):
        if self.parent.rank == self.reducer_rank:
            self.output = {'in_report': 'meta', 'in_report_title':'Available Data Sources'}
            self.output['text'] = []
            self.output['text'].append('Event Keys:<br/>\n<pre>' + pprint.pformat( self.event_keys )  + '</pre>')
            self.output['text'].append('Config Keys:<br/>\n<pre>' + pprint.pformat( self.config_keys )  + '</pre>')
            self.parent.output.append(self.output)
        return

class add_elog(event_process.event_process):
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.logger = logging.getLogger('data_summary.event_process_lib.add_available_data')
        return
    
    def beginJob(self):
        if self.parent.rank == self.reducer_rank:
            self.expNum = self.parent.ds.env().expNum()
        return

    def endJob(self):
        if self.parent.rank == self.reducer_rank:
            self.output = {'in_report': 'meta', 'in_report_title':'Elog'}
            self.output['text'] = "<a href=https://pswww.slac.stanford.edu/apps/portal/index.php?exper_id={:0.0f}>Elog</a>".format(self.expNum)
            self.parent.output.append(self.output)
        return

class store_report_results(event_process.event_process):
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.logger = logging.getLogger('data_summary.event_process_lib.store_report_results')
        return

    def endJob(self):
        self.parent.gather_output()
        if self.parent.rank == 0:
            self.output = {'in_report': 'meta', 'in_report_title':'Report Results'}
            self.output['text'] = "<a href=report.py>Report.py</a>"
            self.parent.output.append(self.output)
            self.parent.gathered_output.append(self.output)
            outfile = open( os.path.join(self.parent.output_dir,'report.py'), 'w' )
            outfile.write( 'report = ' )
            outfile.write( pprint.pformat( self.parent.gathered_output ) )
            outfile.close()
        return





class build_html(event_process.event_process):
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.logger = logging.getLogger('data_summary.event_process_lib.build_html')
        return

    def getsize(self,start_path = '.'):
        tt = 0
        nn = 0
        run = 'r{:04.0f}'.format(self.parent.run)
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                if 'xtc' in f.lower() and run in f.lower():
                    fp = os.path.join(dirpath,f)
                    tt += os.path.getsize(fp)
                    nn += 1
        return nn, tt

    def mk_output_html(self,gathered):
        if self.parent.rank != 0:
            self.logger.info( "mk_output_html rank {:} exiting".format(self.parent.rank) )
            return

        instr, exp = self.parent.exp.split('/')
        thisdir = os.path.join( '/reg/d/psdm/',instr.lower(),exp.lower(),'xtc')
        self.logger.info( "counting files in {:}".format(thisdir) )
        nfile, nbytes = self.getsize(start_path=thisdir)

        self.logger.info( "mk_output_html rank {:} continuing".format(self.parent.rank) )
        self.html = output_html.report(  self.parent.exp, self.parent.run, 
            title='{:} Run {:}'.format(self.parent.exp,self.parent.run),
            css=('css/bootstrap.min.css','jumbotron-narrow.css','css/mine.css'),
            script=('js/ie-emulation-modes-warning.js','js/jquery.min.js','js/toggler.js'),
            output_dir=self.parent.output_dir)

        self.html.start_block('Meta Data', id="metadata")  ##############################################################
                                                                                                                        #
        self.html.start_subblock('Data Information',id='datatime')  ##############################################      #
        self.html.page.p('Start Time: {:}<br/>End Time: {:}<br/>Duration: {:} seconds'.format(                   #      #
            time.ctime( self.parent.all_times[0].seconds()) ,                                                    #      #
            time.ctime(self.parent.all_times[-1].seconds()),                                                     #      #
            self.parent.all_times[-1].seconds()-self.parent.all_times[0].seconds() ) )                           #      #
        self.html.page.p('Total files: {:}<br/>Total bytes: {:} ({:0.1f} GB)<br/>'.format(nfile,nbytes,nbytes/(1024.**3)))
        self.html.end_subblock()                                    ##############################################      #
                                                                                                                        #
                                                                                                                        #
        self.html.start_subblock('Processing Information', id='datainfo')      ###################################      #
        self.html.page.p('Report time: {:}'.format(time.ctime()))                                                #      #
        self.html.page.p('Total events processed: {:} of {:}'.format(                                            #      #
            self.parent.shared['total_processed'], len(self.parent.all_times) ) )                                #      #
        self.html.page.p('Total processors: {:}'.format( self.parent.size ) )                                    #      #
        self.html.page.p('Wall Time: {:0.1f} seconds'.format( time.time() - self.parent.start_time ) )           #      #
        self.html.page.p('CPU Time: {:0.1f} seconds (accuracy ~10%)'.format( self.parent.cpu_time ))             #      #
        #self.html.page.p( "CPU time for final step on rank {:} : {:0.1f} seconds".format(                       #      #
            #self.rank, self.finaltime))                                                                         #      #
        self.html.end_subblock()                                               ###################################      #
                                                                                                                        #
        for thisep in sorted(gathered):                                                                                #
            if thisep['in_report'] == 'meta':                                                                     #
                ep = thisep['in_report_title'].replace(' ','_')
                self.html.start_subblock(thisep['in_report_title'],id=ep)                ################# a sub block #########    #
                if 'text' in thisep:
                    if isinstance(thisep['text'],list):
                        for p in thisep['text']:
                            self.html.page.p( p )
                    else:
                        self.html.page.p( thisep['text'] )
                if 'table' in thisep:
                    self.html.page.add( output_html.mk_table( thisep['table'] )() )                           #    #
                if 'figures' in thisep:
                    self.html.start_hidden(ep)                                       ######### the hidden part ##     #    #
                    for img in sorted(thisep['figures']):                                               #     #    #
                        self.html.page.img(src=os.path.basename(thisep['figures'][img]['png']),style='width:49%;')        #     #    #
                    self.html.end_hidden()                                           ############################     #    #
                self.html.end_subblock()                                    #######################################    #
                                                                                                                        #
        self.html.end_block()          ##################################################################################

        self.html.start_block('Detector Data', id="detectordata") ################################## a block ########### 
                                                                                                                       #
        for thisep in sorted(gathered):                                                                                #
            if thisep['in_report'] == 'detectors':                                                                     #
                ep = thisep['in_report_title'].replace(' ','_')
                self.html.start_subblock(thisep['in_report_title'],id=ep)                ################# a sub block #########    #
                if 'text' in thisep:
                    if isinstance(thisep['text'],list):
                        for p in thisep['text']:
                            self.html.page.p( p )
                    else:
                        self.html.page.p( thisep['text'] )
                if 'table' in thisep:
                    self.html.page.add( output_html.mk_table( thisep['table'] )() )                           #    #
                if 'figures' in thisep:
                    self.html.start_hidden(ep)                                       ######### the hidden part ##     #    #
                    for img in sorted(thisep['figures']):                                               #     #    #
                        self.html.page.img(src=os.path.basename(thisep['figures'][img]['png']),style='width:49%;')        #     #    #
                    self.html.end_hidden()                                           ############################     #    #
                self.html.end_subblock()                                    #######################################    #
                                                                                                                       #
                                                                                                                       #
        self.html.end_block()                                      #####################################################

        self.html.start_block('Analysis', id='analysis')
        self.html.page.p('This is empty.')
        self.html.end_block()

        self.html.start_block('Logging', id='logging')   ######################################## a block #############
        self.html.page.p('link to LSF log file.')                                                                     #
        logs = ','.join(['<a href="log_{0:}.log">log {0:}</a> '.format(x) for x in xrange(self.parent.size) ])
        self.html.page.p('Subjob log files: {:}'.format(logs) )
        if len(self.parent.previous_versions) > 0:                                                                           #
            self.html.start_subblock('Previous Versions',id='prevver') ###################### a sub block ########    #
            self.html.start_hidden('prevver')                             ############## hidden part ####        #    #
            self.html.page.table(class_='table table-condensed')                                        #        #    #
            self.html.page.thead()                                                                      #        #    #
            self.html.page.tr()                                                                         #        #    #
            self.html.page.td('link')                                                                   #        #    #
            self.html.page.td('date')                                                                   #        #    #
            self.html.page.tr.close()                                                                   #        #    #
            self.html.page.thead.close()                                                                #        #    #
            self.parent.previous_versions.reverse()                                                     #        #    #
            for a,b in self.parent.previous_versions:                                                   #        #    #
                self.html.page.tr()                                                                     #        #    #
                self.html.page.td(a)                                                                    #        #    #
                self.html.page.td(b)                                                                    #        #    #
                self.html.page.tr.close()                                                               #        #    #
            self.html.page.table.close()                                                                #        #    #
            self.html.end_hidden()                                        ###############################        #    #
                                                                                                                 #    #
            self.html.end_subblock()                                   ###########################################    #
        self.html.end_block()                            ##############################################################

        # this closes the left column
        self.html.page.div.close()

        self.html.mk_nav()

        self.html._finish_page()

        self.logger.info( "mk_output_html rank {:} outputing file...".format(self.parent.rank) )
        self.html.myprint(tofile=True)
        self.logger.info( "mk_output_html rank {:} outputing file... finished".format(self.parent.rank) )

        return
    def make_report(self,gathered):
        #print gathered
        self.mk_output_html(gathered)
        return

    def endJob(self):
        self.parent.gather_output()
        if self.parent.rank == 0:
            self.make_report(self.parent.gathered_output)
        return

