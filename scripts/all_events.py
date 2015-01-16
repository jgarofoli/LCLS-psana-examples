#import jutils
import time
#import psdata
import ROOT

#data = psdata.psdata(epics_live=True)


def myanalysis():
    answer=None
    # operate on data
    answer = data.Gasdet.f_11_ENRC
    return answer


def getNevents(*args):
    if len(args) > 0:
        N = args[0]
        analysis = args[1]
    else:
        N = 120
        analysis = lambda : None
    start = time.time()
    times = []
    answers = []
    for x in xrange(N):
        times.append( data.EventId.time )
        answers.append(analysis())
        data.next_event()
    finish = time.time()
    print "total time: ", finish-start
    return start, finish, times, answers

def analyzetimes(times):
    t_last = None
    deltas = []
    for t in times:
        if t_last != None:
            deltas.append( t[0]+t[1]/1.e9 - t_last )
        t_last = t[0]+t[1]/1.e9
    return deltas


def mk_histogram(deltas):
    c = ROOT.TCanvas()
    h = ROOT.TH1F('hist','hist',100,0,1)
    for d in deltas:
        h.Fill(d)
    h.Draw()
    return c,h

#start, finish, times, answers = getNevents(240,myanalysis)
#deltas = analyzetimes(times)
#c,h = mk_histogram(deltas)

#print "data frequency is {:0.2f} Hz".format(1./h.GetMean())


c2 = ROOT.TCanvas()
h2 = ROOT.TH1F('gas','gas',501,0,5)
h2.Draw()
for ii in xrange(1200):
    h2.Fill(data.Gasdet.f_11_ENRC)
    data.next_event()
    if ii % 24 == 0:
        c2.Update()


c2.Update()
