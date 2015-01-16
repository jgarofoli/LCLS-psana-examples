import psmon.publish
import psmon.plots
import numpy
import socket
import epics
import time

class plotter(object):
    def __init__(self):
        self.data = {}
        self.update_time = 1.0
        self.max_points = 1000
        self.ref_time  = time.time()
        self.tic = 0
        psmon.publish.init()
        self.plots = {}

    def add_pv(self,pvname):
        self.data[pvname] = {'x':[],'y':[],'last-time':0.}
        print "\n. /reg/g/psdm/etc/ana_env.sh"
        print "psplot -s {:} -p 12301 {:}".format(socket.gethostname(),' '.join([pv.replace(':','-') for pv in self.data]))
        return

    def add_epics_data(self,**kwargs):
        pvname = kwargs.get('pvname',None)
        value  = kwargs.get('value',None)
        x      = kwargs.get('x',None)
        if not x:
            x = time.time() - self.ref_time
        if pvname not in self.data:
            self.add_pv(pvname)
        self.data[pvname]['x'].append(x)
        self.data[pvname]['y'].append(value)

        if x-self.data[pvname]['last-time'] > self.update_time:
            self.data[pvname]['last-time'] = x
            self.tic += 1

            if len(self.data[pvname]['x']) > self.max_points:
                self.data[pvname]['x'] = self.data[pvname]['x'][(-1*self.max_points):]
                self.data[pvname]['y'] = self.data[pvname]['y'][(-1*self.max_points):]

            self.plots[pvname] = psmon.plots.XYPlot(self.tic,pvname.replace(':','-'),numpy.array(self.data[pvname]['x']),numpy.array(self.data[pvname]['y']))
            psmon.publish.send(pvname.replace(':','-'),self.plots[pvname])
        return

    def add_psdata(self,source,value,x=None):
        if source not in self.data:
            self.add_pv(source)
        if not x:
            x = time.time() - self.ref_time
        self.data[source]['x'].append(x)
        self.data[source]['y'].append(value)

        if x-self.data[source]['last-time'] > self.update_time:
            self.data[source]['last-time'] = x
            self.tic += 1

            if len(self.data[source]['x']) > self.max_points:
                self.data[source]['x'] = self.data[source]['x'][(-1*self.max_points):]
                self.data[source]['y'] = self.data[source]['y'][(-1*self.max_points):]
            self.plots[pvname] = psmon.plots.XYPlot(self.tic,pvname.replace(':','-'),numpy.array(self.data[pvname]['x']),numpy.array(self.data[pvname]['y']))
            psmon.publish.send(pvname.replace(':','-'),self.plots[pvname])
        return


    def add_acqiris(self,source,value,x=None):
        if source not in self.data:
            self.add_pv(source)

        thistime = time.time() - self.ref_time
        self.data[source]['x'] = x
        self.data[source]['y'] = value

        if thistime-self.data[source]['last-time'] > self.update_time:
            self.data[source]['last-time'] = thistime
            self.tic += 1

            self.plots[source] = psmon.plots.XYPlot(self.tic,source,self.data[source]['x'],self.data[source]['y'])
            psmon.publish.send(source,self.plots[source])
        return



def demo_start():
    myp = plotter()
    epics.camonitor('GDET:FEE1:363:ENRC',callback=myp.add_epics_data)
    epics.camonitor('CXI:DS1:AIN:01:ai0:in0',callback=myp.add_epics_data)
    return

def demo_stop():
    epics.camonitor_clear('GDET:FEE1:363:ENRC')
    epics.camonitor_clear('CXI:DS1:AIN:01:ai0:in0')
    return


def draw_acqiris(data,acqtr=[0],evrs=[140,42]):
    myp = plotter()

    xvals = numpy.arange(10000)
    
    while True:
        for ac in acqtr:
            #data.evr0.eventCodes  # this loads the evrs?
            thisevr = data.evr0.eventCodes
            for ev in evrs:
                if ev in thisevr:
                    thisdata = data.Acqiris.data(ac).waveforms()[0]
                    myp.add_acqiris('acq{:}_evr{:}'.format(ac,ev), thisdata,x=xvals)
        data.next_event()

    return


def get_list_of_triggers(data,n=1000):
    evrs = []
    for x in range(n):
        data.evr0.eventCodes
        for ev in data.evr0.eventCodes:
            if ev not in evrs:
                evrs.append(ev)
    return evrs
