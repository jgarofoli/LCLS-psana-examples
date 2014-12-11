
class event_process:
    def __init__(self):
        self.data      = []
        self.finaldata = []
        self.mergeddata = []
        self._process_event = lambda oo, evt: True
        self._finish = lambda oo: True
        self.doreduce = False
        self.reduction_step = None
        self.reduction_args = None
        self.reduction_kwargs = None
        self.results = {}
        self.in_report = None

    def set_finish(self,fun):
        """
        the finish function should operate on self.mergeddata (after reduction)
        it can do any process.  data that is to be summarized with other
        data (e.g. dictionaries of final values) should be stored in self.finaldata
        """
        self._finish = fun

    def set_process_event(self,fun):
        """
        the process_event function operates on self and evt.
        It should extract the data from the event and do whatever operations necessary
        and store them in self.data
        """
        self._process_event = fun

    def set_reduction_step(self,name):
        self.reduction_step = name
        self.doreduce = True

    def set_reduction_args(self,*args):
        self.reduction_args = args

    def set_reduction_kwargs(self,**kwargs):
        self.reduction_kwargs = kwargs

    def finish(self):
        self._finish(self)
        return

    def process_event(self,parent,evt):
        self._process_event(self,parent,evt)
        return


# copied from psana/Module.h
# https://www.slac.stanford.edu/~gapon/TALKS/2013_Oct_LCLS_UserMeeting/Batch_Psana_Intro_v2.pdf pg 7
class event_process_v2(object):
    """
    An empty event process in the new style.
    See some working examples in event_process_lib.py
    They all inherit form this.
    """
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        return

    def set_parent(self,parent):
        self.parent = parent

    def beginJob(self):
        #print "rank {:}".format(self.parent.rank)
        return

    def beginRun(self):
        return

    def event(self, evt):
        return

    def endRun(self):
        return

    def endJob(self):
        return

#    def beginCalibCycle(self):
#        return
#    def endCalibCycle(self):
#        return


