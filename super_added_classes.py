import numpy as np

from vispy import app, scene



class FeatureXAxis(scene.Axis):
    
    def __init__(self, *args, **kwargs):
        scene.Axis.__init__(self, *args, **kwargs)
        
        self.Xpos = 0
        
    def print_mouse_event(self, event, what):
        """ print mouse events for debugging purposes """
        print('%s - pos: %r, button: %s,  delta: %r' %
              (what, event.pos, event.button, event.delta))
    
    def on_mouse_press(self, event):
        #~ self.print_mouse_event(event, 'Mouse press')
        self.Xpos =  event.pos[0]




class FeatureLineVisual(scene.visuals.Line):
    #Not used because the number of sent mousse press is equal to the number of features
    
    def __init__(self, *args, **kwargs):
        scene.visuals.Line.__init__(self, *args, **kwargs)
        
        
    def print_mouse_event(self, event, what):
        """ print mouse events for debugging purposes """
        print('%s - pos: %r, button: %s,  delta: %r' %
              (what, event.pos, event.button, event.delta))
    
    
    def on_mouse_press(self, event):

        self.print_mouse_event(event, 'Mouse press')
        