from mpi4py import MPI
import logging
import os
import output_html
import psana
import time
import math

__version__ = 0.2


class job(object):
    def __init__(self):
        self.subjobs = []
        self.ds = None
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.maxEventsPerNode = 5000
        self.all_times = []
        self.shared = {}
        self.output = []
        self.output_dir = None
        self.gathered_output = []
        self.previous_versions = []
        self.start_time = time.time()
        self.logger = logging.getLogger('data_summary.job.r{:0.0f}'.format( self.rank ))
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
        self.logger_fh = logging.FileHandler('log_{:0.0f}.log'.format(self.rank))
        self.logger_fh.setLevel(logging.DEBUG)
        self.logger_fh.setFormatter( logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s' ) )
        self.logger.addHandler( self.logger_fh )
        self.logger.debug( "output directory is "+self.output_dir )
        return

    def set_maxEventsPerNode(self,n):
        self.maxEventsPerNode = n
        return

    def set_datasource(self,exp=None,run=None):
        self.exp = exp
        self.run = run
        instr, thisexp = exp.split('/')
        self.set_outputdir(os.path.join( os.path.abspath('.') ,'{:}_run{:0.0f}'.format(thisexp,run)))

        self.ds = psana.DataSource('exp={:}:run={:0.0f}:idx'.format(exp,run))

        return

    def add_event_process(self,sj):
        sj.set_parent(self)
        
        sj.logger = logging.getLogger( self.logger.name + '.' + sj.logger.name.split('.')[-1] )
        #sj.logger.addHandler(self.logger_fh)
        self.subjobs.append(sj)

    def gather_output(self):
        gathered_output = self.comm.gather( self.output, root=0 )
        timing = self.comm.gather(self.cputotal, root=0)
        if self.rank == 0:
            self.cpu_time = sum( timing )
            if len(self.gathered_output) != 0:
                return
            for go in gathered_output:
                self.gathered_output.extend( go )
        return

    def dojob(self): # the main loop
        self.cpustart = time.time()
        self.logger.info( "rank {:} starting".format( self.rank ) )
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
                    self.logger.ERROR( "**** event fetch failed ({:}) : rank {:}".format(mytimes[ii],self.rank) )
                    continue

                for sj in self.subjobs:
                    sj.event(evt)

            for sj in self.subjobs:
                sj.endRun()

        self.logger.info( "rank {:} finishing".format( self.rank ) )
        self.cputotal = time.time() - self.cpustart
        for sj in self.subjobs:
            sj.endJob()

        return
