from mpi4py import MPI
import logging
import data_summary_utils
import os
import output_html
import psana
import time
import math

__version__ = 0.2


class job(object):
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.maxEventsPerNode = 5000
        self.maxEventsPerNode = 100
        self.event_processes = {}
        self.finalize = lambda : True
        self._output_dir = './'
        self.start_time = time.time()
        self.cpu_time = 0.
        self.previous_versions = []
        return

    def set_maxEventsPerNode(self,n):
        self.maxEventsPerNode = n
        return

    def smart_rename(self,out):
        if out == './':
            return
        while out[-1] == '/':
            out = out[:-1]
        ii = 0
        while True:
            if not os.path.isdir(out+'.{:02.0f}'.format(ii)):
                os.rename(out,out+'.{:02.0f}'.format(ii))
                break
            else:
                self.previous_versions.append( [out+'.{:02.0f}'.format(ii),] )
                if os.path.isdir(out+'.{:02.0f}'.format(ii)) and os.path.isfile( out+'.{:02.0f}'.format(ii) +'/report.html'):
                    self.previous_versions[-1].append( time.ctime( os.path.getctime(  out+'.{:02.0f}'.format(ii) +'/report.html' ) ) )
                else: 
                    self.previous_versions[-1].append( None )
                ii += 1
                continue
        return
                     
    def set_output_directory(self,out):
        if not os.path.isdir(out) and self.rank==0:
            os.mkdir(out)
        elif os.path.isdir(out) and self.rank==0:
            self.smart_rename(out)
            os.mkdir(out)
        self._output_dir = out
        time.sleep(1)
        os.chdir(out)


    def set_datasource(self,exp=None,run=None):
        #self.ds = ds
        self.exp = exp
        self.run = run
        self.ds = psana.DataSource('exp={:}:run={:0.0f}:idx'.format(exp,run))
        self.set_output_directory(os.path.join('/reg/neh/home/justing/','{:}_run{:0.0f}'.format(exp,run)))
        return

    def add_event_process(self,name,ep):
        if not name in self.event_processes:
            self.event_processes[name] = ep
        else:
            raise run_summary_utils.AddEventProcessError('that name is already taken')
        return

    def set_finalize(self,newfinal):
        self.finalize = newfinal
        return

    def mpirun(self):
        cpustart = time.time()
        for run in self.ds.runs():
            times = run.times()
            if self.rank == 0:
                self.all_times = times
            mylength = int(math.ceil(float(len(times))/self.size))
            if mylength > self.maxEventsPerNode:
                mylength = self.maxEventsPerNode
            mytimes = times[self.rank*mylength:(self.rank+1)*mylength]

            if mylength > len(mytimes):
                mylength = len(mytimes)

            print "rank {:} processing {:} events".format(self.rank, mylength)
            for ii in xrange(mylength):
                evt = run.event(mytimes[ii])
                if evt is None:
                    print "**** event fetch failed : rank", self.rank
                    continue
                
                # do generic stuff here
                for ep in sorted(self.event_processes):
                    self.event_processes[ep].process_event(self,evt)


        for ep in sorted(self.event_processes):
            if self.event_processes[ep].doreduce:
                print "rank", self.rank, "reducing", ep
                # I AM DISSASISFIED WITH THIS PART:
                #self.comm.Reduce([self.event_processes[ep].data, MPI.DOUBLE]
                        #,[self.event_processes[ep].mergeddata, MPI.DOUBLE], op=MPI.SUM,root=0) # more generic stuff here
                # this is better
                if self.event_processes[ep].reduction_step == 'gather':
                    self.event_processes[ep].gathered = getattr(self.comm,self.event_processes[ep].reduction_step)( *self.event_processes[ep].reduction_args, **self.event_processes[ep].reduction_kwargs )
                else :
                    getattr(self.comm,self.event_processes[ep].reduction_step)( *self.event_processes[ep].reduction_args, **self.event_processes[ep].reduction_kwargs )

        self.cputotal = time.time() - cpustart
        self.allcputtotal = self.comm.gather(self.cputotal, root=0)
        print "rank {:} cpu time {:}".format( self.rank, self.cputotal )
        if self.rank == 0:
            finaltimestart = time.time()
            for ep in sorted(self.event_processes):
                self.event_processes[ep].finish()
            self.finalize()
            self.cpu_time = sum( self.allcputtotal )
            print "total CPU time {:} seconds".format(self.cpu_time)
            self.finaltime = time.time() - finaltimestart
            print "CPU time for final step on rank {:} : {:} seconds".format(self.rank, self.finaltime)
        return


    def mk_output_html(self):
        if self.rank != 0:
            print "mk_output_html rank {:} exiting".format(self.rank)
            return

        print "mk_output_html rank {:} continuing".format(self.rank)
        self.html = output_html.report(  self.exp, self.run, 
            title='{:} Run {:}'.format(self.exp,self.run),
            css=('css/bootstrap.min.css','jumbotron-narrow.css','css/mine.css'),
            script=('js/ie-emulation-modes-warning.js','js/jquery.min.js','js/toggler.js'),
            output_dir='/reg/neh/home/justing/{:}_run{:}/'.format(self.exp,self.run))

        self.html.start_block('Meta Data', id="metadata")  ##############################################################
                                                                                                                        #
        self.html.start_subblock('Data Information',id='datatime')  ##############################################      #
        self.html.page.p('Start Time: {:}<br/>End Time: {:}<br/>Duration: {:} seconds'.format(                   #      #
            time.ctime( self.all_times[0].seconds()) ,                                                           #      #
            time.ctime(self.all_times[-1].seconds()),                                                            #      #
            self.all_times[-1].seconds()-self.all_times[0].seconds() ) )                                         #      #
        self.html.end_subblock()                                    ##############################################      #
                                                                                                                        #
                                                                                                                        #
        self.html.start_subblock('Processing Information', id='datainfo')      ###################################      #
        self.html.page.p('Report time: {:}'.format(time.ctime()))                                                #      #
        self.html.page.p('Total events processed: {:} of {:}'.format(                                            #      #
            self.event_processes['ep1'].mergeddata[0], len(self.all_times) ) )                                   #      #
        self.html.page.p('Total processors: {:}'.format( self.size ) )                                           #      #
        self.html.page.p('Wall Time: {:0.1f} seconds'.format( time.time() - self.start_time ) )                  #      #
        self.html.page.p('CPU Time: {:0.1f} seconds (accuracy ~10%)'.format( self.cpu_time ))                    #      #
        self.html.page.p( "CPU time for final step on rank {:} : {:0.1f} seconds".format(                        #      #
            self.rank, self.finaltime))                                                                          #      #
        self.html.end_subblock()                                               ###################################      #
                                                                                                                        #
                                                                                                                        #
        self.html.end_block()          ##################################################################################

        self.html.start_block('Detector Data', id="detectordata") ################################## a block ########### 
                                                                                                                       #
        for ep in sorted(self.event_processes):                                                                        #
            thisep = self.event_processes[ep]                                                                          #
            if thisep.in_report == 'detectors':                                                                        #
                self.html.start_subblock(thisep.title,id=ep)                ################# a sub block #########    #
                self.html.page.add( output_html.mk_table( thisep.results['table'] )() )                           #    #
                self.html.start_hidden(ep)                                       ######### the hidden part ##     #    #
                for img in sorted(thisep.results['figures']):                                               #     #    #
                    self.html.page.img(src=thisep.results['figures'][img]['png'],style='width:49%;')        #     #    #
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
        if len(self.previous_versions) > 0:                                                                           #
            self.html.start_subblock('Previous Versions',id='prevver') ###################### a sub block ########    #
            self.html.start_hidden('prevver')                             ############## hidden part ####        #    #
            self.html.page.table(class_='table table-condensed')                                        #        #    #
            self.html.page.thead()                                                                      #        #    #
            self.html.page.tr()                                                                         #        #    #
            self.html.page.td('link')                                                                   #        #    #
            self.html.page.td('date')                                                                   #        #    #
            self.html.page.tr.close()                                                                   #        #    #
            self.html.page.thead.close()                                                                #        #    #
            self.previous_versions.reverse()                                                            #        #    #
            for a,b in self.previous_versions:                                                          #        #    #
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

        print "mk_output_html rank {:} outputing file...".format(self.rank)
        self.html.myprint(tofile=True)
        print "mk_output_html rank {:} outputing file... finished".format(self.rank)

        return




class job_v2(object):
    def __init__(self):
        self.subjobs = []
        self.ds = None
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.maxEventsPerNode = 5000
        #self.maxEventsPerNode = 360
        self.all_times = []
        self.shared = {}
        self.output = []
        self.output_dir = None
        self.gathered_output = []
        self.previous_versions = []
        self.start_time = time.time()
        return

    def smart_rename(self,out):
        if out == './':
            return
        while out[-1] == '/':
            out = out[:-1]
        ii = 0
        while True:
            if not os.path.isdir(out+'.{:02.0f}'.format(ii)):
                os.rename(out,out+'.{:02.0f}'.format(ii))
                break
            else:
                self.previous_versions.append( [out+'.{:02.0f}'.format(ii),] )
                if os.path.isdir(out+'.{:02.0f}'.format(ii)) and os.path.isfile( out+'.{:02.0f}'.format(ii) +'/report.html'):
                    self.previous_versions[-1].append( time.ctime( os.path.getctime(  out+'.{:02.0f}'.format(ii) +'/report.html' ) ) )
                else: 
                    self.previous_versions[-1].append( None )
                ii += 1
                continue
        return
                     
    def set_outputdir(self,*args):
        if len(args) == 1:
            self.output_dir = args[0]
        if not os.path.isdir(self.output_dir) and self.rank==0:
            os.mkdir(self.output_dir)
        elif os.path.isdir(self.output_dir) and self.rank==0:
            self.smart_rename(self.output_dir)
            os.mkdir(self.output_dir)
        time.sleep(1)
        os.chdir(self.output_dir)
        return

    def set_datasource(self,exp=None,run=None):
        self.exp = exp
        self.run = run
        self.ds = psana.DataSource('exp={:}:run={:0.0f}:idx'.format(exp,run))
        instr, thisexp = exp.split('/')
        self.set_outputdir(os.path.join( os.path.abspath('.') ,'{:}_run{:0.0f}'.format(thisexp,run)))
        print "output directory is", self.output_dir
        return

    def add_event_process(self,sj):
        sj.set_parent(self)
        self.subjobs.append(sj)



    def gather_output(self):
        gathered_output = self.comm.gather( self.output, root=0 )
        timing = self.comm.gather(self.cputotal, root=0)
        if self.rank == 0:
            self.cpu_time = sum( timing )
            for go in gathered_output:
                self.gathered_output.extend( go )
        return

    def dojob(self): # the main loop
        self.cpustart = time.time()
        # assign reducer_rank for the subjobs (just cycle through the available nodes)
        ranks = range(self.size)
        for ii,sj in enumerate(self.subjobs):
            sj.reducer_rank = ranks[ ii % len(ranks) ]


        for sj in self.subjobs:
            sj.beginJob()

        for run in self.ds.runs():
            times = run.times()
            if self.rank == 0:
                self.all_times.extend(times)
            mylength = int(math.ceil(float(len(times))/self.size))
            if mylength > self.maxEventsPerNode:
                mylength = self.maxEventsPerNode
            mytimes = times[self.rank*mylength:(self.rank+1)*mylength]

            if mylength > len(mytimes):
                mylength = len(mytimes)

            for sj in self.subjobs:
                sj.beginRun()

            for ii in xrange(mylength):
                evt = run.event(mytimes[ii])
                if evt is None:
                    print "**** event fetch failed ({:}) : rank {:}".format(mytimes[ii],self.rank)
                    continue

                for sj in self.subjobs:
                    sj.event(evt)

            for sj in self.subjobs:
                sj.endRun()

        self.cputotal = time.time() - self.cpustart
        for sj in self.subjobs:
            sj.endJob()
        return
