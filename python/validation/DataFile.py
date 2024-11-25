import uproot as ur
import awkward as ak
import numpy as np

# This class allows to open desired data of ticl_dumper.root files.
# Methods starting from underscore are meant to be used ONLY inside other methods.
#
# Here the following convention is used:
#       Each DataFile object consists of different "Branches". They have
#       corresponding "branch_name"s.
#       Each branch has a set of "key"s.
#       CAUTION: Different branches may have different keys!
#
# Use getBranchKeys() if you want to know all the arrays inside a given branch.
# Use openArray() to open desired array (awkward).

class DataFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = ur.open(filepath)
        self.nevents = None
        self.branches = self.file.keys()
        self._nEvents()

    def getBranchKeys(self, branch_name=''):
        self._correctBranchName(branch_name)
        return self.file[branch_name].keys()
        
    def openArray(self, branch_name='', key=''):
        self._correctBranchName(branch_name)
        self._correctKey(branch_name, key)

        return self.file[branch_name][key].array()
    
    # Check if a given branch_name is available
    def _correctBranchName(self, branch_name=''):
        if branch_name not in self.branches:
            raise NameError(f'branch name = {branch_name} is unavailable in data'\
                            + f' file. \n Available branch names: \n {self.branches}')
        return 0
    
    # Check if a given key is available for a given branch_name
    def _correctKey(self, branch_name='', key=''):
        if key not in self.getBranchKeys(branch_name):
            keys = self.getBranchKeys(branch_name)
            raise KeyError(f'key = {key} is unavailable in branch {branch_name}.'\
                           + f'\n Available keys: \n {keys}')
        return 0
    
    # Compute number of events in DataFile. Called automatically during
    # initialization
    def _nEvents(self):
        if self.nevents is None:
            branch_name = self._isLeaf(self.branches)
            key = self._isLeaf(self.getBranchKeys(branch_name))
            n_events = len(self.openArray(branch_name, key))
            self.nevents = n_events

        return self.nevents
    
    # returns a leaf of a tree to compute number of events
    def _isLeaf(self, l=[]):
        for element in l:
            bool_map = [element.split(';')[0] in el for el in l]
            if sum(bool_map) == 1:
                break
        return element