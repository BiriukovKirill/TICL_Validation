import numpy as np
import awkward as ak

# This class processes given data. Methods starting from underscore are not
# supposed to run by user.
#
# For certain plots one could prefer to use layer ids instead of their explicit
# coordinates. There no such information in branches related to trackters 
# (trackstersCLUE3DHigh, simtrackstersSC and simtrackstersCP).
#
# zToIDMap() defines a map from z-coorinates to layer ids. It is an array of the
# following form: [max_coordinate_id=1, max_coordinate_id=2, ...]

class DataProcessor:
    def __init__(self):
        self.maxID = None
        self.zToID = None

    # data is a DataFile object   
    def zToIDMap(self, data):
        # Initialize self.maxID. It is done only while primary call the function
        # for a given object
        self._maxLayerID(data)

        # Initialize self.zToID if it isn't
        if self.zToID is None:
            cluster_z = ak.flatten(np.abs(data.openArray('ticlDumper/clusters;1',\
                                                         'position_z')))
            cluster_id = ak.flatten(data.openArray('ticlDumper/clusters;1',\
                                                   'cluster_layer_id'))
            
            layer_id_list = []
            for layer in range(1, self.maxID):
                max_for_layer = np.max(cluster_z[cluster_id == layer])
                layer_id_list.append(max_for_layer)

            self.zToID = np.array(layer_id_list)

        return self.zToID

    def _maxLayerID(self, data):
        if self.maxID is None:
            max_value = 0

            layer_id_array = ak.flatten(data.openArray('ticlDumper/clusters;1', \
                                                       'cluster_layer_id'))
            self.maxID = np.max(layer_id_array)
        
        return 0