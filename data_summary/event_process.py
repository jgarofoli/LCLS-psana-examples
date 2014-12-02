
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

