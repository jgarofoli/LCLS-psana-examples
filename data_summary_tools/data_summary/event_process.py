import logging


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
        self.logger = logging.getLogger(__name__+'.default_logger')
        return

    def set_parent(self,parent):
        self.parent = parent
        #if 'r{:}'.format(self.parent.rank) not in self.logger.name:
            #self.logger.name = '{:}.r{:}'.format(self.logger.name,self.parent.rank)
        

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

    def replicate_info(self):
        return None

    def describe_self(self):
        # return a pickleable object (dictionary)
        # that can be used to reproduce this instance (minus the data)
        return (str(self.__class__).split('.')[-1].replace("'>",""), self.replicate_info() )

#    def beginStep(self):
#        return
#    def endStep(self):
#        return


