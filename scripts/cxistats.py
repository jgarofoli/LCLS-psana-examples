import psdata_20141002 as psdata
#import psdata
import pyfiglet
import time
import psana
import pylab 
import numpy

pylab.ion()

def dobanner(ds,width=None):
    fig = pyfiglet.Figlet(font='smslant')
    exp = ds.exp

    line1 =  fig.renderText('  {} {} {} Stats'.format(*exp.upper())).rstrip()
    line2 =  fig.renderText('with PSDATA').rstrip()
    if width:
        pass
        for l in line1.split('\n'):
            print "{string:^{width}s}".format(width = width, string=l)
        for l in line2.split('\n'):
            print "{string:^{width}s}".format(width = width, string=l)
    else:
        print line1
        print line2
    print " "
    return 

class myprinter:
    def __init__(self, width):
        self.width = width
    
    def pr2(self,ls,rs):
        # improve this to accept more than strings
        halfwidth = self.width / 2
        if 2*halfwidth != self.width:
            halfwidthL = halfwidth + 1
            halfwidthR = halfwidth
        else:
            halfwidthL = halfwidth
            halfwidthR = halfwidth

        strL = "{string:.<{width}s}".format(width=halfwidthL,string=ls)
        strR = "{string:.>{width}s}".format(width=halfwidthR,string=rs)
        #print "{string:^{width}s}".format(width=self.width,string=s)
        print strL + strR

    def pr1(self,s):
        print "{string:-^{width}s}".format(width=self.width,string=s)



def getevents(ds):
    # returns the total number of events in the run
    # should check if idx files are present
    thisds = psana.DataSource(ds.data_source()+':idx')
    total_events = 0
    for run in thisds.runs():
        #print run.run()
        total_events += len(run.times())
    return total_events

def doreport(ds,width=50):
    #formatprint = lambda A,B: "{:s}{:.20s}".format(A,B)
    mypr = myprinter(width)
    print " "
    mypr.pr1("metadata report")
    print " "
    # would like to handle the widths better, more dynamically
    mypr.pr2("Instrument", ds.instrument)
    mypr.pr2("Experiment", ds.exp)
    mypr.pr2("Run", "{:0.0f}/{:0.0f}".format(ds.run, len(ds.runs)))
    mypr.pr2("Run Start",  time.ctime( ds.runs[-1]['begin_time_unix'] ) ) 
    mypr.pr2("Run End"  ,  time.ctime( ds.runs[-1]['end_time_unix'  ] ) )
    nevts = getevents(ds)
    mypr.pr2("Events in Run", repr(nevts) )
    #if nevts > 500:
        #N = 50
    #else:
        #N = nevts
    #data = ds.get_events(N,det_list=['ebeam','gasdet','EventId'],silent=True)
    #M   = data.ebeam__ebeamPhotonEnergy.mean()
    #Std = data.ebeam__ebeamPhotonEnergy.std()
    #mypr.pr2("Ebeam Energy ({:0.0f})".format(N), "{:0.1f}+-{:0.1f}".format( M, Std) )
    print " "
    mypr.pr1("end metadata report")
    print " "


def doplotimp(imp):
    y = [x.channels() for x in imp.samples]
    Y = numpy.array(y)
    x = range(len(y))
    pylab.ioff()
    pylab.step(x,Y[:,0])
    pylab.step(x,Y[:,1])
    pylab.step(x,Y[:,2])
    pylab.step(x,Y[:,3])
    pylab.axis('tight')
    pylab.title('CXI IMP device')
    pylab.ion()
    pylab.show()
    return


if __name__ == "__main__":
    ds = psdata.psdata(exp='cxid6014')#,run=403)
    w = dobanner(ds,width=80)
    doreport(ds,width=80)
#for i,evt in enumerate(ds.events):
    #print i, evt

    #doplotimp(ds.imp1)

    configStore = ds.ds.env().configStore()
    configStore_keys = configStore.keys()
    goodones = []
    for i, k in enumerate(configStore_keys):
        if k.type():
            thiscs = configStore.get( k.type() )
            goodones.append((k,thiscs))
            print i, k.src()

    evrs = [int( 'Evr' in repr(x[0].src()) ) for x in goodones]

    print "dumping evr codes"
    for i, k in enumerate(evrs):
        if k == 1:
            codes = goodones[i][1].eventcodes()
            for c in codes:
                print c.code(), c.desc()


   # some NOTES
   # to get an image
   # import matplotlib.pyplot as plt
   # plt.figure('some title')
   # plt.imshow( ds.CxiDg1_0_Tm6740_0.data16 )
   # plt.show()

   # show what directory is loaded in the metadata report
   # could use index file to get number of events (look in psana help) (idx files in the xtc/index directory)
   #  https://confluence.slac.stanford.edu/display/PSDM/psana+-+Python+Script+Analysis+Manual#psana-PythonScriptAnalysisManual-RandomAccesstoXTCFiles%28%22Indexing%22%29
   # mean value of ebeam during run(s)? for example of data summary
   # some simple plots of photon energy
   # maybe add some plotting hooks into the psdata class
   #  check if pylab is loaded? or load it implicitly?
   # 
   # use ds.get_events(100,det_list=['ebeam','gasdet','EventId']) for example to get some data

   # look under X = ds.ds.env()
   # Z = X.configStore()
   # see extra_code.py for example?

   # event code trigger is good to know too
   #
   # xpp has done some nice plotting vs time
   #
   # use pylab step(x,y) to plot lines in stepwise fashion

   # check pandas time handling abilities

   # also look at xx = imp1.samples[0]
   # yy = xx.channels()
   # whihc is the four channels of the imp device
   # this is kind of transposed fo what you you really want
   # similar acquiris

   # check out the differences between what I had and what Jason has done with his psdata package
   # ~koglin/src/ana/psdata.py ~/ana/psdata.py


