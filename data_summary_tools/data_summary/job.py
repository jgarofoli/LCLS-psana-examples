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
        self.x_axes = ['time',]
        self.logger = logging.getLogger(__name__+'.r{:0.0f}'.format( self.rank ))
        self.start_time = time.time()
        self.logger.info('start time is {:}'.format(self.start_time))
        self.eventN = 0
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
                self.previous_versions.append( [out+'.{:02.0f}'.format(ii),] )
                if os.path.isdir(out+'.{:02.0f}'.format(ii)) and os.path.isfile( out+'.{:02.0f}'.format(ii) +'/report.html'):
                    self.previous_versions[-1].append( time.ctime( os.path.getctime(  out+'.{:02.0f}'.format(ii) +'/report.html' ) ) )
                else: 
                    self.previous_versions[-1].append( None )
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
        self.logger_fh.setFormatter( logging.Formatter( '%(asctime)s - %(levelname)s - %(name)s - %(message)s' ) )
        self.logger.addHandler( self.logger_fh )
        self.logger.info( "output directory is "+self.output_dir )
        return

    def set_maxEventsPerNode(self,n):
        self.maxEventsPerNode = n
        return

    def set_datasource(self,exp=None,run=None):
        self.exp = exp
        self.run = run
        instr, thisexp = exp.split('/')
        self.set_outputdir(os.path.join( os.path.abspath('.') ,'{:}_run{:0.0f}'.format(thisexp,run)))

        self.logger.info('connecting to data source')
        self.ds = psana.DataSource('exp={:}:run={:0.0f}:idx'.format(exp,run))
        if self.ds.empty():
            self.logger.error('data source is EMPTY!')
        self.logger.info('preparing to analyze {:} run {:}'.format(exp,run))
        return

    def set_x_axes(self,xaxes):
        self.x_axes = xaxes
        return

    def add_event_process(self,sj):
        sj.set_parent(self)
        
        sj.logger = logging.getLogger( self.logger.name + '.' + sj.logger.name.split('.')[-1] )
        #sj.logger.addHandler(self.logger_fh)
        self.subjobs.append(sj)

    def check_subjobs(self, gsj):
        data = {}
        for ii in xrange(self.comm.size) :
            data[ii] = gsj[ii]
        # make the unified list of jobs, that all the ranks should replicate.
        if len(data) > 1:
            pass
        return data

    def update_subjobs_before_endJob(self):
        #self.scattered_subjobs
        # reorder subjobs if necessary
        # add subjobs if necessary so all can reduce
        return

    def unify_ranks(self):
        self.gathered_subjobs = self.comm.gather( [sj.describe_self() for sj in self.subjobs], root=0 )
        if self.rank == 0:
            self.scattered_subjobs = self.check_subjobs( self.gathered_subjobs )
        else:
            self.scattered_subjobs = None
        self.scattered_subjobs = self.comm.scatter(self.scattered_subjobs, root=0 )
        # instantiate the necessary subjobs in the right order (or reorder them, or whatever)
        # and update the list of subjobs such that they are identical across all ranks.
        self.update_subjobs_before_endJob()
        return

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
                self.evt = run.event(mytimes[ii])
                self.eventN = ii
                if self.evt is None:
                    self.logger.ERROR( "**** event fetch failed ({:}) : rank {:}".format(mytimes[ii],self.rank) )
                    continue

                for sj in self.subjobs:
                    sj.event(self.evt)

            for sj in self.subjobs:
                sj.endRun()

        self.logger.info( "rank {:} finishing".format( self.rank ) )
        self.cputotal = time.time() - self.cpustart

        # do a pre endJob check to make sure all jobs have the same subjobs (unfinished)
        self.unify_ranks()

        for sj in self.subjobs:
            sj.endJob()

        #logger_flush()
        for hdlr in self.logger.__dict__['handlers']: # this is a bad way to do this...
            hdlr.flush()
        return
