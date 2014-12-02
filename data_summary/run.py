from mpi4py import MPI
import logging
import data_summary_utils
import os
import output_html
import psana
import time

__version__ = 0.1


class mpi_runner:
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.maxEventsPerNode = 5000
        self.event_processes = {}
        self.finalize = lambda : True
        self._output_dir = './'
        self.start_time = time.time()
        return

    def set_maxEventsPerNode(self,n):
        self.maxEventsPerNode = n
        return

    def set_output_directory(self,out):
        if not os.path.isdir(out) and self.rank==0:
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
        for run in self.ds.runs():
            times = run.times()
            if self.rank == 0:
                self.all_times = times
            mylength = len(times)/self.size
            if mylength > self.maxEventsPerNode:
                mylength = self.maxEventsPerNode
            mytimes = times[self.rank*mylength:(self.rank+1)*mylength]

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

        if self.rank == 0:
            for ep in sorted(self.event_processes):
                self.event_processes[ep].finish()
            self.finalize()
        return

    def mk_output_html(self):
        if self.rank != 0:
            return

        self.html = output_html.report(  self.exp, self.run, 
            title='{:} Run {:}'.format(self.exp,self.run),
            css=('css/bootstrap.min.css','jumbotron-narrow.css','css/mine.css'),
            script=('js/ie-emulation-modes-warning.js','https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js','js/toggler.js'),
            output_dir='/reg/neh/home/justing/{:}_run{:}/'.format(self.exp,self.run))

        self.html.start_block('Meta Data', id="metadata")  ##############################################################
                                                                                                                        #
        self.html.start_subblock('Data Information',id='datatime')  ##############################################      #
        self.html.page.p('Start Time: {:}<br/>End Time: {:}<br/>Duration: {:}'.format( 
            time.ctime( self.all_times[0].seconds()) , 
            time.ctime(self.all_times[-1].seconds()), 
            self.all_times[-1].seconds()-self.all_times[0].seconds() ) )          #      #
                                                                         #########################################      #
                                                                                                                        #
        self.html.start_subblock('Processing Information', id='datainfo')      ###################################      #
        self.html.page.p('Total events processed: {:}'.format( self.event_processes['ep1'].mergeddata[0] ) )     #      #
        self.html.page.p('Total processors: {:}'.format( self.size ) )                                           #      #
        self.html.page.p('Wall Time: {:0.1f}'.format( time.time() - self.start_time ) )
                                                                                                                 #      #
                                                                         #########################################      #
                                                                                                                        #
        self.html.end_block()          ##################################################################################

        self.html.start_block('Detector Data', id="detectordata") #######################################################  a block
                                                                                                                        #
        self.html.start_subblock('Gas Detectors',id='gasdet')   ####################################################    #
        self.html.page.add( output_html.mk_table( self.event_processes['ep2'].results['table'] )() )               #    #
        self.html.start_hidden('gasdet')                                                                           #    #
        for img in sorted(self.event_processes['ep2'].results['figures']):                                                 #    #
            self.html.page.img(src=self.event_processes['ep2'].results['figures'][img]['png'],style='width:49%;')  #    #
        self.html.end_hidden()                                  ####################################################    #
                                                                                                                        #
        self.html.start_subblock('Acqiris Detectors',id='acqdet')  #################################################    #
        self.html.page.add( output_html.mk_table( self.event_processes['ep4'].results['table'] )() )               #    #
        self.html.start_hidden('acqdet')                                                                           #    #
        for img in sorted(self.event_processes['ep4'].results['figures']):                                                 #    #
            self.html.page.img(src=self.event_processes['ep4'].results['figures'][img]['png'],style='width:49%;')  #    #
        self.html.end_hidden()                                     #################################################    #
                                                                                                                        #
        self.html.end_block()     #######################################################################################

        self.html.start_block('Analysis', id='analysis')
        self.html.end_block()

        # this closes the left column
        self.html.page.div.close()

        self.html.mk_nav()

        self.html._finish_page()
        self.html.myprint(tofile=True)

        return





