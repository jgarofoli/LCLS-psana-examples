import time
import ROOT
import array

"""
"""

class diodes:
    def __init__(self):
        self._calib  = {}
        self._diodes = {}
        self._allvals = {}
        return

    def add_diode(self,n,diode):
        self._diodes[n] = diode
        self._calib[n] = {'m': 1., 'b': 0., 'calibrated': False,}
        return

    def get_diode(self,n):
        if self._calib[n]['calibrated']:
            self._allvals[n] =  self._calib[n]['m']*self._diodes[n]()+self._calib[n]['b']
        else:
            self._allvals[n] =  self._diodes[n]() 
        return float( self._allvals[n] )

    def update_alldiodes(self):
        for d in sorted(self._diodes):
            self._allvals[d] =  self.get_diode(d)
        return

    def get_alldiodes(self):
        self.update_alldiodes()
        return dict(self._allvals)

    def get_diode_sum(self):
        total = 0.
        for d in self._diodes:
            total += self._diodes[n]()
        return total

    def set_calibration(self,n,m,b):
        # y = m*x+b calib
        if n not in self._calib:
            self._calib[n]={}
        self._calib[n]['m'] = float(m)
        self._calib[n]['b'] = float(b)
        self._calib[n]['calibrated'] = True



device = 'DG2'
if device == 'DG2':
    name = 'Dg2diode'
elif device == 'DG1':
    name = 'Dg1diode'

dg2 = diodes()
dg2.add_diode(0, lambda: data._detectors[name].channel[0] ) 
dg2.add_diode(1, lambda: data._detectors[name].channel[1] ) 
dg2.add_diode(2, lambda: data._detectors[name].channel[2] ) 
dg2.add_diode(3, lambda: data._detectors[name].channel[3] ) 

dg2.set_calibration(0,+1.,+0.0)
dg2.set_calibration(1,+1.,+0.0)
dg2.set_calibration(2,+1.,+0.0)
dg2.set_calibration(3,+1.,+0.0)

class trace:
    def __init__(self,ds,col,sty):
        self._datasource = ds
        self._marker     = ROOT.TMarker()
        self._marker.SetMarkerColor(col)
        self._marker.SetMarkerStyle(sty)

class plotvstime:
    def __init__(self,**kwargs):
        title = kwargs.get('title','diode sum vs time')
        frame = kwargs.get('frame',(0,-5,2000,5))
        self._reftime = time.time()
        self._can = ROOT.TCanvas()
        self._ax = self._can.DrawFrame(*frame)
        self._ax.SetTitle(title)
        self._traces = []
        self._preupdate = None
        return

    def add_trace(self,trace):
        self._traces.append(trace)
        return

    def update_all(self,n=1,delay=0):
        self._can.cd()
        for jj in xrange(n):
            if self._preupdate:
                self._preupdate()
            self._current_time = time.time() - self._reftime
            for tr in self._traces:
                tr._marker.DrawMarker( self._current_time, tr._datasource() )
            time.sleep(delay)

    def set_pre_update(self,fun):
        self._preupdate = fun

    def render(self):
        if self._current_time - self._ax.GetXaxis().GetLast() < 10:
            self._ax.GetXaxis().SetRangeUser(self._ax.GetXaxis().GetFirst(), int(self._current_time+60))
        self._can.Update()

class plotvsx:
    def __init__(self,**kwargs):
        title = kwargs.get('title','diode sum vs x')
        frame = kwargs.get('frame',(0,-5,2000,5))
        self._can = ROOT.TCanvas()
        self._ax = self._can.DrawFrame(*frame)
        self._ax.SetTitle(title)
        self._traces = []
        self._preupdate = None

    def add_trace(self,trace):
        self._traces.append(trace)
        return

    def update_all(self,n=1,delay=0):
        self._can.cd()
        for jj in xrange(n):
            if self._preupdate:
                self._preupdate()
            self._current_x = self.get_x()
            for tr in self._traces:
                tr._marker.DrawMarker( self._current_x, tr._datasource() )
            time.sleep(delay)

    def set_x(self,x):
        self.get_x = x

    def set_pre_update(self,fun):
        self._preupdate = fun

    def render(self):
        self._can.Update()



def preup():
    dg2.update_alldiodes()
    #print dg2._allvals
    return

dg2_timeplot = plotvstime(title='ds2 diodes vs time',frame=(0,0,2000,3))
dg2_timeplot.set_pre_update(preup)

preup()

dg2_timeplot.add_trace( trace( lambda : dg2.get_diode(0), 1, 20 ) )
dg2_timeplot.add_trace( trace( lambda : dg2.get_diode(1), 2, 20 ) )
dg2_timeplot.add_trace( trace( lambda : dg2.get_diode(2), 3, 20 ) )
dg2_timeplot.add_trace( trace( lambda : dg2.get_diode(3), 4, 20 ) )

dg2_timeplot.update_all()

ipimb_y_timeplot = plotvstime(title='ds2 target position vs time',frame=(0,-60,2000,20))
ipimb_y_timeplot.add_trace( trace( lambda : data._epics_devices['CXI:DG2:MMS:09'].RBV, 1, 20 ) ) 


dg2_xplot = plotvsx(title='ds2 diodes vs position',frame=(-60,0,20,3))
dg2_xplot.set_pre_update(preup)

dg2_xplot.set_x( lambda : data._epics_devices['CXI:DG2:MMS:09'].RBV )

dg2_xplot.add_trace( trace( lambda : dg2.get_diode(0), 1, 20 ) )
dg2_xplot.add_trace( trace( lambda : dg2.get_diode(1), 2, 20 ) )
dg2_xplot.add_trace( trace( lambda : dg2.get_diode(2), 3, 20 ) )
dg2_xplot.add_trace( trace( lambda : dg2.get_diode(3), 4, 20 ) )

dg2_xplot.update_all()

beam_energy = plotvstime(title='beam',frame=(0,0,2000,4))
beam_energy.add_trace( trace( lambda : data.epics.SIOC.SYS0.ML00.AO569, 6, 20 ) )


def doupdate(*args,**kwargs):
    n=kwargs.get('n',1)
    delay=kwargs.get('delay',0.)
    for jj in xrange(n):
        print jj,'of',n
        data.next_event()
        for a in args:
            a.update_all()
        time.sleep(delay)
        if jj%20 == 0:
            for a in args:
                a.render()

#doupdate(dg2_timeplot,beam_energy,ipimb_y_timeplot,n=1200,delay=.3333)



