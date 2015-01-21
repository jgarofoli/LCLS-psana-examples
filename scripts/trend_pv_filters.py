# goes with trend_pv.py 

def mycustom(val):
    print val
    return val

def mycustom2(val):
    if val > 4.999:
        return (val*12.-60.)
    else:
        return None
