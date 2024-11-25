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
#
# Starting from 12/11/2024, DataProcessor class has subclasses for each type of
# plot, required to extract data.
#
# Multiplicity(DataProcessor) extracts multiplicity data.

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
    
class Multiplicity(DataProcessor):
    def __init__(self):
        self.data = None
        self.config = None
        self._makeConfig()

    def _makeConfig(self):
        if self.config is None:
            config_dict_LC = {
                'reco': 'ticlDumper/trackstersCLUE3DHigh;1',
                'sim': 'ticlDumper/simtrackstersSC;1'
            }
        
            config_dict_Tracksters = {
                'reco': 'ticlDumper/trackstersSuperclusteringDNN;1',
                'sim': 'ticlDumper/simtrackstersCP;1'
            }
    
            self.config = {
                'LC': config_dict_LC,
                'Tracksters': config_dict_Tracksters
            }
        return 0
    

    def getData(self, data):
        if self.data is None:
            self._getData(data)

        return 0
    
    def _getData(self, data):

        data_dict = {}
        for key, options in self.config.items():
            for option_key, option in options.items():
                data_dict[f'{key}_{option_key}'] = \
                    Multiplicity._transformData(data, option)
            
        self.data = data_dict
        return 0
    
    @staticmethod
    def _transformData(data, branch=''):
        raw_data = data.openArray(branch, 'vertices_x')
        flattened_data = ak.flatten(raw_data)
        data = np.array([len(trackster) for trackster in flattened_data])

        return data
        

    
class Combination(Multiplicity):
    def __init__(self):
        self.data = None
        self.config = None
        self.rs_config = {
            'LC': {
                'reco': 'ticlDumper/trackstersCLUE3DHigh;1',
                'sim': 'ticlDumper/simtrackstersSC;1'
            },
            'Tracksters': {
                'reco': 'ticlDumper/trackstersSuperclusteringDNN;1',
                'sim': 'ticlDumper/simtrackstersCP;1'
            }
        }

        self.combination_config = {
            'E': 'raw_energy',
            'ET': 'raw_pt',
            'eta': 'barycenter_eta',
            'HD' : 'barycenter_eta < 2.02',
            'LD' : 'barycenter_eta >= 2.02'
        }
        self._makeConfig()

    def _makeConfig(self):
        if self.config is None:
            self.config = {}
            for opt_key, opt_dict in self.rs_config.items():
                opt_dict.update(self.combination_config)
                self.config[opt_key] = opt_dict
        return 0

    def getData(self, data):
        if self.data is None:
            self._getData(data)

        return 0
    
    def _getData(self, data):

        data_dict = {}
        options = ['LC', 'Tracksters']
        rs_list = ['reco', 'sim']
        
        for option_key, option in self.config.items():
            for rs in rs_list:
                for comb_key in self.combination_config.keys():
                    if comb_key.split(' ')[-1] == '2.02':
                        pass
                    else:
                        data_dict[f'{option_key}_{rs}_{comb_key}'] = \
                            Combination._transformData(data, option[rs],\
                                                       option[comb_key])
        
        self.data = data_dict
        return 0
    
    @staticmethod
    def _transformData(data, branch, key):
        import operator
        operators = {
            '>=': operator.ge,
            '<': operator.lt
        }

        key_list = key.split(' ')
        if len(key_list) > 1:
            filter_data = ak.flatten(data.openArray(branch, key_list[0]))
            op = operators[key_list[1]]
            #mask needed
            mask = op(np.array(filter_data), float(key_list[2]))
            return mask
        else:
            raw_data = data.openArray(branch, key)
            flattened_data = ak.flatten(raw_data)

        return flattened_data