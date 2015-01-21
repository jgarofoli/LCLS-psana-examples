import socket
import time
import argparse

try:
    import epics
    import psmon.plots
    import psmon.publish
    import numpy
except ImportError as e:
    print e
    raise ImportError("could not import, probably need to add and ana evn.  Try:"
            ". /reg/g/psdm/etc/ana_env.sh")

class plotter(object):
    """a striptool like object"""
    def __init__(self,port=None):
        self.channels = {}
        self.port = port
        if port:
            psmon.publish.init(port=port)
        else :
            psmon.publish.init()
        return

    def add_channel(self,pvname,custom=None,lookback=5*60.):
        self.channels[pvname] = {'x':[],'y':[],'tic':0,'custom':custom,'lookback':lookback,'plot':None}
        return

    def set_lookback(self,pvname,lookback):
        self.channels[pvname]['lookback'] = lookback
        return


    def start_all(self):
        for pvname in self.channels:
            epics.camonitor(pvname,callback=self.callback)

        print ". /reg/g/psdm/etc/ana_env.sh"
        print "psplot -s {:} -p {:} {:}".format(socket.gethostname(),self.port,' '.join([pv.replace(':','-') for pv in self.channels]))
        return

    def stop_all(self):
        for pvname in self.channels:
            epics.camonitor_clear(pvname)
        return


    def callback(self,**kwargs):
        pvname = kwargs.get('pvname',None)
        value  = kwargs.get('value' ,None)
        now    = time.time()

        if self.channels[pvname]['custom'] != None:
            newvalue = self.channels[pvname]['custom'](value)
        else:
            newvalue = value

        if newvalue:
            self.channels[pvname]['y'].append(newvalue)
            self.channels[pvname]['x'].append(now)
        else:
            if len(self.channels[pvname]['y']) == 0:
                return
            self.channels[pvname]['y'].append( self.channels[pvname]['y'][-1] )
            self.channels[pvname]['x'].append(now)

        self.channels[pvname]['tic']+=1

        # trim old values...
        keep = len(self.channels[pvname]['x']) - sum([ int( (now - x) < self.channels[pvname]['lookback'] ) for x in self.channels[pvname]['x'] ])
        del self.channels[pvname]['x'][:keep]
        del self.channels[pvname]['y'][:keep]

        tranformedx = [(tt-now) for tt in self.channels[pvname]['x']]

        self.channels[pvname]['plot'] = psmon.plots.XYPlot(
                "{:0.2f}".format(self.channels[pvname]['y'][-1]),
                pvname.replace(':','-'),
                numpy.array(tranformedx),
                numpy.array(self.channels[pvname]['y']),
                xlabel='time [sec]',
                ylabel='value')
        psmon.publish.send(pvname.replace(':','-'),self.channels[pvname]['plot'])
        return

if __name__ == "__main__":
    ps = argparse.ArgumentParser()

    ps.add_argument("PV",
            help="A epics PV to trend (may be many)")

    ps.add_argument("--filter-module","-M",dest="module",default=None,
            help="the name of a python module containing the filter function")

    ps.add_argument("--custom-filter","-F",dest="filter",default=None,
            help="the name of the custom filter to apply to the PV")

    ps.add_argument("--port","-p",type=int,default=12301,dest="port",
            help="port to publish figures on")

    ps.add_argument("--lookback","-l",type=int,default=300,dest="lookback",
            help="look back time")

    args = ps.parse_args()

    plt = plotter(port=args.port)

    if args.module:
        custmod = __import__(args.module)
    
    if args.filter:
        plt.add_channel(args.PV,custom=getattr(custmod,args.filter))
    else :
        plt.add_channel(args.PV)

    plt.set_lookback(args.PV,args.lookback)

    plt.start_all()
