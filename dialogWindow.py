

from pyqtgraph.Qt import QtGui, QtCore

"""

parent needs on_valid_dialogWindow method
"""


class DialogWindow(QtGui.QDialog):
    def __init__(self, parent=None, params=None, selected=None):
        super(DialogWindow, self).__init__(parent)
        self.parent = parent
        self.selected = selected
        self.params = params

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        #~ self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.buttonBox)
     
        #~ ## Select Subject
        #~ vb_txt_subject = QtGui.QLabel('Select a subject :')
        #~ self.verticalLayout.addWidget(vb_txt_subject)
        #~ subject_combo = QtGui.QComboBox()
        #~ self.verticalLayout.addWidget(subject_combo)
        #~ subject_combo.addItems(self.params['subjects'])
        #~ self.connect(subject_combo, QtCore.SIGNAL('activated(QString)'), self.change_subject)
        
        ## Ok button
        self.OkButton = QtGui.QPushButton("Ok")
        self.verticalLayout.addWidget(self.OkButton)
        
        self.connect(self.OkButton, QtCore.SIGNAL("clicked()"), self.parent.on_valid_dialogWindow)
        
    
    def change_subject(self, text):
        self.selected['subject'] = str(text)
        print 'Patient selected : ',  self.selected['subject']

