# -*- coding: utf-8 -*-

import neo
import os
import pandas as pd
import quantities as pq

from tools import pq_to_timedelta, apply_on_sliding_window, split_df_of_tuples
from feature_computing import power_in_bands, spectral_flatness, permutation_entropy, decimate_and_recurrence
from scipy.stats import moment
from pyeeg import svd_entropy, dfa
from numpy import mean

"""
For one .TRC file, create a HDF Store with :
    - EEG raw data
    - each feature (alpha, beta, delta<1, delta>1, dfa, kurtosis, laminarity, means,
                            permutation_entropy, skewness, spectral_flatness, svd_entropy
                            theta, variances, 

"""

def get_subject_HDFStore(dirname, patient_name, trc_filename, feats_bands_params, feats_params, feats_params2, func, general_config, output_dirname):
    
    #TODO FOR ALL :test if exists and if different. If not :
    blocks = neo.MicromedIO(filename = os.path.join(dirname, trc_filename)).read()
    store = pd.HDFStore(output_dirname + 'store' + patient_name + '.h5')
    
    print blocks[0].segments[0].annotations['rec_datetime']
    
    ########## EEG raw data ##########
    nb_chan = len(blocks[0].segments[0].analogsignals)
    chan_names = [blocks[0].segments[0].analogsignals[i].name for i in range(nb_chan)]
    eeg_signals = {chan_name:blocks[0].segments[0].analogsignals[chan_index] 
                                    for chan_index,chan_name in enumerate(chan_names) if chan_name in general_config['eeg_chan']}
    ## pandaz time delta associated to data
    example_signal = eeg_signals['Cz'] 
    ns_tstart = pq_to_timedelta(example_signal.t_start,'ns')
    ns_freq = pq_to_timedelta(1/example_signal.sampling_rate,'ns')
    time_axis = pd.timedelta_range(start=pd.Timedelta(value = ns_tstart, unit = 'ns'), 
                                    periods=len(example_signal), 
                                    freq=pd.Timedelta(value = ns_freq, unit = 'ns')
                                    )
    datas = {chan_name:signal.magnitude for chan_name,signal in eeg_signals.items()}
    eeg_raw_df = pd.DataFrame(datas, index=time_axis)
    #~ df.to_hdf(os.path.join(output_dirname, patient_name+('.h5')),'df')
    store['eeg_raw_df'] = eeg_raw_df
    
    ########## General & feat info keep as series ##########
    general_config['rec_datetime'] =  blocks[0].segments[0].annotations['rec_datetime']
    general_config['sample_rate'] =  blocks[0].segments[0].analogsignals[0].sampling_rate.rescale('Hz')
    general_config['chan_names'] = chan_names 
    
    for k1 in  feats_bands_params.keys():
        store['config/feats_bands_params/{}'.format(k1)] = pd.Series(feats_bands_params[k1])
    for k1 in  feats_params.keys():
        store['config/feats_params/{}'.format(k1)] = pd.Series(feats_params[k1])
    for k1 in  feats_params2.keys():
        store['config/feats_params/{}'.format(k1)] = pd.Series(feats_params2[k1])
    store['config/general_config'] = pd.Series(general_config)
   
    ########## features ##########
    ## freq bands on raw data
    bands=[]
    for k in feats_bands_params.keys():
        bands.append((feats_bands_params[k]['f_in']*pq.Hz, feats_bands_params[k]['f_out']*pq.Hz))
    feat_bands_val = apply_on_sliding_window(eeg_raw_df, 
                                        func=power_in_bands,
                                        window_size=general_config['win_feat_size'],
                                        window_coverage=general_config['win_feat_overlap'],
                                        bands = bands,
                                        sampling_rate = general_config['sample_rate'])
    for i,df in enumerate(split_df_of_tuples(feat_bands_val.dropna())):
        store[feats_bands_params.keys()[i]] = df

    ## laminarity and determinism on raw data
    feat_val_rqa = apply_on_sliding_window(eeg_raw_df,
                                    func=decimate_and_recurrence,
                                    window_size=general_config['win_feat_size'], 
                                    window_coverage=general_config['win_feat_overlap'],
                                    **feats_params2['determinism'] #same for laminarity
                                    )
    for i,df in enumerate(split_df_of_tuples(feat_val_rqa.dropna())):
        store[feats_params2.keys()[i]] = df

    ## other feats on raw data
    for feat in feats_params.keys():
        print "feat calculated : ", feat
        print "feats_params[feat] : ", feats_params[feat]
        feat_val = apply_on_sliding_window(eeg_raw_df,
                                        func=func[feat],
                                        window_size=general_config['win_feat_size'], 
                                        window_coverage=general_config['win_feat_overlap'],
                                        **feats_params[feat]
                                        )
        store[feat] = feat_val
        
        
    
    ## freq bands on filtered data
    
    ## other feats on filtered data
    
    
    store.close()
    
#~ def dict2series(dict, serie):

def micromed_to_pandas(dirname, trc_filename, output_dirname, selected_chan):
    ## Create patient folder if doesn't exists
    patient_name = dirname.split('/')[-2]
    if not os.path.exists(output_dirname):
        os.makedirs(output_dirname)

    ## One export by file. no concatenation to keep recording exact time for viewer
    all_eeg_df = []
    ii = 0
    for trc_filename in trc_filename:
        blocks = neo.MicromedIO(filename = os.path.join(dirname, trc_filename)).read()
        ## EEG data
        nb_chan = len(blocks[0].segments[0].analogsignals)
        chan_names = [blocks[0].segments[0].analogsignals[i].name for i in range(nb_chan)]
        print chan_names
        eeg_signals = {chan_name:blocks[0].segments[0].analogsignals[chan_index] 
                        for chan_index,chan_name in enumerate(chan_names)
                        if chan_name in selected_chan}
        ## pandaz time delta associated to data
        example_signal = eeg_signals['Cz'] 
        rec_data_time = blocks[0].segments[0].annotations['rec_datetime']
        ns_freq = int(1./example_signal.sampling_rate.magnitude * pow(10,9))
        time_axis = pd.date_range(start=pd.to_datetime(rec_data_time), periods=len(example_signal), freq = str(ns_freq)+'N')
        datas = {chan_name:signal.magnitude for chan_name,signal in eeg_signals.items()}
        eeg_raw_df = pd.DataFrame(datas, index=time_axis)

        file_name = patient_name + '_' + str(ii)+ '_EEGBrut.h5'
        eeg_raw_df.to_hdf(os.path.join(output_dirname, file_name),'eeg_raw_df')
        print patient_name + " " + trc_filename + " micromed EEG data exported to pandaz in " + file_name
        all_eeg_df.append(eeg_raw_df)
        ii+=1

    ## Save concatenated data if multiple recordings
    if ii>1:
        file_name = patient_name + '_Concat_EEGBrut.h5'
        result = pd.concat(all_eeg_df)        
        result.to_hdf(os.path.join(output_dirname, file_name),'eeg_raw_df')
        print patient_name + " " + trc_filename + " micromed EEG data concatenated and exported to pandaz in " + file_name
   
    
if __name__ == '__main__':
    

    patient_name = 'PSain'
    dirname = "./../data/" + patient_name +"/"
    trc_filename= ["EEG_1094.TRC"]#, "EEG_1095.TRC", "EEG_1096.TRC", "EEG_1098.TRC", "EEG_1099.TRC", "EEG_1100.TRC"]
    output_dirname = './../data_node/' + patient_name + '/'
    selected_chan = ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2', 'veog+', 'heog+', 'emg+', 'ecg+']
    #['x4', 'x5', 'x6', 'x7', 'F3', 'Fz', 'F4', 'x8', 'T3', 'C3', 'Cz', 'C4', 'T4', 'x9', 'P3', 'Pz', 'P4', 'x10', 'O1', 'x11', 'O2', 'x1', 'x2', 'x3', 'veog+', 'heog+', 'emg+', 'ecg+',
    micromed_to_pandas(dirname, trc_filename , output_dirname, selected_chan)

    # patient_name = 'PSain'
    # #~ patient_name = 'P07'
    # dirname = "./../data/" + patient_name +"/"
    # trc_filename= "EEG_1094.TRC"
    # #~ trc_filename= "EEG_1044.TRC"
    # output_dirname = './'
    
    # feats_bands_params = {'delta<1' : {'f_in': 0 , 'f_out' : 1},
    #                                     'delta>1': {'f_in': 1, 'f_out' : 4},
    #                                     'theta' : {'f_in': 4 , 'f_out' : 8},
    #                                     'alpha':  {'f_in': 8 , 'f_out' : 15},
    #                                     'beta' : {'f_in': 15 , 'f_out' : 31}
    #                                     }
    
    # feats_params = {#'dfa' : {},
    #                             'variances' : {'moment' : 3},
    #                             'skewness': {'moment' : 3},
    #                             'kurtosis' : {'moment' : 4} ,
    #                             'means':{},
    #                             #~ 'permutation_entropy':{'dim': 3, 'skipping_parameter': 1},  #OK
    #                             'spectral_flatness':{}, 
    #                             #~ 'svd_entropy':{'dE':20, 'tau':1}
    #                         }
    # feats_params2 = { 'determinism': {'decimate_q':4,'metric':'supremum', 'normalize':False, 'threshold':0.2},  #TODO
    #                                 'laminarity':{'decimate_q':4,'metric':'supremum', 'normalize':False, 'threshold':0.2} # func is decimate_and_recurrence
    #                             }
    
    # func = {'dfa': dfa,
    #             'variances' : moment,
    #             'skewness': moment,
    #             'kurtosis' : moment,
    #             'means': mean,
    #             'permutation_entropy': permutation_entropy,
    #             'spectral_flatness': spectral_flatness, 
    #             'svd_entropy': svd_entropy
    #             } #eventuelement ajouter band ?
                            
    # general_config = {'win_feat_size':'30s', #Sec
    #                             'win_feat_overlap':2,
    #                             'eeg_chan': ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2'],
    #                             'Chan_differential' : [['F3','C3'],['C3','P3'],['P3','O1'],['Fz','Cz'],['Cz','Pz'],['F4','C4'],['C4','P4'],['P4','O2'],['T3','C3'],['C3','Cz'],['C4','Cz'],   # Means first - segond; Ex : F3-C3
    #                                                                 ['C4','T4'],['veog+','veog-'],['heog+','heog-'],['ecg+','ecg-'],['emg+','emg-'],['abdo+','abdo-']],
    #                             'filter':{'f_in':1, 'f_out': 30} #Hz
    #                             }
    
    # get_subject_HDFStore(dirname, patient_name, trc_filename, feats_bands_params, feats_params, feats_params2, func, general_config, output_dirname)
    
    
    