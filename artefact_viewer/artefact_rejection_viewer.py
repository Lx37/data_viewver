"""
Artefact detection viewer for Florent - Coma project

- load h5 data with time as index
(concatenated if several recording)
- predefined artifacts :

visualisation options :
- removes averaged ref
- apply filter

"""
import sys
from os.path import isfile, join
import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from scipy import signal

from tools import *


class date_EEG_Xaxis(pg.AxisItem):
    def __init__(self, dataFrame_index, *arg, **kargs):
    	pg.AxisItem.__init__(self, *arg, **kargs)
    	self.dataFrame_index = dataFrame_index

    def setDataFrameIndex(self, dataFrame_index):
    	self.dataFrame_index = dataFrame_index

    def tickStrings(self, values, scale, spacing):
    	return [date.strftime("%H:%M:%S") for date in self.dataFrame_index[values]]


class Artefact_rejection_viewer(ViewerBase):
    
    def __init__(self, with_time_seeker):
    	super(Artefact_rejection_viewer, self).__init__()
        self.with_time_seeker = with_time_seeker
        self.initUI()

    def initUI(self, params = None, optionParams = None):

        if params == None:
            self.params = {
            	'data_repo'		: './../data_node/',
            	'sub_base_name' : ['_0_EEGBrut', '_Concat_EEGBrut', '_artf'],
        		'subjects'		: ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P21', 'S01'],
        		'selected_sub'	: 'S01',
        		'all_chan'		: ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2', 'veog+', 'heog+', 'emg+', 'ecg+'],
        		'eeg_chan'      : ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2'],
                'physio_chan'   : ['veog+', 'heog+', 'emg+', 'ecg+'],
                'fe'			: 256. #Hz
        		}
        if optionParams == None:
        	self.optionParams = {
        		'filt_f0'		: 0.05,    #Hz
        		'filt_f1'		: 30.,      #Hz
        		'Ampl_th'		: 200,     #micro volt
        		'Sampl_th'		: 2,       #sample
        		'win_size'		: 30,      #s
        		'win_step'		: 1./2,
        		'gain' 			: 1,
        		'base_offset'	: 0,
        		'chan_offset'	: 300,
                'physio_offset' : 1000,
        		'auto_detect'	: False,
        		'filter'		: False,
        		'remove_avRef'	: False,
        		'EEG_chan_ref'	: ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2'],
                'region_size'   : 768,      #samples = 3s ici
        	}

        self.dialogArtefEdit = Artefact_DialogWindow(self)      
        self.setWindowTitle('EEG Artefact Viewer')
        self.resize(1200, 1000)
        self.main_layout = QtGui.QGridLayout()  
        self.setLayout(self.main_layout)

        ## Set background in white
        #pg.setConfigOption('background', 'w')

        ## Graph Properties Options
        self.prop_layout = QtGui.QHBoxLayout()
        ## Subject selected
        vb_txt_subject = QtGui.QLabel('Subject selected :')
        self.prop_layout.addWidget(vb_txt_subject)
        subject_combo = QtGui.QComboBox()
        subject_combo.addItems(self.params['subjects'])
        subject_combo.setCurrentIndex(self.params['subjects'].index(self.params['selected_sub']))
        self.prop_layout.addWidget(subject_combo)               #TODO set combo initial to self.selected['subject']
        self.connect(subject_combo, QtCore.SIGNAL('activated(QString)'), self.change_subject)

        ## Edition windows
        self.EditButton = QtGui.QPushButton("Options")
        self.EditButton.clicked.connect(self.on_push_Edit_Button)
        self.prop_layout.addWidget(self.EditButton)
        ## Save artefects
        self.SaveButton = QtGui.QPushButton("Save")
        self.SaveButton.clicked.connect(self.on_push_Save_Button)
        self.prop_layout.addWidget(self.SaveButton)
        self.main_layout.addLayout(self.prop_layout, 0, 0)

        ## EEG Grapfics window
        self.EEG_GView = pg.GraphicsView()

        #~ self.label = pg.LabelItem(justify = 'right')
        #~ self.EEG_GView.addItem(self.label)
        #axisEEG = EEGAxis(sampling_rate= self.params['fe'], eegView_win_size=self.params['win_size'], orientation = 'bottom')
        #axisEEG = date_EEG_Xaxis(orientation = 'bottom')
        
        self.EEG_Xaxis = date_EEG_Xaxis(orientation='bottom', dataFrame_index=[])
        self.EEG_Yaxis = pg.AxisItem(orientation='left')
        values = np.arange(self.optionParams['base_offset']+self.optionParams['chan_offset'], 
            self.optionParams['chan_offset']*(len(self.params['eeg_chan'])+1), self.optionParams['chan_offset'])
        Yticks = [(i,j) for i,j in zip(values, self.params['eeg_chan'])]
        #Yticks.append('ref')
        self.EEG_Yaxis.setTicks([Yticks])
        #self.eeg_plot = self.EEG_GView.addPlot(row=1, col=0, axisItems={'bottom': self.EEG_Xaxis})  #eeg_plot and feat_plot are viewbox
        
        self.viewBox = MyViewBox()
        self.eeg_plot = pg.PlotItem(viewBox = self.viewBox,  axisItems={'bottom': self.EEG_Xaxis, 'left':self.EEG_Yaxis})
        self.eeg_plot.hideButtons()
        self.EEG_GView.setCentralItem(self.eeg_plot)
        self.eeg_plot.invertY()
        #self.eeg_plot.setMouseEnabled(x=True, y=True)
        # Add the graphic window to the view. But maybe we should not ??
        self.main_layout.addWidget(self.EEG_GView, 1,0)

        self.physio_Yaxis = pg.AxisItem(orientation='left')
        values = np.arange(self.optionParams['base_offset']+self.optionParams['physio_offset'], 
            self.optionParams['physio_offset']*(len(self.params['physio_chan'])+1), self.optionParams['physio_offset'])
        Yticks = [(i,j) for i,j in zip(values, self.params['physio_chan'])]
        self.physio_Yaxis.setTicks([Yticks])

        self.physio_GView = pg.GraphicsView()
        self.viewBox2 = MyViewBox()
        self.physio_plot = pg.PlotItem(viewBox = self.viewBox2, axisItems={'left':self.physio_Yaxis})
        self.physio_plot.hideButtons()
        self.physio_plot.invertY()
        self.physio_GView.setCentralItem(self.physio_plot)
        self.main_layout.addWidget(self.physio_GView,2,0)
      

        if self.with_time_seeker:
            self.timeseeker = TimeSeeker(show_slider = False, show_spinbox = False, show_label = False)
            self.main_layout.addWidget(self.timeseeker)
            self.timeseeker.set_start_stop(0., 100000.) #max sample number
            self.timeseeker.time_changed.connect(self.seek)
            self.timeseeker.fast_time_changed.connect(self.fast_seek)

        self.main_layout.setRowStretch(1,3)
        self.main_layout.setRowStretch(2,1)

        ## EEG init params
        self.nb_win_EEG_sample = self.optionParams['win_size'] * self.params['fe']
        self.EEG_Xpos = 0
        self.curves = []

        #Artef init
        #self.vLine = []
        self.auto_ref_artf = np.array([])
        self.added_lines = [] 
        self.manual_ref_artf = np.array([])
        self.added_regions = []
        self.existingArtefile = False

        # TODO fin du init.

        # Pre-plot data
        self.eeg_store=False
        self.loadSubjectdata()
        
        self.show()
        
    def set_params(params = None):
        print "todo"

    def loadSubjectdata(self):
    	filename = self.params['selected_sub'] + self.params['sub_base_name'][1] + '.h5'
    	file_path = join(self.params['data_repo'], self.params['selected_sub'], filename )
    	if not isfile(file_path):
    		filename = self.params['selected_sub'] + self.params['sub_base_name'][0] + '.h5'
    		file_path = join(self.params['data_repo'], self.params['selected_sub'] , filename)
    	print "load subject file : ", file_path
        if self.eeg_store: #if one file was already open, close it
            self.eeg_store.close()
    	self.eeg_store = pd.HDFStore(file_path) #open
    	self.eeg_raw_df = self.eeg_store.eeg_raw_df #read data
    	#TODO : init AllChan by sub because not the same number (cf temoin..)
        self.EEG_Xaxis.setDataFrameIndex(self.eeg_raw_df.index)
        self.eeg_plot.clear()
        # init curves
        self.EEG_Xpos = 0
        self.timeseeker.t = 0
        self.curves = []
        nb_chan = len(self.params['eeg_chan']) # +1 for ref
        for i, name_chan in enumerate(self.params['eeg_chan']):
            #eeg_win = self.eeg_raw_df[name_chan][x0:x1].values * gain + (nb_chan - i)*chan_offset
            curve = self.eeg_plot.plot([np.nan],  pen=(i, nb_chan*1.3 ))
            self.curves.append(curve)
        #curve = self.eeg_plot.plot([np.nan],  pen=(i+1, nb_chan*1.3 ))
        #self.curves.append(curve)

        self.physio_plot.clear()
        self.other_curves = []
        nb_chan = len(self.params['physio_chan'])
        for i, name_chan in enumerate(self.params['physio_chan']):
            #eeg_win = self.eeg_raw_df[name_chan][x0:x1].values * gain + (nb_chan - i)*chan_offset
            curve = self.physio_plot.plot([np.nan],  pen=(i, nb_chan*1.3 ))
            self.other_curves.append(curve)

        #load artefact dataframe if exits or create it
        filename = self.params['selected_sub'] + self.params['sub_base_name'][2] + '.h5'
        file_path = join(self.params['data_repo'], self.params['selected_sub'] , filename)
        self.artf_raw_df = pd.HDFStore(file_path)
        
        if not self.artf_raw_df['auto'].empty: #init to data from file
            self.existingArtefile = True
            self.auto_ref_artf =  np.transpose(self.artf_raw_df['auto'].values)
            print "artef file found. data are : ", self.auto_ref_artf 
            print np.shape(self.auto_ref_artf)

        self.get_ref()
        if self.optionParams['auto_detect']:
            self.auto_detect_artef()
            
        self.refresh()

    def get_ref(self):
        print 'start computing av_ref'
        self.eeg_av_ref = np.average(self.eeg_raw_df[self.optionParams['EEG_chan_ref']].values, axis = 1)
        #print "shape eeg_av_ref : ", np.shape(self.eeg_av_ref)

    def refresh(self, fast = False):
        print "self.time : ", self.timeseeker.t
        #print " self.timeseeker.step_size : ", self.timeseeker.step_size
        self.EEG_Xpos = int(self.timeseeker.t * self.params['fe'])
        x0 = np.int(self.EEG_Xpos)
        x1 = np.int(self.EEG_Xpos + self.nb_win_EEG_sample)

        ## EEG params
        base_offset = self.optionParams['base_offset']
        chan_offset = self.optionParams['chan_offset']
        gain = self.optionParams['gain']
        nb_chan = len(self.params['eeg_chan'])
        fe = self.params['fe']

        for i, name_chan in enumerate(self.params['eeg_chan']):
            eeg_win = self.eeg_raw_df[name_chan].iloc[x0:x1].values

            if name_chan in self.params['eeg_chan']:
                if self.optionParams['remove_avRef']:
                    eeg_win = eeg_win - self.eeg_av_ref[x0:x1]

                if self.optionParams['filter']:
                    b, a = signal.butter(4, [self.optionParams['filt_f0']/fe, self.optionParams['filt_f1']/fe], btype='band')
                    # bp = signal.firwin(4, [self.optionParams['filt_f0'], self.optionParams['filt_f1']])
                    # numpy.convolve(eeg_win, bp)
                    eeg_win = signal.filtfilt(b, a, eeg_win)
            eeg_win = eeg_win * gain + (nb_chan - i)*chan_offset
            self.curves[i].setData(np.arange(x0, x1), eeg_win)
        #self.curves[i+1].setData(np.arange(x0, x1), self.eeg_av_ref[x0:x1])

        physio_offset = self.optionParams['physio_offset']
        nb_chan = len(self.params['physio_chan'])
        for i, name_chan in enumerate(self.params['physio_chan']):
            other_win = self.eeg_raw_df[name_chan].iloc[x0:x1].values * gain + (nb_chan - i)*physio_offset
            self.other_curves[i].setData(np.arange(x0, x1), other_win)

        # show a line for each artef auto detected
        if self.optionParams['auto_detect'] or self.existingArtefile == True:
            for i,j in enumerate(self.added_lines): #removes all vlines.
                self.eeg_plot.removeItem(j)
            for x in np.nditer(self.auto_ref_artf[0]):
                if (x0 <= x <= x1):
                    vLine = pg.InfiniteLine(pos=x, angle=90, movable=False)
                    self.eeg_plot.addItem(vLine)
                    self.added_lines.append(vLine)

        #show if a region is defined inside the window
        if self.added_regions:
            for i,j in enumerate(self.added_regions): 
                v1, v2 = j.getRegion()
                print v1, v2
                if (v1 <= x0 or v1 >= x1) or (v2 <= x0 or v2 >= x1):
                    self.eeg_plot.removeItem(j)
                    self.manual_ref_artf = [self.manual_ref_artf, [np.int(v1),np.int(v2)]] #TODO : add code ??
        print "self.manual_ref_artf : ", self.manual_ref_artf
        print "and size : ", np.shape(self.manual_ref_artf)
        if self.manual_ref_artf:
            for x,y in np.nditer(self.manual_ref_artf):
                if (x0 <= x <= x1) and (x0 <= y <= x1):
                    region = pg.LinearRegionItem(values = [x, y])
                    self.eeg_plot.addItem(region)
                    self.added_regions.append(region)




        self.is_refreshing = False

    def change_subject(self, text):
        self.params['selected_sub'] = str(text)
        print "selected subject : " + self.params['selected_sub']
        self.loadSubjectdata()
        #self.update_eeg_plots()

    def auto_detect_artef(self):
        self.existingArtefile = False
        self.auto_ref_artf = np.array([])
        amp_th = self.optionParams['Ampl_th']
        samp_th = self.optionParams['Sampl_th']
        #TODO pour le moment que sur 2 echantillons et sur ref moy.
        ref_diff = np.ediff1d(self.eeg_av_ref)
        self.auto_ref_artf = np.where(np.abs(ref_diff) > amp_th)
        print "Found ", np.shape(self.auto_ref_artf)[1], " artifacts."
        self.refresh()

    def rm_auto_detect_artef(self):
        self.auto_ref_artf = np.array([])
        self.refresh()

    def on_valid_dialogWindow(self):
        print 'on_valid_dialogWindow'
        self.optionParams['auto_detect'] = self.dialogArtefEdit.artf_checkBox.isChecked()
        self.optionParams['filter'] = self.dialogArtefEdit.filt_checkBox.isChecked()
        #self.optionParams['win_size'] = self.dialogArtefEdit.win_size_ql.text()
        self.optionParams['remove_avRef'] = self.dialogArtefEdit.rmRef_checkBox.isChecked()

        self.optionParams['Ampl_th'] = int(self.dialogArtefEdit.artf_ampl_ql.text())
        self.optionParams['Sampl_th'] = int(self.dialogArtefEdit.artf_sampl_ql.text())
        self.optionParams['filt_f0'] = float(self.dialogArtefEdit.filt_f0_ql.text())
        self.optionParams['filt_f1'] = float(self.dialogArtefEdit.filt_f1_ql.text())
       # self.optionParams['win_size'] = int(self.dialogArtefEdit.win_size_ql.text())
        
        self.dialogArtefEdit.close()
        if self.optionParams['auto_detect']:
            self.auto_detect_artef()
        else:
            self.rm_auto_detect_artef()
        self.refresh()

    def keyPressEvent(self, ev):
        print 'ici'
        print ev.key()
        if ev.key() == 16777236: # >
            self.timeseeker.t = self.timeseeker.t + self.timeseeker.step_size
            self.refresh()
        if ev.key() == 16777234: # >
            self.timeseeker.t = self.timeseeker.t - self.timeseeker.step_size
            self.refresh()

        if ev.key() == 49: #1
            print 'touche 1'
            x0 = np.int(self.EEG_Xpos + self.nb_win_EEG_sample/2 - self.optionParams['region_size'])
            x1 = np.int(x0 + 2*self.optionParams['region_size'])
            region = pg.LinearRegionItem(values = [x0, x1])
            self.added_regions.append(region)
            self.eeg_plot.addItem(region)

    def on_push_Edit_Button(self):  
        self.dialogArtefEdit.exec_()

    def on_push_Save_Button(self):
        print "Save"    
        self.update_artf_raw_df()
        #save artefacts with infos

    def update_artf_raw_df(self):
        #Auto :
        if self.auto_ref_artf:
            auto_artef = []
            auto_artef_idx = []
            for x in np.nditer(self.auto_ref_artf[0]):
                auto_artef.append(x)
                auto_artef_idx.append(self.eeg_raw_df.index[np.int(x)])
            self.artf_raw_df['auto'] =  pd.DataFrame(auto_artef, index=auto_artef_idx)
            self.artf_raw_df['auto_info'] = pd.Series({'Ampl_th': self.optionParams['Ampl_th'],
                                                       'Sampl_th' : self.optionParams['Sampl_th']})

        if self.manual_ref_artf:
            print "TODO"

    def closeEvent(self, ev):
        print 'Close'
        self.update_artf_raw_df()
        self.artf_raw_df.close()
        self.eeg_store.close()

def main():
    data_repo = './../data/'
    #~ if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        #~ QtGui.QApplication.instance().exec_()
    with_time_seeker = True
    app = QtGui.QApplication(sys.argv)
    ex = Artefact_rejection_viewer(with_time_seeker)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 