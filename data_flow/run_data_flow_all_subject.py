
from feature_computing import power_in_bands, spectral_flatness, permutation_entropy, decimate_and_recurrence
from scipy.stats import moment
from pyeeg import svd_entropy, dfa
from numpy import mean
from data_flow_by_subject import get_subject_HDFStore




all_patient_name = ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10']
trc_filename= ["EEG_1031.TRC", "EEG_1034.TRC", "EEG_1037.TRC", "EEG_1042.TRC", 
                        "EEG_1044.TRC", "EEG_1049.TRC", "EEG_1052.TRC", "EEG_1054.TRC"] 

output_dirname = './'
    
feats_bands_params = {'delta<1' : {'f_in': 0 , 'f_out' : 1},
                                    'delta>1': {'f_in': 1, 'f_out' : 4},
                                    'theta' : {'f_in': 4 , 'f_out' : 8},
                                    'alpha':  {'f_in': 8 , 'f_out' : 15},
                                    'beta' : {'f_in': 15 , 'f_out' : 31}
                                    }

feats_params = {#'dfa' : {},
                            'variances' : {'moment' : 3},
                            'skewness': {'moment' : 3},
                            'kurtosis' : {'moment' : 4} ,
                            'means':{},
                            #~ 'permutation_entropy':{'dim': 3, 'skipping_parameter': 1},  #OK
                            'spectral_flatness':{}, 
                            #~ 'svd_entropy':{'dE':20, 'tau':1}
                        }
feats_params2 = { 'determinism': {'decimate_q':4,'metric':'supremum', 'normalize':False, 'threshold':0.2},  #TODO
                                'laminarity':{'decimate_q':4,'metric':'supremum', 'normalize':False, 'threshold':0.2} # func is decimate_and_recurrence
                            }

func = {#'dfa': dfa,
            'variances' : moment,
            'skewness': moment,
            'kurtosis' : moment,
            'means': mean,
            'permutation_entropy': permutation_entropy,
            'spectral_flatness': spectral_flatness, 
            'svd_entropy': svd_entropy
            } #eventuelement ajouter band ?
                        
general_config = {'win_feat_size':'30s', #Sec
                            'win_feat_overlap':2,
                            'eeg_chan': ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2'],
                            'Chan_differential' : [['F3','C3'],['C3','P3'],['P3','O1'],['Fz','Cz'],['Cz','Pz'],['F4','C4'],['C4','P4'],['P4','O2'],['T3','C3'],['C3','Cz'],['C4','Cz'],   # Means first - segond; Ex : F3-C3
                                                                ['C4','T4'],['veog+','veog-'],['heog+','heog-'],['ecg+','ecg-'],['emg+','emg-'],['abdo+','abdo-']],
                            'filter':{'f_in':1, 'f_out': 30} #Hz
                            }


for ii in range(len(all_patient_name)):
    dirname = "./../data/" + all_patient_name[ii] +"/"
    get_subject_HDFStore(dirname, all_patient_name[ii], trc_filename[ii], feats_bands_params, feats_params, feats_params2, func, general_config, output_dirname)
    
    
    







