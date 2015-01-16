import pandas
import pylab
import pprint
import matplotlib

pylab.ion()


data = pandas.DataFrame.from_csv('some_data.csv')

print "data columns"
for d in data.columns:
    print d


time = [eval(t) for t in data.EventId__time]
time2 = [ t[0] + t[1]/1.e9 for t in time]
time3 = pandas.to_datetime(time2,unit='s')

data.ebeam__ebeamPhotonEnergy


#beam = pandas.Series( data.ebeam__ebeamPhotonEnergy.tolist(), time3 )
gas11 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )
gas12 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )
gas21 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )
gas22 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )
gas63 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )
gas64 = pandas.Series( data.gasdet__f_11_ENRC.tolist(), time3 )

gas11.plot()
gas12.plot()
gas21.plot()
gas22.plot()
gas63.plot()
gas64.plot()






#ts.plot()

