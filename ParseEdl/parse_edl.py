import os
import EDL

filename = os.environ.get('PYTHONSTARTUP')
if filename and os.path.isfile(filename):
    with open(filename) as fobj:
        startupfile = fobj.read()
    exec(startupfile)


if __name__ == "__main__":
    mybase = '/reg/g/pcds/package/epics/3.14-dev/screens/edm/cxi/current'
    myfile = 'HXRAYFrame.edl'

    hxray = EDL.EDL(mybase,myfile)
    
    DS2_CSpad  = EDL.EDL( mybase, hxray.subscreens['0_DS2-CSpad']['filename']   , symbols=hxray.subscreens['0_DS2-CSpad']['symbols']  )
    Cryo0      = EDL.EDL( mybase, hxray.subscreens['0_CRYO'     ]['filename']   , symbols=hxray.subscreens['0_CRYO'     ]['symbols']  ) #, verbose=True )
    DG2_MMS2   = EDL.EDL( mybase, hxray.subscreens['0_DG2MMS'   ]['filename']   , symbols=hxray.subscreens['0_DG2MMS'   ]['symbols']  ) #, verbose=False  )

    #import pprint
    #pprint.pprint(DG2_MMS2.obj_dict)
    #xx = DG2_MMS2.get_all_pvs()
