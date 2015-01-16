import psdata
import jutils
import ROOT

dd = psdata.psdata(exp='cxic0114',run=37)

motor = lambda : dd.epics.CXI.DG2.MMS.n09.RBV
diode1 = lambda : dd.Dg2Ipimb.channel[0]
diode2 = lambda : dd.Dg2Ipimb.channel[1]
diode3 = lambda : dd.Dg2Ipimb.channel[2]
diode4 = lambda : dd.Dg2Ipimb.channel[3]


graph1 = ROOT.TGraph()
graph2 = ROOT.TGraph()
graph3 = ROOT.TGraph()
graph4 = ROOT.TGraph()



if False:
    for ii in range(1000):
        if ii%100 == 0:
            print "loading event", ii
        graph1.SetPoint(ii,motor(),diode1())
        graph2.SetPoint(ii,motor(),diode2())
        graph3.SetPoint(ii,motor(),diode3())
        graph4.SetPoint(ii,motor(),diode4())
        dd.next_event()

    can = ROOT.TCanvas()
    fr = can.DrawFrame(-65,0,20,5)
    graph1.Draw()
