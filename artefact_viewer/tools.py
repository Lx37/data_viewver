# -*- coding: utf-8 -*-
"""
Common tools for viewers.
TimeSeeker from OpenElectrophy
"""

#from .guiutil import *

import quantities as pq
import numpy as np

import pyqtgraph as pg
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import time


class TimeSeeker(QWidget) :
    """
    This is a remote for all Vierwers.
    """
    time_changed = pyqtSignal(float)
    fast_time_changed = pyqtSignal(float)
    
    def __init__(self, parent = None, show_play = True, show_step = True,
                                    show_slider = False, show_spinbox = False, show_label = False,
                                    refresh_interval = .1) :
        QWidget.__init__(self, parent)
        
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)
        
        self.toolbar = QToolBar()
        self.mainlayout.addWidget(self.toolbar)
        t = self.toolbar
        
        self.show_play = show_play
        self.show_step = show_step
        self.show_slider = show_slider
        self.show_spinbox = show_spinbox
        self.show_label = show_label
        
        if show_play:
            but = QPushButton(QIcon('./icons/media-playback-start.png'), '')
            but.clicked.connect(self.play)
            t.addWidget(but)
            
            but = QPushButton(QIcon('./icons/media-playback-stop.png'), '')
            but.clicked.connect(self.stop_pause)
            t.addWidget(but)
            
            t.addWidget(QLabel('Speed:'))
            #~ self.speedSpin = QDoubleSpinBox()
            self.speedSpin = pg.SpinBox()
            t.addWidget(self.speedSpin)
            self.speedSpin.setMinimum(1)
            self.speedSpin.setMaximum(100.)
            self.speedSpin.setSingleStep(0.1)
            self.speedSpin.setValue(1.)
            self.speedSpin.valueChanged.connect(self.change_speed)
            t.addSeparator()
        
        if show_step:
            but = QPushButton('<')
            but.clicked.connect(self.prev_step)
            t.addWidget(but)
            
            self.popupStep = QToolButton( popupMode = QToolButton.MenuButtonPopup,
                                                                        toolButtonStyle = Qt.ToolButtonTextBesideIcon,
                                                                        text = u'Step 15ms'
                                                                        )
            t.addWidget(self.popupStep)
            ag = QActionGroup(self.popupStep )
            ag.setExclusive( True)
            for s in ['30s','20s', '15s', '10s', '5s']:
                act = QAction(s, self.popupStep, checkable = True)
                ag.addAction(act)
                self.popupStep.addAction(act)
            ag.triggered.connect(self.change_step)
            
            but = QPushButton('>')
            but.clicked.connect(self.next_step)
            t.addWidget(but)
            
            t.addSeparator()
        
        if show_slider:
            self.slider = QSlider()
            t.addWidget(self.slider)
            self.slider.setOrientation( Qt.Horizontal )
            self.slider.setMaximum(1000)
            self.slider.setMinimum(0)
            self.slider.setMinimumWidth(200)
            self.slider.valueChanged.connect(self.sliderChanged)
        
        if show_spinbox:
            #~ self.spinbox = QDoubleSpinBox(decimals = 3., minimum = -np.inf, maximum = np.inf, 
                                                                #~ singleStep = 0.05, minimumWidth = 60)
            self.spinbox =pg.SpinBox(decimals = 3., minimum = -np.inf, maximum = np.inf, 
                                                                singleStep = 0.05, minimumWidth = 60)
            t.addWidget(self.spinbox)
            t.addSeparator()
            self.spinbox.valueChanged.connect(self.spinBoxChanged)
        
        if show_label:
            self.labelTime = QLabel('0')
            t.addWidget(self.labelTime)
            t.addSeparator()

        self.timerPlay = QTimer(self)
        self.timerPlay.timeout.connect(self.timerPlayTimeout)
        self.timerDelay = None
        
        # all in s
        self.refresh_interval = refresh_interval #s
        self.step_size = 15 #s
        self.speed = 1.
        self.t = 0 #  s
        self.set_start_stop(0., 10.)
        
        
    def play(self):
        # timer is in ms
        self.timerPlay.start( int(self.refresh_interval*1000.) )

    def stop_pause(self):
        self.timerPlay.stop()
        self.seek(self.t)
    
    def timerPlayTimeout(self):
        t = self.t +  self.refresh_interval*self.speed
        self.seek(t)
    
    def set_start_stop(self, t_start, t_stop, seek = True):
        #~ print 't_start', t_start, 't_stop', t_stop
        assert t_stop>t_start
        self.t_start = t_start
        self.t_stop = t_stop
        if seek:
            self.seek(self.t_start)
        if self.show_spinbox:
            self.spinbox.setMinimum(t_start)
            self.spinbox.setMaximum(t_stop)
        
    def change_step(self, act):
        t = str(act.text())
        print "t est :", t
        self.popupStep.setText(u'Step '+t)
        if t.endswith('ms'):
            self.step_size = float(t[:-2])*1e-3
        else:
            self.step_size = float(t[:-1])
        if self.show_spinbox:
            self.spinbox.setSingleStep(self.step_size)

    def prev_step(self):
        t = self.t -  self.step_size
        self.seek(t)
    
    def next_step(self):
        t = self.t +  self.step_size
        self.seek(t)
    
    def sliderChanged(self, pos):
        t = pos/1000.*(self.t_stop - self.t_start)+self.t_start
        self.seek(t, refresh_slider = False)
    
    def spinBoxChanged(self, val):
        self.seek(val, refresh_spinbox = False)
    
    def seek(self , t, refresh_slider = True, refresh_spinbox = True):
        if self.timerDelay is not None and self.timerDelay.isActive():
            self.timerDelay.stop()
            self.timerDelay = None
        
        self.t = t
        if (self.t<self.t_start):
            self.t = self.t_start
        if (self.t>self.t_stop):
            self.t = self.t_stop
            if self.timerPlay.isActive():
                self.stop_pause()

        if refresh_slider and self.show_slider:
            self.slider.valueChanged.disconnect(self.sliderChanged)
            pos = int((self.t - self.t_start)/(self.t_stop - self.t_start)*1000.)
            self.slider.setValue(pos)
            self.slider.valueChanged.connect(self.sliderChanged)
        
        if refresh_spinbox and self.show_spinbox:
            self.spinbox.valueChanged.disconnect(self.spinBoxChanged)
            self.spinbox.setValue(t)
            self.spinbox.valueChanged.connect(self.spinBoxChanged)
        
        if self.show_label:
            self.labelTime.setText('{:5.3} s'.format(self.t))
        
        self.fast_time_changed.emit(self.t)
        if not self.timerPlay.isActive():
            self.delay_emit()
        
    def change_speed(self , speed):
        self.speed = speed
    
    
    def delay_emit(self):
        if self.timerDelay is not None: return
        self.timerDelay = QTimer(interval = 700, singleShot = True)
        self.timerDelay.timeout.connect(self.timerDelayTimeout)
        self.timerDelay.start()
        
    def timerDelayTimeout(self):
        self.time_changed.emit(self.t)
        self.timerDelay = None





class ViewerBase(QWidget):
    """
    Base for SignalViewer, TimeFreqViewer, EpochViewer, ...
    
    This handle seek and fast_seek with TimeSeeker time_changed and fast_time_changed signals
    """
    need_refresh = pyqtSignal(bool)
    def __init__(self, parent = None):
        super(ViewerBase, self).__init__(parent)

        self.t = 0.
        self.is_refreshing = False
        self.need_refresh.connect(self.refresh, type = Qt.QueuedConnection)
        
        self.delay_timer = QTimer(singleShot = True)
        self.delay_timer.timeout.connect(self.refresh)

    def fast_seek(self, t):
        if self.is_refreshing: 
            return
        self.t = t
        self.is_refreshing = True
        self.need_refresh.emit(True)

    def seek(self, t):
        if self.is_refreshing:
            return
        self.t = t
        self.is_refreshing = True
        self.need_refresh.emit(False)
    
    def refresh(self, fast = False):
        # Implement in subclass
        if fast:
            print 'fast refresh'
        else:
            time.sleep(.5)
            print 'slow refresh'
        self.is_refreshing = False
    
    def delayed_refresh(self, interval = 50):
        if self.delay_timer.isActive():
            return
        else:
            self.delay_timer.setInterval(interval)
            self.delay_timer.start()
        