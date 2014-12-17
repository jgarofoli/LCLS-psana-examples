from mpi4py import MPI
import math
import numpy

class trend_bin(object):
    def __init__(self,begin_time,end_time):
        #print "*** new trend_bin ***"
        self.begin_time = begin_time
        self.end_time   = end_time
        self.n         = None
        self.sum1      = None
        self.sum2      = None
        self.std       = None
        self.minval    = None
        self.maxval    = None
        self.avg       = None

    def __contains__(self,time):
        if time >= self.begin_time and time < self.end_time:
            return True
        else :
            return False

    def add_entry(self,time,val):
        #print time, self.begin_time, self.end_time
        if time >= self.begin_time and time < self.end_time:
            self._add(time,val)
        else :
            raise Exception('you are adding something that is out of my range')

    def _add(self,time,val,weight=1.0):
        if self.n == None:
            self.n = weight
            self.sum1 = float(val)
            self.sum2 = float(val)**2.0
            self.avg  = float(val)
            self.std  = None
            self.minval = val
            self.maxval = val
        else : 
            self.n += weight
            self.sum1 += val
            self.sum2 += val**2.0
            self.avg   = (self.n - weight)/self.n * self.avg + weight/self.n * val
            #print self.n, self.sum1, self.sum2
            self.std   = math.sqrt( round(self.n*self.sum2 - self.sum1**2.0,9) ) / self.n
            if val < self.minval:
                self.minval = val
            if val > self.maxval:
                self.maxval = val
        return

    def __add__(self,other): # for trend_bina + trend_binb
        if self.begin_time != other.begin_time or self.end_time != other.end_time: # there could be other logic...
            raise Exception('times must match')
        newbin = trend_bin(self.begin_time,self.end_time)
        newbin._add(self.begin_time,self.avg,weight=self.n)
        newbin._add(self.begin_time,other.avg,weight=other.n)
        newbin.minval = min( [ self.minval, other.minval ] )
        newbin.maxval = max( [ self.maxval, other.maxval ] )
        newbin.std = math.sqrt( self.n/newbin.n * self.std**2 + other.n/newbin.n * other.std**2 )
        return newbin

class mytrend(object):
    def __init__(self,period_window):
        self.period_window=period_window # this should be in seconds
        self.trend_periods = []
        return

    def get_begin_end_times(self,time):
        begin_time = round(self.period_window * round( time / self.period_window, 9 ), 9) # all this rounding is to avoid floating point errors, there could be a more clever way
        end_time   = round(begin_time + self.period_window, 9)
        return begin_time, end_time

    def add_entry(self,time,val):
        if len(self.trend_periods) == 0:
            begin_time, end_time = self.get_begin_end_times(time)
            #print time, begin_time, end_time
            self.trend_periods.append( trend_bin( begin_time, end_time ) )
        if time in self.trend_periods[-1]:
            self.trend_periods[-1].add_entry(time,val)
        else :
            added = False
            for tp in self.trend_periods:
                if time in tp:
                    tp.add_entry(time,val)
                    added = True
                    break
            if not added:
                begin_time, end_time = self.get_begin_end_times(time)
                self.trend_periods.append( trend_bin( begin_time, end_time ) )
                self.trend_periods[-1].add_entry(time,val)
        return

    def dump(self):
        for tp in self.trend_periods:
            print "[{:0.3f},{:0.3f}) min: {:0.2f}, max: {:0.2f}, mean: {:0.2f}, std: {:0.2f}".format( tp.begin_time, tp.end_time, tp.minval, tp.maxval, tp.avg, tp.std)

    def __add__(self,other):
        return

    def merge(self):
        """ merge bins that have the same begin_time and end_time
        """
        return

    def sort(self):
        """ sort in place
        """
        return

    def getxs(self):
        return [ ii.begin_time for ii in self.trend_periods ]

    def getmeans(self):
        return [ ii.avg for ii in self.trend_periods ]
    def getmins(self):
        return [ ii.minval for ii in self.trend_periods ]
    def getmaxs(self):
        return [ ii.maxval for ii in self.trend_periods ]
    def getstds(self):
        return [ ii.std for ii in self.trend_periods ]

    def reduce(self,comm,reducer_rank):
        # the hard part?
        self.gathered = comm.gather( self.trend_periods, root=reducer_rank) 

        if comm.Get_rank() == reducer_rank:
            reduced_trend = mytrend(self.period_window)
            for gath in self.gathered:
                reduced_trend.trend_periods.extend(gath)
            
            reduced_trend.merge()
            reduced_trend.sort()
            return reduced_trend

class myhist(object):
    # to do: implement __add__(self,other)
    # also then implement a complete object transport for reduction of these, perhaps as a member function
    #      so that all parts are transported, not just the bin entries
    def __init__(self,nbins,mmin,mmax):
        self.minrange  = mmin
        self.maxrange  = mmax
        self.nbins     = nbins
        self.binwidth  = (mmax-mmin)/float(nbins)
        self.edges     = numpy.arange(mmin,mmax,self.binwidth)
        self.binentries= numpy.zeros_like(self.edges)
        self.entries   = 0
        self.overflow  = None
        self.underflow = None
        self.maxval = None
        self.minval = None
        return

    def __add__(self,other):
        return

    def set_edges_entries(self,edges,binentries):
        self.edges = edges
        self.binentries = binentries
        self.binwidth = abs(self.edges[1]-self.edges[0])
        self.maxrange = self.edges[-1] + self.binwidth
        self.minrange = self.edges[0]

    def fill(self,val):
        boollist = list(val >= self.edges)
        boollist.reverse()
        self.entries += 1

        if self.overflow is None:
            self.overflow = 0
        if self.underflow is None:
            self.underflow = 0

        if True in boollist:
            whichbin = self.nbins - boollist.index(True) - 1
            self.binentries[ whichbin ] += 1.
        elif val >= self.maxrange:
            self.overflow += 1
            whichbin = 'overflow'
        elif val < self.minrange:
            self.underflow += 1
            whichbin = 'underflow'
        if self.minval is None:
            self.minval = val
            self.maxval = val
        if val < self.minval:
            self.minval = val
        if val > self.maxval:
            self.maxval = val
        return

    def mean(self):
        """ calculate the mean of the histogram distribution
        """
        wgtavg = 0.
        for lowedge,binentries in zip(self.edges, self.binentries):
            wgtavg += binentries * (lowedge + self.binwidth / 2.)
        wgtavg /= sum(self.binentries)
        return wgtavg

    def rms(self):
        """ calculate the mean of the histogram distribution
        """
        mean = self.mean()
        summ = 0.
        total = 0.
        for lowedge,binentries in zip(self.edges,self.binentries):
            summ += binentries* ( (lowedge+self.binwidth/2.) -  mean )**2
            total += binentries
        std = math.sqrt( summ / total )
        return std

    def std(self):
        return self.rms()

    def reduce(self,comm,reducer_rank):
        reduced_entries = numpy.zeros_like( self.binentries )
        comm.Reduce(
                [self.binentries, MPI.DOUBLE], 
                [reduced_entries, MPI.DOUBLE],
                op=MPI.SUM,root=reducer_rank)
        allmins = comm.gather(self.minval, root=reducer_rank)
        allmaxs = comm.gather(self.maxval, root=reducer_rank)
        if comm.Get_rank() == reducer_rank:
            histofall = myhist(self.nbins,self.minrange,self.maxrange)
            histofall.set_edges_entries(self.edges,reduced_entries)
            histofall.minval = min(allmins)
            histofall.maxval = max(allmaxs)
            return histofall

    def mksteps(self):
        self.Xsteps, self.Ysteps = [], [0,]
        for x,y in zip(self.edges,  self.binentries):
            self.Xsteps.append(x)
            self.Xsteps.append(x)
            self.Ysteps.append(y)
            self.Ysteps.append(y)
        return self.Xsteps, self.Ysteps

if __name__ == "__main__":
    import jutils
    myh = myhist(11,-1,10)
    for x in range(10):
        myh.fill(x)



    mytbin_all = trend_bin(0,1)
    mytbin_first = trend_bin(0,1)
    mytbin_second = trend_bin(0,1)

    import random
    R = random.Random()
    for t in xrange(100):
        this_r = R.uniform(0,1)
        this_t = t/100.
        mytbin_all.add_entry(this_t,this_r)
        if t < 35 :
            mytbin_first.add_entry(this_t, this_r)
        else :
            mytbin_second.add_entry(this_t, this_r)

    mytbin_new = mytbin_first + mytbin_second

    print "all std: {:}".format( mytbin_all.std )
    print "new std: {:}".format( mytbin_new.std )


    thistrend = mytrend(0.2)
    for t in xrange(1000):
        this_t = t/100.
        thistrend.add_entry( this_t, R.uniform(0,1) )

    thistrend.dump()




