import ROOT
import time
import os



device = 'DG2'

sum2 = lambda : sum( alldiodes() )


def alldiodes():
    if device == 'DG2':
        name = 'Dg2diode'
    elif device == 'DG1':
        name = 'Dg1diode'
    total = [\
    data._detectors[name].channel0Volts , \
    data._detectors[name].channel1Volts , \
    data._detectors[name].channel2Volts , \
    data._detectors[name].channel3Volts ]
    return total



can = ROOT.TCanvas()
ax = can.DrawFrame(0,0,2000,20)
ax.SetTitle(device+' diode sum vs time')
mr = ROOT.TMarker()
mr.SetMarkerStyle(20)

reftime = time.time()

def drawmarker():
    can.cd()
    x = time.time() - reftime
    y = sum2()      
    print x,y
    if x and y:
        mr.DrawMarker(x,y)

can2 = ROOT.TCanvas()
ax2 = can2.DrawFrame(-80,0,+80,20)
ax2.SetTitle(device+' diode vs target position')
mr2 = ROOT.TMarker()
mr2.SetMarkerStyle(20)

def drawmarker2():
    can2.cd()
    if device == 'DG2':
        x = data._epics_devices['CXI:DG2:MMS:09'].RBV
    elif device == 'DG1':
        x = data._epics_devices['CXI:DG1:MMS:08'].RBV
    y = sum2()
    print x,y
    if x and y:
        mr2.DrawMarker(x,y)
    return

next = lambda : data.next_event()
next()

can3 = ROOT.TCanvas()
hh = ROOT.TH1F('histo',device+' diode sum',200,0,20)
hh.Draw()

def fillhisto():
    x = sum2()
    if x:
        hh.Fill( x )
    can3.Update()
    return

cans = [can, can2, can3]
pid = os.getpid()
def saveallfigs(pid,cans):
    for i,c in enumerate(cans):
        c.Print('figs/can_{:}_{:}.pdf'.format(pid,i))

def updateall():
    next()
    print "vs time"
    drawmarker()
    print "vs motor"
    drawmarker2()
    fillhisto()
    return

def record(nevts=30,nsecs=1,savefigs=False):
    for jj in xrange(nevts):
        print jj,'of',nevts
        updateall()
        if savefigs:
            saveallfigs(pid,cans)
        time.sleep(nsecs)
    return

