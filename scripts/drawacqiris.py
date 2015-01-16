import array
import ROOT
import time



#data.Acqiris.load_functions('acqiris')

#def drawacqiris(n):
#    mydata = data.Acqiris.data(n).waveforms()[0]
#    can = ROOT.TCanvas()
#    fr  = can.DrawFrame(0,-2000,5000,10000)
#    gr = ROOT.TGraph()
#    gr.DrawGraph(5000,array.array('i',range(5000)),array.array('i',mydata))
#    return can,fr,gr


#acq = drawacqiris(1)

class arraytrace:
    def __init__(self,ds,col,sty):
        self._datasource = ds
        self._color = col
        self._sty = sty
        return

acqtrace0 = arraytrace( lambda : data.Acqiris.data(0).waveforms()[0], 1, 1 )
acqtrace1 = arraytrace( lambda : data.Acqiris.data(1).waveforms()[0], 2, 1 )

class drawacqiris:
    def __init__(self):
        self._can = ROOT.TCanvas()
        self._n = 5000
        self._frame_lims = (0,-2000,self._n,10000)
        self._fr = self._can.DrawFrame(*self._frame_lims)
        self._x = array.array('i',range(self._n))
        self._traces = []

    def set_bkg_range(a,b):
        self._bkg_range = (a,b)

    def set_sig_range(a,b):
        self._sig_range = (a,b)

    def update_all(self,n=1,delay=0):
        self._can.cd()
        for tr in self._traces:
            for ii,val in enumerate(tr['trace']._datasource()):
                tr['graph'].SetPoint(ii,ii,val)
            #tr['graph'] = ROOT.TGraph(self._n, self._x, array.array('i', tr['trace']._datasource()) )
        #self._can.Update()
        time.sleep(delay)

    def add_trace(self,tr):
        self._traces.append({})
        self._traces[-1]['trace']=tr
        self._traces[-1]['graph']=ROOT.TGraph()
        self._traces[-1]['graph'].SetLineColor( tr._color )
        self._traces[-1]['graph'].SetLineStyle( tr._sty )

    def render(self):
        for tr in self._traces:
            tr['graph'].Draw('L')
        self._can.Update()

acq = drawacqiris()
acq.add_trace( acqtrace0 )
acq.add_trace( acqtrace1 )

acq.update_all()

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

doupdate(acq,n=100,delay=0.3333)
