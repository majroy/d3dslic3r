#!/usr/bin/env python
'''
Slic3 and dic3!
-------------------------------------------------------------------------------
0.1 - Inital release
'''

__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2021-"

import sys,os,ctypes
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
import vtk
import d3dslic3r.slic3_widget as slic3_widget
from d3dslic3r.d3dslic3r_common import make_splash

class main_window(QtWidgets.QMainWindow):
    '''
    Need to create a inherited version of a QMainWindow to override the closeEvent method to finalize any tabs before garbage collection when running more than one vtkWidget.
    '''
    def __init__(self, app):
        super().__init__()
        
        self.setWindowIcon(QtGui.QIcon(resource_filename("d3dslic3r","meta/sys_icon.png")))
        self.setWindowTitle("d3dslic3r - main v%s" %__version__)
        if os.name == 'nt':
            myappid = 'd3dslic3r.main.%s'%__version__ # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) #windows taskbar icon
        
        self.setMinimumSize(QtCore.QSize(1000, 1000))

        
        self.tabWidget = QtWidgets.QTabWidget()

        self.slic3_tab = QtWidgets.QWidget(self.tabWidget)
        self.tabWidget.addTab(self.slic3_tab, "slic3r")
        self.setCentralWidget(self.tabWidget)

        #make menubar
        self.menubar = QtWidgets.QMenuBar(self)
        file_menu = self.menubar.addMenu('&File')

        load_button = QtWidgets.QAction('Load', self)
        load_button.setShortcut('Ctrl+L')
        load_button.setStatusTip('Nil')
        # load_button.triggered.connect(self.populate)

        save_button = QtWidgets.QAction('Save', self)
        save_button.setShortcut('Ctrl+S')
        save_button.setStatusTip('Nil')

        save_as_button = QtWidgets.QAction('Save As...', self)
        save_as_button.setStatusTip('Nil')

        
        exit_button = QtWidgets.QAction('Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.setStatusTip('Exit application')
        exit_button.triggered.connect(self.close)
        
        util_menu = self.menubar.addMenu('&Utilities')

        
        #add actions to menubar
        file_menu.addAction(load_button)
        file_menu.addAction(save_button)
        file_menu.addAction(save_as_button)
        file_menu.addAction(exit_button)
        file_menu.setEnabled(False)


        #add menubar to window
        self.setMenuBar(self.menubar)
        
        #add a status bar
        self.statusbar = QtWidgets.QStatusBar(self)
        # self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        
        self.tabWidget.setCurrentIndex(0)
        
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
        lhLayout = QtWidgets.QHBoxLayout(self.slic3_tab)
        self.slic3_widget=slic3_widget.interactor(self.tabWidget)
        self.slic3_widget.iren.Initialize()
        lhLayout.addWidget(self.slic3_widget)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    splash = make_splash()
    splash.show()
    
    app_main_window = main_window(app)
    app_main_window.center()
    app_main_window.show()
    QTimer.singleShot(2000, splash.close)
    
    sys.exit(app.exec_())