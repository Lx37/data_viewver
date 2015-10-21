
from feature_computing import power_in_bands, spectral_flatness, permutation_entropy, decimate_and_recurrence
from scipy.stats import moment
from pyeeg import svd_entropy, dfa
from numpy import mean
from data_flow_by_subject import get_subject_HDFStore, micromed_to_pandas



def get_all_feature_store(all_patient_name, trc_filename):
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
        
        
    
def run_all_micromed_to_pandas():

    all_patient_name = ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11',
                        'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P21',
                        'S01']
    all_trc_filename= [["EEG_1031.TRC"], ["EEG_1034.TRC"], ["EEG_1037.TRC"], ["EEG_1042.TRC"], 
                      ["EEG_1044.TRC"], ["EEG_1049.TRC"], ["EEG_1052.TRC"], ["EEG_1054.TRC"],
                      ["EEG_1056.TRC", "EEG_1057.TRC"], ["EEG_1058.TRC", "EEG_1059.TRC"],
                      ["P13 EEG 1.TRC", "P13 EEG 2.TRC", "P13 EEG 3.TRC"], 
                      ["EEG_1065.TRC", "EEG_1066.TRC"], ["P15EEG.TRC"], ["P16EEG.TRC"],
                      ["P17 EEG 24h.TRC"], ["EEG_1087.TRC", "EEG_1089.TRC"],
                      ["EEG_1090.TRC", "EEG_1092.TRC"], ["EEG_1110.TRC", "EEG_1111.TRC"],
                      ["EEG_1094.TRC", "EEG_1095.TRC", "EEG_1096.TRC", "EEG_1098.TRC", "EEG_1099.TRC", "EEG_1100.TRC"]] 

    for ii, patient_name in enumerate(all_patient_name):
        print patient_name
        print all_trc_filename[ii]
        dirname = "./../data/" + patient_name +"/"
        output_dirname =  './../data_node/' + patient_name + '/'
        selected_chan =  ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2', 'veog+', 'heog+', 'emg+', 'ecg+']
        micromed_to_pandas(dirname, all_trc_filename[ii] , output_dirname, selected_chan)
        
   


if __name__ == '__main__':

    run_all_micromed_to_pandas()