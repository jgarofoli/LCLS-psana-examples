import os,inspect

fname = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),'device_config.dict')
with open(fname,'r') as f:
    devices = eval(f.read())

del fname
