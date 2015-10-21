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


class Artefact_DialogWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Artefact_DialogWindow, self).__init__(parent)
        self.parent = parent
        #self.params = params
        #self.optionParams = optionParams

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.resize(500, 800) # (X,Y)
        #~ self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.title_txt = QtGui.QLabel('General options', self)
        self.title_txt.move(200, 10)
        self.advice_txt = QtGui.QLabel('please enter only number or it will crash.', self)
        self.advice_txt.move(150, 30)
        self.advice_txt.resize(300,30)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.buttonBox)
         
        ## Automated artefact detection 
        self.artf_checkBox = QtGui.QCheckBox('Automatic artefact rejection : ', self)
        self.artf_checkBox.setChecked(self.parent.optionParams['auto_detect'])
        self.artf_checkBox.move(10, 70)
        self.artf_checkBox.resize(300,30)
        self.artf_ampl_txt = QtGui.QLabel('Microvolt threshold : ', self)
        self.artf_ampl_txt.move(40, 110)
        self.artf_ampl_txt.resize(150,30)
        self.artf_ampl_ql = QtGui.QLineEdit(str(self.parent.optionParams['Ampl_th']), self)
        self.artf_ampl_ql.move(200, 110)
        self.artf_sampl_txt = QtGui.QLabel('Sample threshold : ', self)
        self.artf_sampl_txt.move(40, 150)
        self.artf_sampl_txt.resize(150,30)
        self.artf_sampl_ql = QtGui.QLineEdit(str(self.parent.optionParams['Sampl_th']), self)
        self.artf_sampl_ql.move(200, 150)

        ## Filtering 
        self.filt_checkBox = QtGui.QCheckBox('Filter EEG channel (only on view) : ', self)
        self.filt_checkBox.setChecked(self.parent.optionParams['filter'])
        self.filt_checkBox.move(10, 220)  #y+150
        self.filt_checkBox.resize(300,30)
        self.filt_txt1 = QtGui.QLabel('Low frequency (Hz) : ', self)
        self.filt_txt1.move(40, 260)
        self.filt_txt1.resize(150,30)
        self.filt_f0_ql = QtGui.QLineEdit(str(self.parent.optionParams['filt_f0']), self)
        self.filt_f0_ql.move(200, 260)
        self.filt_txt2 = QtGui.QLabel('High frequency (Hz) : ', self)
        self.filt_txt2.move(40, 300)
        self.filt_f1_ql = QtGui.QLineEdit(str(self.parent.optionParams['filt_f1']), self)
        self.filt_f1_ql.move(200, 300)

        ## view size
        self.win_txt1 = QtGui.QLabel('Size (in sec) of the signal view : ', self)
        self.win_txt1.move(10, 400)
        self.win_txt1.resize(300,30)
        self.filt_f0_ql = QtGui.QLineEdit(str(self.parent.optionParams['win_size']), self)
        self.filt_f0_ql.move(250, 400)


        ## Ok button
        self.OkButton = QtGui.QPushButton("Ok")
        self.verticalLayout.addWidget(self.OkButton)
        self.connect(self.OkButton, QtCore.SIGNAL("clicked()"), self.parent.on_valid_dialogWindow)


class date_EEG_axis(pg.AxisItem):
    def __init__(self, dataFrame_index, *arg, **kargs):
    	pg.AxisItem.__init__(self, *arg, **kargs)
    	self.dataFrame_index = dataFrame_index

    def setDataFrameIndex(self, dataFrame_index):
    	self.dataFrame_index = dataFrame_index

    def tickStrings(self, values, scale, spacing):
    	return [date.strftime("%H:%M:%S") for date in self.dataFrame_index[values]]


class Artefact_rejection_viewer(QtGui.QWidget):
    
    def __init__(self):
    	super(Artefact_rejection_viewer, self).__init__()
        self.initUI()

    def initUI(self, params = None, optionParams = None):

        if params == None:
            self.params = {
            	'data_repo'		: './data_node/',
            	'sub_base_name' : ['_0_EEGBrut', '_Concat_EEGBrut'],
        		'subjects'		: ['P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P21', 'S01'],
        		'selected_sub'	: 'P03',
        		'all_chan'		: ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2', 'veog+', 'heog+', 'emg+', 'ecg+'],
        		'fe'			: 256. #Hz
        		}
        if optionParams == None:
        	self.optionParams = {
        		'filt_f0'		: 0.05,	#Hz
        		'filt_f1'		: 30,		#Hz
        		'Ampl_th'		: 200,	#micro volt
        		'Sampl_th'		: 4,		#sample
        		'win_size'		: 30, #s
        		'win_step'		: 1./2,
        		'gain' 			: 1,
        		'base_offset'	: 0,
        		'chan_offset'	: 300,
        		'auto_detect'	: True,
        		'filter'		: True,
        		'remove_avRef'	: True,
        		'EEG_chan_ref'	: ['F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2'],
        	}

        self.dialogArtefEdit = Artefact_DialogWindow(self)

        ## Main Window and Layout
        self.main_win = QtGui.QWidget()
        self.main_win.setWindowTitle('EEG Artefact Viewer')
        self.main_win.resize(1200, 1000)
        self.main_layout = QtGui.QGridLayout()  
        self.main_win.setLayout(self.main_layout)

        ## Graph Properties Options
        self.prop_layout = QtGui.QHBoxLayout()
        ## Subject selected
        vb_txt_subject = QtGui.QLabel('Subject selected :')
        self.prop_layout.addWidget(vb_txt_subject)
        subject_combo = QtGui.QComboBox()
        subject_combo.addItems(self.params['subjects'])
        self.prop_layout.addWidget(subject_combo)               #TODO set combo initial to self.selected['subject']
        self.connect(subject_combo, QtCore.SIGNAL('activated(QString)'), self.change_subject)

        ## Edition windows
        self.EditButton = QtGui.QPushButton("Options")
        self.EditButton.clicked.connect(self.on_push_Edit_Button)
        self.prop_layout.addWidget(self.EditButton)
        #self.main_layout.addLayout(self.prop_layout, 0, 0)

        ## Save artefects
        self.SaveButton = QtGui.QPushButton("Save")
        self.SaveButton.clicked.connect(self.on_push_Save_Button)
        self.prop_layout.addWidget(self.SaveButton)
        self.main_layout.addLayout(self.prop_layout, 0, 0)

        #load EEG data -- to get indexes..
        #self.loadSubjectdata()

        ## EEG Grapfics window
        self.gWin = pg.GraphicsWindow()
        #~ self.label = pg.LabelItem(justify='right')
        #~ self.gWin.addItem(self.label)
        #axisEEG = EEGAxis(sampling_rate= self.params['fe'], eegView_win_size=self.params['win_size'], orientation='bottom')
        #axisEEG = date_EEG_axis(orientation='bottom')
        self.EEG_axis = date_EEG_axis(orientation='bottom', dataFrame_index=[])
        self.eeg_plot = self.gWin.addPlot(row=1, col=0, axisItems={'bottom': self.EEG_axis})  #eeg_plot and feat_plot are viewbox
        self.eeg_plot.invertY()
        #self.eeg_plot.setMouseEnabled(x=True, y=True)
        ## EEG init params
        self.nb_win_EEG_sample = self.optionParams['win_size'] * self.params['fe']
        self.EEG_Xpos = np.round(self.nb_win_EEG_sample/2)

        # Add the graphic window to the view. But maybe we should not ??
        self.main_layout.addWidget(self.gWin, 1,0)

        # Pre-plot data
        self.loadSubjectdata()
        self.update_eeg_plots()

        self.main_win.show()

    def loadSubjectdata(self):
    	filename = self.params['selected_sub']+self.params['sub_base_name'][1]+'.h5'
    	file_path = join(self.params['data_repo'], self.params['selected_sub'], filename )
    	print not isfile(file_path) 
    	if not isfile(file_path):
    		filename = self.params['selected_sub']+self.params['sub_base_name'][0]+'.h5'
    		file_path = join(self.params['data_repo'], self.params['selected_sub'] , filename)
    	print "load subject file : ", file_path
    	eeg_store = pd.HDFStore(file_path) #open
    	self.eeg_raw_df = eeg_store.eeg_raw_df #read data
    	#TODO : init AllChan by sub because not the same number (cf temoin..)

    def update_eeg_plots(self):
    	print "update EEG plots, self.EEG_Xpos is :", self.EEG_Xpos
    	## EEG params
    	base_offset = self.optionParams['base_offset']
    	chan_offset = self.optionParams['chan_offset']
    	gain = self.optionParams['gain']
    	nb_chan = len(self.params['all_chan'])

    	x0 = np.int(self.EEG_Xpos - self.nb_win_EEG_sample/2)
    	x1 = np.int(self.EEG_Xpos + self.nb_win_EEG_sample/2)
    	print "x0 : ", x0
    	print "x1 : ", x1
    	eeg_win = np.empty((x1-x0))
    	## set EEG Axis dates
    	self.EEG_axis.setDataFrameIndex(self.eeg_raw_df.index[x0:x1])
    	## EEG Lines plots
    	self.eeg_plot.clear()
    	for i, name_chan in enumerate(self.params['all_chan']):
    		eeg_win = self.eeg_raw_df[name_chan][x0:x1].values * gain + (nb_chan - i)*chan_offset
    		self.eeg_plot.plot(eeg_win, pen=(i, nb_chan*1.3 ))

    def change_subject(self, text):
        self.params['selected_sub'] = str(text)
        print "selected subject : " + self.params['selected_sub']
        self.loadSubjectdata()
        self.update_eeg_plots()

    def on_push_Edit_Button(self):  
        self.dialogArtefEdit.exec_()

    def on_push_Save_Button(self):
        print "Save Pushed"    
        #save artefacts with infos

    def on_valid_dialogWindow(self):
        print 'validation dialogWindow'
        self.optionParams['Ampl_th'] = int(self.dialogArtefEdit.artf_ampl_ql.text())
        self.optionParams['Sampl_th'] = int(self.dialogArtefEdit.artf_sampl_ql.text())
        self.optionParams['filt_f0'] = int(self.dialogArtefEdit.filt_f0_ql.text())
        self.optionParams['filt_f1'] = int(self.dialogArtefEdit.filt_f1_ql.text())
        
        self.optionParams['auto_detect'] = self.dialogArtefEdit.artf_checkBox.isChecked()
        self.optionParams['filter'] = self.dialogArtefEdit.filt_checkBox.isChecked()
        #self.optionParams['remove_avRef'] = self.dialogArtefEdit.?.isChecked()

        self.dialogArtefEdit.close()
        self.update_eeg_plots()



def main():
    data_repo = './data/'
    #~ if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        #~ QtGui.QApplication.instance().exec_()
    app = QtGui.QApplication(sys.argv)
    ex = Artefact_rejection_viewer()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main() 