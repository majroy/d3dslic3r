#!/usr/bin/env python
'''
Slic3 and dic3!
'''

__author__ = "M.J. Roy"
__version__ = "0.4"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2024-"

import sys,os,ctypes
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
import vtk
import importlib.resources

import d3dslic3r.slic3_widget as slic3_widget
from d3dslic3r.gui_common import make_splash


class main_window(QtWidgets.QMainWindow):
    '''
    Need to create a inherited version of a QMainWindow to override the closeEvent method to finalize any tabs before garbage collection when running more than one vtkWidget.
    '''
    def __init__(self, app):
        super().__init__()
        
        ico = importlib.resources.files('d3dslic3r') / 'meta/sys_icon.png'
        with importlib.resources.as_file(ico) as path:
            self.setWindowIcon(QtGui.QIcon(path.__str__()))
        self.setWindowTitle("d3dslic3r - main v%s" %__version__)
        if os.name == 'nt':
            myappid = 'd3dslic3r.main.%s'%__version__ # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) #windows taskbar icon
        
        screen = QtWidgets.QApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.setMinimumSize(QtCore.QSize(int(2*rect.width()/3), int(7*rect.height()/8)))

        
        self.initialize_all()
    
    def center(self):
        frame = self.frameGeometry()
        center = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())
    
    def closeEvent(self, event):
        '''
        Need to finalize all VTK widgets otherwise openGL errors abound
        '''
        self.slic3_widget.ui.vtkWidget.close()


    def initialize_all(self):
        self.setup_slic3()

    def setup_slic3(self):
        '''
        create an instance of the model viewer interactor with current main_window as parent.
        '''
        self.slic3_widget=slic3_widget.interactor(self)
        self.slic3_widget.iren.Initialize()
        self.setCentralWidget(self.slic3_widget)
        #or add it to a layout . . .

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    splash = make_splash()
    splash.show()
    
    app_main_window = main_window(app)
    app_main_window.center()
    app_main_window.show()
    QTimer.singleShot(1500, splash.close)
    
    sys.exit(app.exec_())