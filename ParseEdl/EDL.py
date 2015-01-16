import os
import EDLParse

VERBOSE = False

# Author: Justin Garofoli
# Email : justing@SLAC.stanford.edu
# Date  : 2014 October 27

class EDL:
    """
    Pass in the absolute base directory path (basedir) and the filename to be parsed.
    If verbose is set to True, a lot of debugging information will print to screen.
    The symbols variable is used internally when automagically loading imported edl files.

    Example Usage:

        mybase = '/reg/g/pcds/package/epics/3.14-dev/screens/edm/cxi/current'
        myfile = 'HXRAYFrame.edl'
        hxray = EDL.EDL(mybase,myfile)

        hxray.obj_dict # all edl objects in file.
        hxray.pvs      # pvs in this file only

        all_pvs = hxray.get_all_pvs() # returns the pvs in imported all screens

    Parsing happens at init, so it's fully formed after defining.

    * this behavior is _only_ implemented for the CXI hutch.                                      *
    * note that currently the parsing will NOT proceed from the "head" edl screen and parse all *
    * the edl screens in the hutch.  It will proceed from a secondary screen.                   *
    """

    def __init__(self,basedir, filename,verbose=VERBOSE,symbols={}):
        """
        initializer
        """
        self.verbose = verbose
        self.basedir = basedir
        self.filename = filename
        self.symbols = symbols

        self.pvs = []
        self.all_pvs = []


        with open(os.path.join(self.basedir,self.filename)) as myfile :
            self.lines = myfile.readlines()
        self.parse()
        self.get_title()
        self.get_subscreens()
        self.get_pvs()


    def parse(self):
        """
        call the EDLParse.parser and store the returned dictionary in the self.obj_dict.
        """
        if self.verbose:
            print os.path.join(self.basedir, self.filename)
        self.obj_dict = EDLParse.parser(self.lines, verbose=self.verbose, symbols=self.symbols )

    def get_subscreens(self):
        """
        return the list of imported edl files in this edl file.
        """
        self.subscreens = {}
        self.obj_dict['subscreens'] = {}
        self.EDLs = {}
        if 'activePipClass' in self.obj_dict:
            for i, pip in enumerate(self.obj_dict['activePipClass']):
                for k in pip['displayFileName']:
                    self.subscreens[ repr(i) +'_' + pip['menuLabel'][k] ] = { 'filename': pip['displayFileName'][k], }
                    if k in pip['symbols']:
                        self.subscreens[ repr(i) + '_' + pip['menuLabel'][k] ]['symbols'] = EDLParse.symbols(pip['symbols'][k])
                    else :
                        self.subscreens[ repr(i) + '_' + pip['menuLabel'][k] ]['symbols'] = {}

        if self.filename != 'HXRAYFrame.edl':
            for sb in self.subscreens:
                self.EDLs[sb] = EDL( self.basedir, self.subscreens[sb]['filename'], symbols=self.subscreens[sb]['symbols'], verbose=self.verbose )
                self.obj_dict['subscreens'][sb] = self.EDLs[sb].obj_dict 

    def get_title(self):
        """
        return the title of this edl file, if present.  Returns None otherwise.
        """
        title = None
        for t in self.obj_dict:
            for u in self.obj_dict[t]:
                if 'title' in u:
                    title = u['title']
                    if self.verbose:
                        print self.filename, title
                    break
        
        self.title = str(title)

    def get_pvs(self, PVS=['visPv', 'controlPv'], verbose=VERBOSE):
        """
        return a list of the PVs for this edl file only (not any imported edl files).
        """                         
        if self.filename == 'HXRAYFrame.edl': # for cxi, something else for a different hutch
            #print "don't do that, yet"
            # this will spider through ALL of the channels in the CXI screens
            # potentially thousands of epics records will be returned
            return

        for t in self.obj_dict:
            for u in self.obj_dict[t]:
                if 'title' in u:
                    continue
                for k in u:
                    if k in PVS :
                        self.pvs.append( u[k] )


        if self.verbose or verbose:
            for pv in self.pvs:
                print self.title, pv

        return self.pvs

    def get_all_pvs(self):
        """
        return a list of all the PVs in the edl file and imported edls.
        """
        for sb in self.subscreens:
            __ = self.EDLs[sb].get_pvs() 
            self.all_pvs.extend( list(__) )
        return self.all_pvs

    def print_all_pvs(self, prefix='#'):
        """
        output all the process variables to the screen, prefixed by the name of the screen/subscreen tree.
        """
        for pv in self.pvs:
            print prefix+self.title+'#', pv
        for sedl in self.EDLs:
            self.EDLs[sedl].print_all_pvs(prefix=prefix+self.title+'#')

