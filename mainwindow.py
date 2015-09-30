"""
Demonstrates some customized mouse interaction by drawing a crosshair that follows 
the mouse.


"""
import collections
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from os.path import isfile, join
import pandas as pd

from dialogWindow import DialogWindow


class MainWindow(QtGui.QWidget):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        
    def initUI(self, params = None):

        if params == None:
            self.params = {
                'subjects' : ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'eeg_plot0', 'eeg_plot1', 'eeg_plot2', 'eeg_plot3', 'eeg_plot4', 'eeg_plot5', 'eeg_plot6', 'eeg_plot7'], 
                'channels' : ['Cz', 'Pz', 'Fz'],
                'base_offset' : 0,
                'chan_offset' : 150,
                'gain' : 1,
                'features' : [ 'theta', 'alpha', 'beta', 'means',  'kurtosis', 'skewness',  'svd_entropy'],
                #'features' : ['alpha', 'means', 'entropy',  'kurtosis'],
                'envir' : ['luxmetre','sonometre'], 
                'data_repo' : './data/',
                'fe' : 256, #Hz
                'featCalc_win_size' : 30, #s
                'featCalc_win_overlap' : 1./2,
                'eegView_win_size' : 30 #s
            }
        self.selected = collections.OrderedDict({
                'subject' : 'P03',
                'channels' : [2,2,2],
                'features' : [2,2,2,2,2,2,2],
                'feat_chan': 'Cz',
                'envir' : [2,2]
        })
        self.last_selected = self.selected.copy()
        ## Usefull params
        self.nb_win_EEG_values = self.params['eegView_win_size'] * self.params['fe']
        print "nb EEG values : ", self.nb_win_EEG_values
        self.EEG_Xpos = np.round(self.nb_win_EEG_values/2)
        print "EEG_Xpos: ", self.EEG_Xpos 
        self.Feat_Xpos = 0
        
        self.dialogPlotEdit = DialogWindow(self, self.params, self.selected)
        
        ## Main Window and Layout
        self.main_win = QtGui.QWidget()
        self.main_win.setWindowTitle('EEG Super Viewer')
        self.main_win.resize(1200, 1000)
        self.main_layout = QtGui.QGridLayout()  
        self.main_win.setLayout(self.main_layout)

        ## Graph Properties Optins
        self.prop_layout = QtGui.QHBoxLayout()
        ## Subject selected
        vb_txt_subject = QtGui.QLabel('Subject selected :')
        self.prop_layout.addWidget(vb_txt_subject)
        subject_combo = QtGui.QComboBox()
        subject_combo.addItems(self.params['subjects'])
        self.prop_layout.addWidget(subject_combo)               #TODO set combo initial to self.selected['subject']
        self.connect(subject_combo, QtCore.SIGNAL('activated(QString)'), self.change_subject)     
        # EEG Time #TODO
        vb_time_EEG = QtGui.QLabel('EEG time :')
        self.prop_layout.addWidget(vb_time_EEG)
        ## Edition windows
        self.EditButton = QtGui.QPushButton("Edit Plots properties")
        self.EditButton.clicked.connect(self.on_push_Edit_Button)
        self.prop_layout.addWidget(self.EditButton)
        self.main_layout.addLayout(self.prop_layout, 0, 0)
        
        #~ self.dialogPlotEdit = DialogWindow(self, self.params, self.selected)

        ## Grapfics window
        self.gWin = pg.GraphicsWindow()
        #~ self.label = pg.LabelItem(justify='right')
        #~ self.gWin.addItem(self.label)
        self.eeg_plot = self.gWin.addPlot(row=1, col=0)  #eeg_plot and feat_plot are viewbox
        self.eeg_plot.invertY()
        self.eeg_plot.setMouseEnabled(x=True, y=True)
        self.feat_plot = self.gWin.addPlot(row=2, col=0)
        self.feat_plot.setMouseEnabled(x=True, y=True)
        self.main_layout.addWidget(self.gWin, 1,0)
               
        ## Line EEG : always in the center
        self.vLine_eeg = pg.InfiniteLine(pos= np.round(self.nb_win_EEG_values/2), angle=90, movable=False)
        self.eeg_plot.addItem(self.vLine_eeg, ignoreBounds=True)
        ## Line feat (movable and update EEG view)
        self.vLine_feat = pg.InfiniteLine(pos=self.Feat_Xpos, angle=90, movable=True)
        self.feat_plot.addItem(self.vLine_feat, ignoreBounds=True)
        self.vLine_feat.sigPositionChangeFinished.connect(self.update_cursor_pos)
    
        ## Load and init plots
        self.nbEEGsamples = 0 ## updated in loadSubjectdata
        self.nbFeatSamples = 0
        self.env_sigs = 0
        self.loadSubjectdata()
        self.update_eeg_plots()
        self.load_feat_plots()

        self.main_win.show()
      
    def on_push_Edit_Button(self):
        print "Properties Pushed"    
        self.dialogPlotEdit.exec_()

    def on_valid_dialogWindow(self):
        print 'validation dialogWindow'
        self.dialogPlotEdit.close()
    
    def update_cursor_pos(self, evt):
        win =self.params['featCalc_win_size']
        featCalc_win_overlap =self.params['featCalc_win_overlap']
        fe = self.params['fe']
        self.Feat_Xpos = np.round(self.vLine_feat.value())   # Or int, depends how you want to proceed betwen feat dots ?
        if self.Feat_Xpos < 0:
            self.Feat_Xpos = 0
        if self.Feat_Xpos > self.nbEEGsamples:
            self.Feat_Xpos = self.nbEEGsamples
        print "new feat pos is : ", self.Feat_Xpos  #TODO put it in time
        self.EEG_Xpos = self.Feat_Xpos * (win*featCalc_win_overlap*fe)
        print "new eeg pos is : ", self.EEG_Xpos  #TODO put it in time
        
        self.update_eeg_plots()
    
    def load_feat_plots(self):
        nb_feat = len(self.params['features'])      
        self.feat_plot.clear()
        for j in range(nb_feat):
            data = self.feat_df[self.params['features'][j]][self.selected['subject']][self.selected['feat_chan']].values.reshape((self.nbFeatSamples))
            self.feat_plot.plot(data, pen=(j, nb_feat*1.3 ))
        self.vLine_feat.setValue(self.Feat_Xpos)
        self.feat_plot.addItem(self.vLine_feat, ignoreBounds=True)
        
    def update_eeg_plots(self):
        print "update EEG plots, self.EEG_Xpos is :", self.EEG_Xpos
        ## EEG params
        nb_chan = len(self.params['channels'])
        base_offset = self.params['base_offset']
        chan_offset = self.params['chan_offset']
        gain = self.params['gain']
        
        x0 = np.int(self.EEG_Xpos - self.nb_win_EEG_values/2)
        x1 = np.int(self.EEG_Xpos + self.nb_win_EEG_values/2)
        print "x0 : ", x0
        print "x1 : ", x1
        eeg_win = np.empty((x1-x0))
        
        ## EEG Lines plots
        self.eeg_plot.clear()
        for i, name_chan in enumerate(self.params['channels']):
            eeg_win = self.eeg_df[name_chan][x0:x1].values * gain+(nb_chan - i)*chan_offset
            self.eeg_plot.plot(eeg_win, pen="g")
            
        ## Update EEG central Line
        self.eeg_plot.addItem(self.vLine_eeg, ignoreBounds=True)
               
    def change_subject(self, text):
        self.selected['subject'] = str(text)
        print 'Patient selected : ',  self.selected['subject']
        self.loadSubjectdata()
        self.update_eeg_plots()
        self.load_feat_plots()
        
    def loadSubjectdata(self):
        ##load eeg data
        print "subject file : ", join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.h5')
        eeg_Store = pd.HDFStore(join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.h5')) 
        self.eeg_df = eeg_Store.df
        
        ##load features data
        self.feat_df = {}
        for feat in self.params['features']:
            print "file : ", join(self.params['data_repo'], feat + '.h5')
            feat_Store = pd.HDFStore(join(self.params['data_repo'], feat + '.h5'))  # read_hdf ?? 
            self.feat_df[feat] = feat_Store.df.dropna()
           
        ##load environment data
        env_raw = join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.raw')
        env_raw_header = join(self.params['data_repo'], self.selected['subject'] , self.selected['subject']  +'.header')
        d = self.read_header(env_raw_header)
        
        ## (re)set params
        self.nbEEGsamples = np.shape(self.eeg_df['Cz'])[0]
        print "size EEG : ", self.nbEEGsamples
        self.nbFeatSamples = np.shape(self.feat_df[self.params['features'][0]])[0]
        print "nb feat samples : ", self.nbFeatSamples
        self.env_sigs = np.fromfile(env_raw, dtype = d['dtype'],).reshape(-1, d['nbvoies'])
        print "size env sigs : ", np.shape(self.env_sigs)[0]
        self.EEG_Xpos = np.round(self.nb_win_EEG_values/2)
        self.Feat_Xpos = 0
        
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
        
def main():
    data_repo = './data/'
    #~ if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        #~ QtGui.QApplication.instance().exec_()
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main() 
