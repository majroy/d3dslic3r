#!/usr/bin/env python
'''
pyCM fea_widget - runs external thread to run an FEA from a pyCM output file.
'''

__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2014--"

import os, io
import subprocess as sp
import numpy as np
import vtk
import vtk.util.numpy_support as v2n
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yaml
from d3dslic3r_gui_common import get_file, get_save_file
import importlib.resources

class execute(QThread):
    '''
    Sets up and runs external thread, emits 100 when done.
    '''
    _signal = pyqtSignal(int)
    def __init__(self,input_file,exe,val,direction):
        super(execute, self).__init__()
        #variables passed here
        self.input_file = input_file
        self.exe = exe #executable path
        self.which_dir = direction
        self.cut_val = val

    def run(self):
        current_dir = os.getcwd()
        output_dir = os.path.dirname(self.input_file)
        base = os.path.basename(self.input_file)
        os.chdir(output_dir)
        
        try:
            print('Slic3r console exec: %s -i %s'%(self.exe,base))
        
            out=sp.check_output([self.exe,"--cut",str(self.cut_val),base], shell=True)
            print("Slic3r output log:")
            print("----------------")
            print(out.decode("utf-8"))
            print("----------------")
            print("d3dslic3r: Slic3r run completed . . . Idle")
        except sp.CalledProcessError as e:
            print("Slic3r command failed for some reason.")
            print(e)
        
        self._signal.emit(100)
        os.chdir(current_dir)
        
    
class slic3r_widget(QtWidgets.QDialog):

    def __init__(self, parent, file):
        super(slic3r_widget, self).__init__(parent)
        self.file = file

        self.setWindowTitle("d3dslic3r using Slic3r: %s"%os.path.basename(self.file))
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumSize(QtCore.QSize(450, 200))

        param_layout = QtWidgets.QGridLayout()
        
        self.cut_x_rb=QtWidgets.QRadioButton("Cut X")
        self.cut_x_rb.setEnabled(False)
        self.cut_y_rb=QtWidgets.QRadioButton("Cut Y")
        self.cut_y_rb.setEnabled(False)
        self.cut_z_rb=QtWidgets.QRadioButton("Cut Z")
        self.cut_val=QtWidgets.QDoubleSpinBox()
        self.cut_z_rb.setChecked(True)

        mtype_button_group = QtWidgets.QButtonGroup()
        mtype_button_group.addButton(self.cut_x_rb)
        mtype_button_group.addButton(self.cut_y_rb)
        mtype_button_group.addButton(self.cut_z_rb)
        mtype_button_group.setExclusive(True)
        
        self.clean_up_cb = QtWidgets.QCheckBox('Remove intermediate files')
        self.clean_up_cb.setToolTip('Remove intermediate files after running command')
        self.clean_up_cb.setChecked(False)
        self.clean_up_cb.setEnabled(False)
        
        param_layout.addWidget(self.cut_x_rb,0,0,1,1)
        param_layout.addWidget(self.cut_y_rb,0,1,1,1)
        param_layout.addWidget(self.cut_z_rb,0,2,1,1)
        param_layout.addWidget(self.cut_val,0,3,1,1)
        param_layout.addWidget(self.clean_up_cb,0,4,1,1)
        
        self.pbar = QtWidgets.QProgressBar(self, textVisible=True)
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setFormat("Idle")
        self.pbar.setFont(QtGui.QFont("Helvetica",italic=True))
        self.pbar.setValue(0)

        self.run_button = QtWidgets.QPushButton('Run')
        slic3r_exec_path_label = QtWidgets.QLabel('Slic3r console executable:')
        self.slic3r_exec_path = QtWidgets.QLineEdit()
        slic3r_choose_path = QtWidgets.QPushButton('...')
        slic3r_choose_path.setMaximumWidth(30)
        slic3r_choose_path.setAutoDefault(False)
        work_dir_path_label = QtWidgets.QLabel('Working directory:')
        self.work_dir_path = QtWidgets.QLineEdit()
        wd_choose_path = QtWidgets.QPushButton('...')
        wd_choose_path.setMaximumWidth(30)
        wd_choose_path.setAutoDefault(False)

        run_layout = QtWidgets.QGridLayout()
        
        run_layout.addWidget(slic3r_exec_path_label,1,0,1,1)
        run_layout.addWidget(self.slic3r_exec_path,1,1,1,2)
        run_layout.addWidget(slic3r_choose_path,1,3,1,1)
        
        run_layout.addWidget(work_dir_path_label,2,0,1,1)
        run_layout.addWidget(self.work_dir_path,2,1,1,2)
        run_layout.addWidget(wd_choose_path,2,3,1,1)
        run_layout.addWidget(self.run_button,3,0,1,1)
        run_layout.addWidget(self.pbar,3,1,1,3)

        self.run_button.clicked.connect(self.run_slic3r)
        slic3r_choose_path.clicked.connect(self.set_slic3r)
        wd_choose_path.clicked.connect(self.set_wd)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(param_layout)
        self.layout.addLayout(run_layout)

        self.setLayout(self.layout)
        self.read_config()
        self.show()

    
    
    def run_slic3r(self):
        self.make_config_change() #save anything that the user might have put into config boxes
        
        self.input_file = get_file("*.stl", self.work_dir_path.text())
        if self.input_file is None:
            return
        
        

        self.thread = execute(self.input_file,self.slic3r_exec_path.text(),        self.cut_val.value(), None) #None should be direction

        self.thread._signal.connect(self.signal_accept)
        self.thread.start()
        self.pbar.setTextVisible(True)
        self.pbar.setStyleSheet("")
        self.pbar.setRange(0,0)
        
    def signal_accept(self, msg):
        if int(msg) == 100:
            self.pbar.setRange(0,100)
            self.pbar.setValue(0)
            self.pbar.setFormat("Complete")
            self.pbar.setStyleSheet("QProgressBar"
              "{"
              "background-color: lightgreen;"
              "border : 1px"
              "}")
    
    def set_slic3r(self):
        f = get_file("*.*")
        if f is None or not(os.path.isfile(f)):
            return
        self.slic3r_exec_path.setText(f)
        self.make_config_change()

    def set_wd(self):
        dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if dir != '':
            self.work_dir_path.setText(dir)
            self.make_config_change()
        else:
            return

    def read_config(self):
        fname=importlib.resources.files('d3dslic3r') / 'meta/d3dslic3r_config.yml'
        with open(fname, 'r') as f:
            read = yaml.safe_load(f)
        
        self.slic3r_exec_path.setText(read['slic3r']['exec'])
        self.work_dir_path.setText(read['slic3r']['work_dir'])


    def make_config_change(self):
        new_entries = dict(
        slic3r_exec = str(self.slic3r_exec_path.text()),
        work_dir = str(self.work_dir_path.text())
        )
        
        fname=importlib.resources.files('d3dslic3r') / 'meta/d3dslic3r_config.yml'
        with open(fname, 'r') as yamlfile:
            cur_yaml = yaml.safe_load(yamlfile)
            cur_yaml['slic3r'].update(new_entries)
        if cur_yaml:
            with open(fname, 'w') as yamlfile:
                yaml.safe_dump(cur_yaml, yamlfile)

    def closeEvent(self, event):
        '''
        Not implemented
        '''
        pass


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv)>1:
        fw = slic3r_widget(None, sys.argv[1])
    else:
        fw = slic3r_widget(None, 'No file specified')
    sys.exit(app.exec_())