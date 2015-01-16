import epics
import psmon.plots
import psmon.publish
import numpy
import socket
import time


class plotter(object):
    """a striptool like object"""
    def __init__(self):
        self.channels = {}
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
        print "psplot -s {:} -p 12301 {:}".format(socket.gethostname(),' '.join([pv.replace(':','-') for pv in self.channels]))
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
                "{:0.2f} ml/h".format(self.channels[pvname]['y'][-1]),
                pvname.replace(':','-'),
                numpy.array(tranformedx),
                numpy.array(self.channels[pvname]['y']),
                xlabel='time [sec]',
                ylabel='flow [ml/h]')
        psmon.publish.send(pvname.replace(':','-'),self.channels[pvname]['plot'])
        return

if __name__ == "__main__":
    plt = plotter()
    
    def mycustom(val):
        if val > 4.999:
            return (val*12.-60.)
        else:
            return None

#    class filter(object):
#        def __init__(self):
#            self.last_value = None
#            self.limit = 5.
#
#        def do(self,val):
#            if val > 4.999:
#                newval = val*12.-60.
#            else:
#                return None
#            if self.last_value == None or newval - self.last_value < self.limit:
#                goodval = newval
#            else:
#                goodval = None
#            self.last_value = newval
#            return goodval

    #mycustom2 = filter()
    plt.add_channel('CXI:SC1:AIN:04',custom=mycustom)#,lookback=10.)
    #plt.set_lookback('CXI:SC1:AIN:04',5*60.)

    plt.start_all()
