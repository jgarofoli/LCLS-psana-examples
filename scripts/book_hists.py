import psdata
import ROOT
import sys


class book_histos:
    def __init__(self,dd):
        self.ds = dd # a psdata object
        self.histos = {}

    def add_var(self,name,var):
        self.histos[name] = {}
        self.histos[name]['var'] = var
        self.histos[name]['histo'] = ROOT.TH1F('h_'+name,name,100,0,5) # have to set the histogram range by hand
                                                                       # an advantage of the numpy way is that since you keep all
                                                                       # the values in an array, you can 'auto' range.
                                                                       # a disadvantage of that is memory usage.

    def next_event(self,n=1):
        for ii in xrange(n):
            if n > 1:
                sys.stdout.write('loading event {:03.0f}/{:03.0f}\r'.format(ii,n) )
                sys.stdout.flush()
            self.ds.next_event()
            for h in self.histos:
                self.histos[h]['histo'].Fill( self.histos[h]['var']() )
        print " "

    def draw_all_histos(self):
        for h in self.histos:
            self.histos[h]['canvas'] = ROOT.TCanvas()
            # the histograms can be styled to look less "rooty"
            self.histos[h]['histo'].Draw()

if __name__ == "__main__":
    data = psdata.psdata(exp='cxie7914',run=192)

    bh = book_histos(data)

    bh.add_var('f_11_ENRC',lambda : data.Gasdet.f_11_ENRC)
    bh.add_var('f_12_ENRC',lambda : data.Gasdet.f_12_ENRC)
    bh.add_var('f_21_ENRC',lambda : data.Gasdet.f_21_ENRC)
    bh.add_var('f_22_ENRC',lambda : data.Gasdet.f_22_ENRC)

    bh.next_event(n=1000)

    bh.draw_all_histos()

