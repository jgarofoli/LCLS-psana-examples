from event_process import *
from mpi4py import MPI 

class AddEventProcessError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


def mk_counter():
    import numpy           # would like to remove this
    import psana           # and this
    ep1 = event_process()
    ep1.data       = numpy.array([0,])
    ep1.mergeddata = numpy.array([0,])
    ep1.set_reduction_step('Reduce')
    ep1.set_reduction_args([ep1.data, MPI.DOUBLE], [ep1.mergeddata, MPI.DOUBLE])
    ep1.set_reduction_kwargs(op=MPI.SUM,root=0)
    def ep1proc(ss,pp,evt):
        id = evt.get(psana.EventId)
        #print 'rank', pp.rank, 'analyzed event with fiducials', id.fiducials()
        ss.data[0] += 1
        return
    def ep1fin(ss):
        print "total events processed by all ranks", ss.mergeddata[0]
        return
    ep1.set_process_event(ep1proc)
    ep1.set_finish(ep1fin)
    return ep1

