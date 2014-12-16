import logging

logger = logging.getLogger('data_summary.event_process')

# copied from psana/Module.h
# https://www.slac.stanford.edu/~gapon/TALKS/2013_Oct_LCLS_UserMeeting/Batch_Psana_Intro_v2.pdf pg 7
class event_process(object):
    """
    An empty event process in the new style.
    See some working examples in event_process_lib.py
    They all inherit form this.
    """
    def __init__(self):
        self.output = {}
        self.reducer_rank = 0
        self.logger = logging.getLogger('data_summary.event_process.default_logger')
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


