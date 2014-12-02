from mpi4py import MPI
import logging
import data_summary_utils
import os
import output_html


class mpi_runner:
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.maxEventsPerNode = 100
        self.event_processes = {}
        self.finalize = lambda : True
        self._output_dir = './'
        return

    def set_maxEventsPerNode(self,n):
        self.maxEventsPerNode = n
        return

    def set_output_directory(self,out):
        if not os.path.isdir(out):
            os.mkdir(out)
        self._output_dir = out
        os.chdir(out)


    def set_datasource(self,ds):
        self.ds = ds
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

        return





