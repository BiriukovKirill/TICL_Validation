import numpy as np

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
            
            # Access z-coordinate and id data of clusters.
            cluster_z = np.abs(data.openArray('ticlDumper/clusters;1', 'position_z'))
            cluster_id = data.openArray('ticlDumper/clusters;1', 'cluster_layer_id')

            # Set initial values to output
            layer_id_array = np.full(self.maxID, 9999)
            
            for event in range(data.nevents):
                
                # Initialize z-coordinate array per event
                event_cluster_z = cluster_z[event]
                for i, z in enumerate(event_cluster_z):
                    
                    layer_id = int(cluster_id[event][i]) - 1
                    
                    if layer_id_array[layer_id] > z:
                        layer_id_array[layer_id] = z
            self.zToID = layer_id_array
                    
        return self.zToID

    def _maxLayerID(self, data):
        if self.maxID is None:
            max_value = 0

            layer_id_array = data.openArray('ticlDumper/clusters;1', 'cluster_layer_id')
            for event in range(data.nevents):
                max_candidate = np.max(layer_id_array[event])
                if max_candidate > max_value:
                    max_value = max_candidate
            self.maxID = int(max_value)
        
        return 0