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
                'reco': 'ticlDumper/trackstersTiclCandidate;1',
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
                'reco': 'ticlDumper/trackstersTiclCandidate;1',
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
        self._makeCombConfig()

    def _makeCombConfig(self):
        if self.config is None:
            self.config = {}
            for opt_key, opt_dict in self.rs_config.items():
                opt_dict.update(self.combination_config)
                self.config[opt_key] = opt_dict
        return 0

    def getCombData(self, data):
        if self.data is None:
            self._getCombData(data)

        return 0
    
    def _getCombData(self, data):

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

class PID(DataProcessor):
    #Checking PID scores of being an EM-object (sum e and gamma probabilities)
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
                'reco': 'ticlDumper/trackstersTiclCandidate;1',
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
        pdg_dict = {
            'electron': 0,
            'photon': 1
        }

        data_dict = {}
        for opt_key, opt_dict in self.config.items():
            if opt_key == 'LC':
                pass
            else:
                raw_data = data.openArray(opt_dict['reco'], 'id_probabilities')
                flattened_data = ak.flatten(raw_data)
                raw_true_pdg = data.openArray(opt_dict['sim'], 'id_probabilities')
                true_pdg = ak.flatten(raw_true_pdg)
                for pdg_key, pdg_order in pdg_dict.items():
                    mask = np.array(true_pdg[:, pdg_order]).astype(bool)
                    data_per_key = flattened_data[:, pdg_order]
                    data_key = f'{opt_key}_{pdg_key}'
                    data_dict[data_key] = data_per_key[mask]

        self.data = data_dict
        return 0

class Association(DataProcessor):
    #here I'm going to save only best values
    def __init__(self):
        self.associations = None
        self.config = {
            'LC': {
                'SC': 'tsCLUE3D_recoToSim_SC',
                'CP': 'tsCLUE3D_recoToSim_CP'
            },
            'Tracksters': {
                'CP': 'ticlCandidate_recoToSim_CP'
            } 
        }

    def getData(self, data):
        scores = ['', '_score', '_sharedE']
        
        data_dict = {}

        for opt_key, opt_dict in self.config.items():
            for obj, branch_key in opt_dict.items():
                for score in scores:
                    Association._extractAssociation(data, data_dict, opt_key, obj,\
                                                    branch_key, score)
        
        self.data = data_dict
        return 0

    @staticmethod
    def _extractAssociation(data, data_dict, opt_key='', obj='', branch_key='',\
                            score=''):
        if score == '':
            raw_data = data.openArray('ticlDumper/associations;1', f'{branch_key}{score}')
            key = f'association_{opt_key}_{obj}{score}'
            data_dict[key] = raw_data[:,:, 0]
        else:
            raw_data = data.openArray('ticlDumper/associations;1', f'{branch_key}{score}')
            flattened_data = ak.flatten(raw_data)
            key = f'association_{opt_key}_{obj}{score}'
            data_dict[key] = flattened_data[:, 0]
        
        return 0

        
class PCAResolution(DataProcessor):
    # It needs data (class<DataFile>) and associations (class<Association>)
    def __init__(self):
        self.data = None
        self.meta = None

    def _extractNTracksters(self, data, option=''):
        # option = 'SC', 'CP'
        return data.openArray(f'ticlDumper/simtracksters{option};1', 'NTracksters')

    def _makeMeta(self, data):
        options = ['SC', 'CP']
        meta_dict = {}

        for option in options:
            meta_dict[option] = self._extractNTracksters(data, option)
        
        self.meta = meta_dict

        return 0

    def getData(self, data):
        if self.data is None:
            self._getData(self,data)

        return 0

    def _getData(self, data, associations):
        
        sc_association = associations.data['association_LC_SC']
        sim_data = []
        for label in ['x', 'y', 'z']:
            sim_data.append(data.openArray('ticlDumper/simtrackstersSC;1',\
                                            f'eVector0_{label}'))
        
        permuted_sim_data = []
        for s_data in sim_data:
            permuted_sim_data.append(ak.flatten(s_data[sc_association]))
        permuted_sim_data = np.transpose(permuted_sim_data)

        reco_data = []
        for label in ['x', 'y', 'z']:
            r_data = data.openArray('ticlDumper/trackstersCLUE3DHigh;1', f'eVector0_{label}')
            reco_data.append(ak.flatten(r_data))
        reco_data = np.transpose(reco_data)
        
        norm_sim = np.linalg.norm(sim_data, axis=1)
        norm_reco = np.linalg.norm(reco_data, axis=1)
        dot_prod = np.array([np.dot(s_data, r_data) for s_data, r_data in zip(sim_data, reco_data)])
        theta = np.acos(dot_prod/(norm_sim*norm_reco))

        self.data = {
            'LC_SC': theta
        }
    
        return 0
    
    
