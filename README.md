# LCLS-psana-examples
A few examples scripts using psana interface.

Some of the scripts are written with basic psana, some are with Jason's psdata tool.

## Directories

### data_summary_tools

A tool kit to produce a fairly simple summary of a data set produced
at the LCLS CXI user facility.  It should also work with other hutches.
The tool can run on a single node, with [MPI](http://www.open-mpi.org),
or be submitted to a batch MPI pool.

Note: requires data_summary_tools (below).

### data_summary_tools_html

The HTML (bootstrap, jquery) framework used to produce the output
of the data_summary_tools library.

### ParseEdl

A EDL parser that will 'descend the tree' and return all
of the EDL objects and a list of all the PVs that are
referenced in the EDL files.  

### scripts

Assorted scripts.
