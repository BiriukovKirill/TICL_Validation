# In this file, there is a class required to produce plots
# of given NTuples. For now, it only reads the .json files
#!!! in principle, it might be improoved if needed!!!
import json
import numpy as np
from typing import Union, List, Dict
import matplotlib.pyplot as plt
import matplotlib as mpl
import mplhep as hep

class Plotter:
    # setting up dpi=300 for all plots
    mpl.rcParams['figure.dpi'] = 300
    # setting up a cms style
    hep.style.use("CMS")

    def __init__(self, input: str, output: str):
        self.input = input
        self.output = output
        self.file = None
        self.prefix = None
        self.hist1D_x_labels = {
            'multiplicity': {
                                'LC': '# of LC in trackster',
                                'Tracksters': '# of tracksters in supercluster'
                            },
            'pid': {
                        'LC': 'Pr(EM trackster)',
                        'Tracksters': 'Pr(EM supercluster)'
                    },
            'response': {
                            'LC': 'trackster energy response',
                            'Tracksters': 'supercluster energy response'
                    },
            'efficiency': {
                            'LC': 'trackster to CP score',
                            'Tracksters': 'supercluster to CP score'
                    }
        }
        self.readJSON()
        self._setPrefix()

    def _setPrefix(self):
        if self.prefix is None:
            file_name = self.input.split('/')[-1]
            self.prefix = file_name.split('_')[0]

    def readJSON(self):
        if self.file is None:
            with open(self.input, 'r') as file:
                self.file = json.load(file)
    
    def makePlots(self):
        # This function makes all the plots from a given input file.
        # There may be 1D and 2D histograms. They are easily distinguished
        # by checking a data type of the first element of the list:
        #       1. type(data[0]) == list -> 2D histogram
        #       2. type(data[0]) == float -> 1D histogram

        for hist_name, hist in self.file.items():
            if type(hist['data'][0]) == int:
                self.hist1D(hist_name, hist)
            else:
                self.hist2D(hist_name, hist)
                self.unrolledHist(hist_name, hist)

    def hist1D(self, hist_name: str, hist: Dict[str, List[Union[List, int]]],\
                scale: str ='log', comb_bin_min: float = None,\
                comb_bin_max: float = None, comb_var: str = None, bin_num: int=None):
        # As data is already NTuplized, we use ax.bar() for 1D histograms.
        # We define scale parameter to be str(log) (default) or None.

        data, bar_centers, bar_widths = self._defineHist(hist, scale, bin_num)
        label = self._setLabel(comb_bin_min, comb_bin_max, comb_var)

        fig, ax = plt.subplots()
        ax.bar(bar_centers, data, width=bar_widths, label=label)
        hep.cms.label('Internal', loc=0, com=None)
        
        # when log-scale we change y_ticks
        if scale == 'log':
            y_ticks = ax.get_yticks()
            ax.set_yticklabels([f'$10^{{{i:.1f}}}$' for i in y_ticks])

        # setting up labels
        ax.set_ylabel('Counts')
        ax.set_xlabel(self.hist1D_x_labels[self.input.split('_')[0]][hist_name.split('_')[0]])
        
        #setting up legend
        ax.legend()
        
        #saving plot inside self.output directory
        if bin_num is None:
            plt.savefig(f'{self.output}/{self.prefix}_{hist_name}.svg')
        else:
            plt.savefig(f'{self.output}/{self.prefix}_{hist_name}_{bin_num}.svg')

    def hist2D(self, hist_name: str, hist: Dict[str,List[Union[List, int]]], scale: str='log'):
        data_edges, c_bin_edges = hist['data_bin_edges'], hist['c_data_bin_edges']
        if scale == 'log':
            data = np.log10(np.array(hist['data']) + 1)
        else:
            data = hist['data']

        fig, ax = plt.subplots()
        im = ax.imshow(data)
        hep.cms.label("Internal", loc=0, com=None)
        x_ticks, y_ticks = self._getHist2DTicks(hist_name, hist)
        ax.set_xticks(x_ticks[0], x_ticks[1])
        ax.set_yticks(y_ticks[0], y_ticks[1])
        cbar = fig.colorbar(im, ax=ax, fraction=0.2, pad=0.04)

        if scale == 'log':
            cbar.set_ticklabels([f'$10^{{{i}}}$' for i in cbar.get_ticks()])

        ax.set_ylabel(hist_name.split('_')[-1])
        ax.set_xlabel(self.hist1D_x_labels[self.prefix][hist_name.split('_')[0]])
        
        plt.savefig(f'{self.output}/{self.prefix}_{hist_name}.svg')

    def unrolledHist(self, hist_name: str, hist: Dict[str, List[Union[List, int]]], scale: str = 'log'):
        # This function unrolls a given 2D histogram
        n_unrolling_bins = len(hist['data'])
        for bin in range(n_unrolling_bins):
            comb_bin_min = np.round(hist['c_data_bin_edges'][bin], 2)
            comb_bin_max = np.round(hist['c_data_bin_edges'][bin + 1], 2)
            comb_var = hist_name.split('_')[-1]

            self.hist1D(hist_name, hist, scale, comb_bin_min, comb_bin_max, comb_var, bin)

    def _getHist2DTicks(self, hist_name: str, hist: Dict[str, List[float]]):
        x_tick_positions = np.linspace(-0.5, 9.5, 9)
        data_bin_ids = np.linspace(0, len(hist['data_bin_edges']), 9)
        x_tick_labels = [str(np.round(hist['data_bin_edges'][int(i - 1)],2)) for i in data_bin_ids]
        y_tick_positions = np.linspace(-0.5, len(hist['c_data_bin_edges']) - 0.5, len(hist['c_data_bin_edges']))
        y_tick_labels = [str(np.round(i)) for i in hist['c_data_bin_edges']]

        return [x_tick_positions, x_tick_labels], [y_tick_positions, y_tick_labels]


    def _defineHist(self, hist, scale: str = 'log', bin_num: int=None):
        # This is a helper function. It returns a set of the following
        # info about a hist: data, bar_centers, bar_widths

        bin_edges = np.array(hist['data_bin_edges'])
        bar_centers = (bin_edges[1:] + bin_edges[:-1]) / 2
        bar_widths = bin_edges[1:] - bin_edges[:-1]

        if scale == 'log' and bin_num is None:
            return np.log10(np.array(hist['data']) + 1), bar_centers, bar_widths
        elif scale == 'log' and bin_num is not None:
            return np.log10(np.array(hist['data'][bin_num]) + 1), bar_centers, bar_widths
        elif scale != 'log' and bin_num is None:
            return hist['data'], bar_centers, bar_widths
        else:
            return hist['data'][bin_num], bar_centers, bar_widths

    def _setLabel(self, comb_bin_min: float=None,\
                    comb_bin_max: float=None, comb_var: str=None):
        
        # hist_flag is '1D' of '2D'
        if comb_bin_min is None:
            return 'combined'
        elif comb_var == 'HD' or comb_var == 'LD':
            return comb_var
        elif comb_var == 'eta':
            return f'{comb_bin_min} < {comb_var} < {comb_bin_max}'
        else:
            return f'{comb_bin_min} < {comb_var} < {comb_bin_max} MeV'