# Scripts Readme

Some helpful information about the scripts in this directory.
It is not promised that all scripts will work.


### trend_pv.py and trend_pv_filters.py

Command line tool to trend a PV with a custom filter.

```
$> python -i trend_pv.py -M trend_pv_filters -F mycustom -p 12302 MEC:HXM:PIP:01:PMON
```

Possible extensions are the addition of other custom routines inside the callback function.  One use
that I can think of: fitting a trend line to predict when a volume will be pumped down.

### flow_meter*.py

See trend_pv* first.

Plots and publishes a flow meter channel, and filters out some
of the bad data points.

### all_events.py
### book_hists.py
### draw_acqiris_lowlevel.py
### draw_acqiris_lowlevel_tst.py
### draw_acqiris.py
### drawacqiris.py
### drawclass.py
### find_leadingedge.py
### gasdet.py
### ipimb.py
### mydatastore.py
### myplotter.py
### plotter.py
### simple_example.py
### targets.py


