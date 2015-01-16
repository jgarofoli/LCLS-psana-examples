import epics
import time

def filter(**kwargs):
    value = kwargs.get('value',None)
    pvname = kwargs.get('pvname',None)
    if value > 4.9999:
        print "{:} {:} {:0.3f} V, {:6.3f} ml/h".format(pvname,time.asctime(), value, value*12.-60.)
        #print time.asctime(), value, value*12.-60.
    return

def start(chan='CXI:SC1:AIN:04'):
    epics.camonitor(chan,callback=filter)
    return


def stop(chan='CXI:SC1:AIN:04'):
    epics.camonitor_clear(chan)
    return

if __name__ == "__main__":
    start()
