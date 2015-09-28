# -*- coding: utf-8 -*-
"""
eeg super viewer main window 
"""

import sys
from PyQt4 import QtGui, QtCore

from vispy import app, visuals, scene, use
from vispy.scene import SceneCanvas
from vispy.scene.cameras import MagnifyCamera, Magnify1DCamera
from vispy.color import Colormap
from extra_classes import FeatureLineVisual, FeatureXAxis


import pandas as pd
from os.path import isfile, join
import numpy as np
use('pyqt4') 

class MainWindow(QtGui.QWidget):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        
    def initUI(self, params = None):

        if params == None:
            self.params = {
                'subjects' : ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17'], 
                'channels' : ['Cz', 'Pz', 'Fz'],
                'features' : [ 'theta', 'alpha', 'beta', 'means',  'kurtosis', 'skewness',  'svd_entropy'],
                #'features' : ['alpha', 'means', 'entropy',  'kurtosis'],
                'envir' : ['luxmetre','sonometre'], 
                'data_repo' : './data/',
                'fe' : 256, #Hz
                'win_size' : 30, #s
                'win_overlap' : 1./2 
            }
        self.selected = {
                'subject' : 'P06',
                'channels' : [2,2,2],
                'features' : [2,2,2,2,2,2, 2],
                'feat_chan': 'Cz',
                'envir' : [2,2]
        }
        
        self.cm = Colormap(['r', 'g', 'b'])

        self.setWindowTitle('eeg Super Viewer')
        self.resize(1200, 1000)
        #~ self.setStyleSheet("QWidget { background-color: rgb(50,50,50) }")
        
        self.mainlayout = QtGui.QHBoxLayout()
        self.setLayout(self.mainlayout)
        
        # Parameters layout
        self.vb_param = QtGui.QVBoxLayout(self)
        self.mainlayout.addLayout(self.vb_param)
        self.vb_param1 = QtGui.QVBoxLayout(self)
        self.vb_param.addLayout(self.vb_param1)
        self.vb_param2 = QtGui.QVBoxLayout(self)
        self.vb_param.addLayout(self.vb_param2)
        self.vb_param3 = QtGui.QVBoxLayout(self)
        self.vb_param.addLayout(self.vb_param3)
        
        #~ palette = QtGui.QPalette()
        #~ palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.white)
        #~ palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        #~ palette.setColor(QtGui.QPalette.BrightText,QtCore.Qt.white)
        
        ## Select subject
        vb_txt_subject = QtGui.QLabel('Select a subject :')
        #~ vb_txt_subject.setPalette(palette)
        self.vb_param1.addWidget(vb_txt_subject)
        subject_combo = QtGui.QComboBox()
        #~ subject_combo.setPalette(palette)
        self.vb_param1.addWidget(subject_combo)
        subject_combo.addItems(self.params['subjects'])
        self.connect(subject_combo, QtCore.SIGNAL('activated(QString)'), self.change_subject)
        
        ## Select sensors
        vb_txt_chan = QtGui.QLabel('Select eeg channels :')
        #~ vb_txt_chan.setPalette(palette)
        self.vb_param1.addWidget(vb_txt_chan)
        self.chan_cbs = []
        #~ for name in reversed(self.params['channels']): #same order than visual
        for name in self.params['channels']:
            chan_cb = QtGui.QCheckBox(name)
            #~ chan_cb.setPalette(palette)
            chan_cb.setCheckState(2)
            self.vb_param1.addWidget(chan_cb)
            self.chan_cbs.append(chan_cb)
            self.connect(self.chan_cbs[-1], QtCore.SIGNAL('stateChanged(int)'), self.change_channel)
        
        #~ vb_txt_empty = QtGui.QLabel(' ')
        #~ vb_txt_chan.setPalette(palette)
        #~ self.vb_param1.addWidget(vb_txt_empty , 1)
        
        ## Selecte channel for features data
        vb_txt_chanfeat = QtGui.QLabel('Select the feature channel :')
        #~ vb_txt_chanfeat.setPalette(palette)
        self.vb_param2.addWidget(vb_txt_chanfeat)
        chanFeat_combo = QtGui.QComboBox()
        #~ chanFeat_combo.setPalette(palette)
        self.vb_param2.addWidget(chanFeat_combo)
        chanFeat_combo.addItems(self.params['channels'])
        self.connect(chanFeat_combo, QtCore.SIGNAL('activated(QString)'), self.change_feat_channel)
        
        ## Select features
        vb_txt_feat = QtGui.QLabel('Select Features :')
        #~ vb_txt_feat.setPalette(palette)
        self.vb_param2.addWidget(vb_txt_feat)
        self.feat_cbs = []
        #~ i=0
        for name in self.params['features']:
            feat_cb = QtGui.QCheckBox(name)
            #~ feat_cb.setPalette(palette)
            feat_cb.setCheckState(2)
            self.vb_param2.addWidget(feat_cb)
            self.feat_cbs.append(feat_cb)
            self.connect(self.feat_cbs[-1], QtCore.SIGNAL('stateChanged(int)'), self.change_feature)
        
        #~ self.vb_param2.addWidget(vb_txt_empty , 1)
        
        #~ text = scene.Text(color, bold=True, font_size=24, color='w',
                  #~ pos=(200, 40), parent=canvas.central_widget)
        
        ## Select physio
        vb_txt_envir = QtGui.QLabel('Select environment data :')
        #~ vb_txt_envir.setPalette(palette)
        self.vb_param3.addWidget(vb_txt_envir)
        self.env_cbs = []
        for name in self.params['envir']:
            env_cb = QtGui.QCheckBox(name)
            #~ envir_cb.setPalette(palette)
            env_cb.setCheckState(2)
            self.vb_param3.addWidget(env_cb)
            self.env_cbs.append(env_cb)
            self.connect(self.env_cbs[-1], QtCore.SIGNAL('stateChanged(int)'), self.change_envData)
        
        # Vispy view layout
        self.vb_view = QtGui.QVBoxLayout(self)
        self.mainlayout.addLayout(self.vb_view)
        
        canvas_size = (1000, 1000)
        self.canvas = SceneCanvas(title='eeg Super Viewer', size=canvas_size, keys='interactive', show=True, parent = self)#, parent =  self.mainlayout)
        self.grid = self.canvas.central_widget.add_grid()
        self.eeg_view = self.grid.add_view(row=0, col=0,  col_span=2)# bgcolor= (0, 0, 0, 0.5), border_color=(0, 0, 0))
        self.feat_view = self.grid.add_view(row=1, col=0,  col_span=2)#, margin=10, bgcolor=(0, 0, 0, 0.5), border_color=(0, 0, 0))
        self.env_view = self.grid.add_view(row=2, col=0,  col_span=2)
        
        self.vb_view.addWidget(self.canvas.native)
        self.eeg_lines = []
        self.feat_lines = []
        self.feat_df = {}
        self.env_lines = []
        
        self.loadSubjectdata()
        self.init_plots()
        
        self.show()     


    def read_header(self, header_filename):
        d = { }
        for line in open(header_filename):
            k,v = line.replace('\n', '').replace('\r', '').split(':')
            d[k] = v
        if 'frequence' in d:
            d['frequence'] = float(d['frequence'])
        if 'dtype' in d:
            d['dtype'] = np.dtype(d['dtype'])
        if 'nbvoies' in d:
            d['nbvoies'] = int(d['nbvoies'])
            channelnames = [ ]
            for i in range(d['nbvoies']):
                channelnames.append(d['nom'+str(i+1)])
            d['channelnames'] = channelnames

        return d

    def loadSubjectdata(self):
        
        ##load eeg data
        print "subject file : ", join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.h5')
        eeg_Store = pd.HDFStore(join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.h5')) 
        self.eeg_df = eeg_Store.df
        self.nbEEGsample = np.shape(self.eeg_df['Cz'])[0]
        print "size EEG : ", self.nbEEGsample
        
        ##load features data
        for feat in self.params['features']:
            print "file : ", join(self.params['data_repo'], feat + '.h5')
            feat_Store = pd.HDFStore(join(self.params['data_repo'], feat + '.h5'))  # read_hdf ?? 
            self.feat_df[feat] = feat_Store.df.dropna()
           
        ##load environment data
        env_raw = join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.raw')
        env_raw_header = join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.header')
        d = self.read_header(env_raw_header)
        self.env_sigs = np.fromfile(env_raw, dtype = d['dtype'],).reshape(-1, d['nbvoies'])
        
        print "size env sigs : ", np.shape(self.env_sigs) 



    def init_plots(self):
        
        ## EEG params
        win =self.params['win_size']
        fe = self.params['fe']
        nb_chan = len(self.params['channels'])
        
        eeg_pos = np.empty((win*fe, 2))
        eeg_pos[:, 0] = range(win*fe)
        base_offset = 50
        chan_offset = 300
        gain = 1#0.1
        
        self.EEG_Xpos = np.round(win*fe/2)+1
        x0 = self.EEG_Xpos - win*fe/2
        x1 = self.EEG_Xpos + win*fe/2
        
        ## EEG Lines plots
        for i in range(nb_chan):
            eeg_pos = eeg_pos.copy()
            eeg_pos[:, 1] = self.eeg_df[self.params['channels'][i]][x0:x1].values * gain+(nb_chan - i)*chan_offset
            eeg_line = scene.visuals.Line(pos=eeg_pos, color='white', parent=self.eeg_view.scene)
            self.eeg_lines.append(eeg_line)
        
        ## EEG Axes
        x_lim = [0., win*fe]
        y_lim = [0, chan_offset*(nb_chan+1)]
        x_lim_scale = [0., win]
        y_lim_scale = [0., chan_offset*(nb_chan+1)]
        domains = np.array([x_lim, y_lim])
        pos_ax = [np.array([domains[0], [domains[1][0]] * 2]).T,np.array([[domains[0][0]] * 2, domains[1]]).T]
        self.eeg_x_axis = scene.Axis(pos_ax[0], x_lim_scale, (0, -1), parent=self.eeg_view.scene)
        self.eeg_y_axis = scene.Axis(pos_ax[1], y_lim_scale, (-1, 0), parent=self.eeg_view.scene)
        self.eeg_view.camera = 'panzoom'
   
        ## Feats params
        nb_feat = len(self.params['features'])
        nb_feat_values = len( self.feat_df[self.params['features'][0]])
        print 'nb_feat_values : ', nb_feat_values
        feat_pos = np.empty((nb_feat_values, 2))
        #~ feat_pos[:, 0] = np.linspace(-1.5, 1.5, nb_feat_values)
        feat_pos[:, 0] = range(nb_feat_values)
        feat_offset = 1
        self.featcolor = self.cm[np.linspace(0., 1., nb_feat)]
        
        ## Feat Axes
        truc = nb_feat_values*self.params['win_overlap']*self.params['win_size']/3600
        print 'nb_feat_values : ', nb_feat_values
        print 'self.params[win_overlap]', self.params['win_overlap']
        print  'self.params[win_size]', self.params['win_size']
        x_lim = [0.,nb_feat_values]
        y_lim = [0, feat_offset*(nb_feat+1)]
        x_lim_scale = [0., nb_feat_values]
        y_lim_scale = [0., feat_offset*(nb_feat+1)]
        domains = np.array([x_lim, y_lim])
        pos_ax = [np.array([domains[0], [domains[1][0]] * 2]).T,np.array([[domains[0][0]] * 2, domains[1]]).T]
        self.feat_x_axis = FeatureXAxis(pos_ax[0], x_lim_scale, (0, -1), parent=self.feat_view.scene) #set the position to .Xpos
        self.feat_y_axis = scene.Axis(pos_ax[1], y_lim_scale, (-1, 0), parent=self.feat_view.scene)
        
        self.feat_view.camera = 'panzoom'
        self.feat_view.camera._viewbox.events.mouse_press.connect(self.change_EEG_Xtime) #update EEG pos when clic on feat_view
        
        ## Feats Lines plots
        for j in range(nb_feat):
            feat_pos = feat_pos.copy()
            data = self.feat_df[self.params['features'][j]][self.selected['subject']][self.selected['feat_chan']].values.reshape((nb_feat_values))
            min_feat = min(data)
            max_feat = np.percentile(data, 90)#
            #~ max_feat = max(data)
            print  'feature %s min = %f, max = %f'%(self.params['features'][j], min_feat, max_feat )
            feat_pos[:, 1] = (data -  max_feat)/(max_feat - min_feat ) +  (nb_feat-j)*feat_offset
            #~ feat_pos[:, 1] = data
            feat_line = scene.visuals.Line(pos=feat_pos, color=self.featcolor[j], parent=self.feat_view.scene)
            self.feat_lines.append(feat_line)

        
        ## Environment params
        nb_env_sigs = np.shape(self.env_sigs)[1]
        nb_env_sigs_values = np.shape(self.env_sigs)[0]
        env_pos =  np.empty((nb_env_sigs_values, 2))
        env_pos[:, 0] = range(nb_env_sigs_values)
        self.envcolor = self.cm[np.linspace(0., 1., nb_env_sigs)]
        
        ## Environement Axes
        x_lim = [0.,nb_env_sigs_values]
        y_lim = [0, 1]
        x_lim_scale = [0., nb_env_sigs_values]
        y_lim_scale = [0.,1]
        domains = np.array([x_lim, y_lim])
        pos_ax = [np.array([domains[0], [domains[1][0]] * 2]).T,np.array([[domains[0][0]] * 2, domains[1]]).T]
        self.env_x_axis = scene.Axis(pos_ax[0], x_lim_scale, (0, -1), parent=self.env_view.scene)
        self.env_y_axis = scene.Axis(pos_ax[1], y_lim_scale, (-1, 0), parent=self.env_view.scene)
        
        self.env_view.camera = 'panzoom'
        
        ##Environment data
        for k in range(nb_env_sigs-1):
            env_pos = env_pos.copy()
            env_pos[:, 1] =  self.env_sigs[:,k]
            env_line = scene.visuals.Line(pos=env_pos, color=self.envcolor[k], parent=self.env_view.scene)
            self.env_lines.append(env_line)

    def change_EEG_Xtime(self, text):
        win =self.params['win_size']
        win_overlap =self.params['win_overlap']
        fe = self.params['fe']
        nb_feat_values = len( self.feat_df[self.params['features'][0]])
        print "nb_feat_values : ", nb_feat_values
        ## Convert from feature samples to EEG samples
        Xpos = np.int(self.feat_x_axis.Xpos)
        print "position received is : ", Xpos 
        if  Xpos > 0:
            if Xpos < nb_feat_values:
                self.EEG_Xpos = np.int(Xpos * win*fe* win_overlap) 
            else:
                self.EEG_Xpos =  self.nbEEGsample - win*fe/2
        else:
            self.EEG_Xpos = np.round(win*fe/2) +1
        print "new position is : ", self.EEG_Xpos 
        
        self.update_eeg_plots()


    def update_eeg_plots(self):
        win =self.params['win_size']
        fe = self.params['fe']
        nb_chan = len(self.params['channels'])
        eeg_pos = np.empty((win*fe, 2))
        eeg_pos[:, 0] = range(win*fe)
        chan_offset = 300
        gain = 1
        x0 = self.EEG_Xpos - win*fe/2
        x1 = self.EEG_Xpos + win*fe/2

          
        for i in range(nb_chan):
            if self.selected['channels'][i] == 2:
                eeg_pos = eeg_pos.copy()
                #~ print self.eeg_df[self.params['channels'][i]][x0:x1].values
                #~ print np.size(self.eeg_df[self.params['channels'][i]][x0:x1].values )
                eeg_pos[:, 1] = self.eeg_df[self.params['channels'][i]][x0:x1].values * gain+(nb_chan - i)*chan_offset
                self.eeg_lines[i].set_data(pos=eeg_pos)
                self.eeg_lines[i].parent = self.eeg_view.scene
            else:
                self.eeg_lines[i].parent = []
        

    def update_feat_plots(self):
        nb_feat = len(self.params['features'])
        nb_feat_values = len( self.feat_df[self.params['features'][0]])
        feat_pos = np.empty((nb_feat_values, 2))
        feat_pos[:, 0] = range(nb_feat_values)
        feat_offset = 1
        
        for j in range(nb_feat):
            if self.selected['features'][j] == 2:
                feat_pos = feat_pos.copy()
                data = self.feat_df[self.params['features'][j]][self.selected['subject']][self.selected['feat_chan']].values.reshape((nb_feat_values))
                min_feat = min(data)
                max_feat = np.percentile(data, 90)#max(data)
                feat_pos[:, 1] = (data -  max_feat)/(max_feat - min_feat ) +  (nb_feat-j)*feat_offset
                self.feat_lines[j].set_data(pos=feat_pos)
                self.feat_lines[j].parent =  self.feat_view.scene
            else:
                self.feat_lines[j].parent = []
        
        
    def update_env_plots(self):
        nb_env = len(self.params['envir'])
        nb_env_values = np.shape(self.env_sigs)[0]
        env_pos = np.empty((nb_env_values, 2))
        env_pos[:, 0] = range(nb_env_values)
        
        for k in range(nb_env):
            if self.selected['envir'][k] == 2:
                env_pos = env_pos.copy()
                env_pos[:, 1] = self.env_sigs[:,k]
                self.env_lines[k].set_data(pos=env_pos)
                self.env_lines[k].parent =  self.env_view.scene
            else:
                self.env_lines[k].parent = []
                
                
    def change_subject(self, text):
        self.selected['subject'] = str(text)
        print 'Patient selected : ',  self.selected['subject']
        self.loadSubjectdata()
        self.update_eeg_plots()
        
    
    def change_channel(self, text):
        for idx in range(len(self.chan_cbs)):
            state = self.chan_cbs[idx].checkState()
            self.selected['channels'][idx]  = state
        self.update_eeg_plots()
        
        
    def change_feat_channel(self, text):
        self.selected['feat_chan'] = str(text)
        print "Slected channel for feature plots is: ",  str(text)
        self.update_feat_plots()
        
    def change_feature(self, text):
        for idx in range(len(self.feat_cbs)):
            state = self.feat_cbs[idx].checkState()
            self.selected['features'][idx]  = state
        self.update_feat_plots()
        
        
    def change_envData(self, text):
        for idx in range(len(self.env_cbs)):
            state = self.env_cbs[idx].checkState()
            self.selected['envir'][idx]  = state
        self.update_env_plots()
        

    
def main():
    
    data_repo = './data/'
    
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main()    