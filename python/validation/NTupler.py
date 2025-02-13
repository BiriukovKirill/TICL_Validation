# This file is dedicated to specify all the required classes
# and function for TICL validation NTuples production
import numpy as np
import json
import os
from typing import List

class NTupler:
    # Later bins would have to be in either int (representing number of bins),
    # List[float] (representing bin edges), Dict[str, int] (representing 
    # number of bins for each key in data or combined data) or Dict[str, List[int]]
    # (representing bin edges for each key in data or combined data)
    #
    # !!! It would be better to extract these data from config file !!!
    def __init__(self, data, combination_data, data_bins = 10, c_data_bins = 10, output = "output.json"):
        self.data = data
        self.combination_data = combination_data
        self.data_bins = data_bins
        self.c_data_bins = c_data_bins
        self.output = output

    # data and combination_data are dictionaries of arrays
    def makeHist(self):

        for key, d in self.data.items():
            new_key, flag = NTupler._trim(key)
            if flag:
                mapping_data = d
                d = self.data[new_key][mapping_data]
                self._makeCombinedHisto(new_key, d)
                self._makeHistoInBins(new_key, d, key, mapping_data)
            else:
                self._makeCombinedHisto(key, d)
                self._makeHistoInBins(key, d)
        

    @staticmethod
    def _trim(key):
        base_keys = {'LC_reco', 'LC_sim', 'Tracksters_reco', 'Tracksters_sim'}
        
        if key in base_keys:
            return key, False
        else:
            key_list = key.split('_')[:2]
            return f'{key_list[0]}_{key_list[1]}', True

    def _extractBins(self, key, comb_key):
        # depending on the type of self.data_bins and self.c_data_bins returns
        # bins for required data key and comb_key (as np.array or int)
        if comb_key is None:
            if type(self.data_bins) == int:
                return self.data_bins
            else:
                return self.data_bins[key]
        elif type(self.data_bins) == int and type(self.c_data_bins) == int:
            return self.data_bins, self.c_data_bins
        elif type(self.data_bins) == int:
            return self.data_bins, self.c_data_bins[f'{comb_key}']
        elif type(self.c_data_bins) == int:
            return self.data_bins[key], self.c_data_bins
        else:
            return self.data_bins[key], self.c_data_bins[f'{comb_key}']

    def _fillHist(self, data, c_data, data_bins, c_data_bins):
        # Dimension of NTuple depends on type of c_data
        # c_data = None condition to plot combined plot
        if c_data is None:
            return self.histo1D(data, data_bins)
        elif type(c_data[0]) == np.bool:
            data = data[c_data]
            return self.histo1D(data, data_bins)
        else:
            return self.histo2D(data, c_data, data_bins, c_data_bins)

    def histo1D(self, data, data_bins):

        H, d_bins = np.histogram(data, bins=data_bins)
        histogram = {
            "data": H.tolist(),
            "data_bin_edges": d_bins.tolist()
        }

        return histogram

    def histo2D(self, data, c_data, data_bins, c_data_bins):

        H, c_bins, d_bins = np.histogram2d(c_data, data, bins=(c_data_bins, data_bins))
        histogram = {
            "data": H.tolist(),
            "data_bin_edges": d_bins.tolist(),
            "c_data_bin_edges": c_bins.tolist()
        }

        return histogram

    def saveHisto(self, histo_key, histo):

        json_data = self._loadJSON()
        json_data[histo_key] = histo

        with open(self.output, 'w') as file:
            json.dump(json_data, file, indent=4)

    def _loadJSON(self):

        if os.path.exists(self.output):
            with open(self.output, 'r') as file:
                json_data = json.load(file)
        else: 
            json_data = {}

        return json_data

    def _makeHistoInBins(self, data_key, data, key_to_save=None, mapping_data=None):

        combination_keys = ['E', 'ET', 'eta', 'HD', 'LD']
        if mapping_data is not None:
            for comb_key in combination_keys:
                c_data = self.combination_data[f'{data_key}_{comb_key}'][mapping_data]
                data_bins, c_data_bins = self._extractBins(data_key, comb_key)
                histo = self._fillHist(data, c_data, data_bins, c_data_bins)
                self.saveHisto(f'{key_to_save}_{comb_key}', histo)
        else:
            for comb_key in combination_keys:
                c_data = self.combination_data[f'{data_key}_{comb_key}']
                data_bins, c_data_bins = self._extractBins(data_key, comb_key)
                histo = self._fillHist(data, c_data, data_bins, c_data_bins)
                self.saveHisto(f'{data_key}_{comb_key}', histo)

    def _makeCombinedHisto(self, data_key, data):
        
        data_bins = self._extractBins(data_key, comb_key=None)
        histo = self._fillHist(data, c_data=None, data_bins=data_bins, c_data_bins=None)
        self.saveHisto(data_key, histo)

