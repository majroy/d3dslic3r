#!/usr/bin/env python
'''
d3dslic3r export_widget - popup to allow for directing export formats
'''

__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2014--"

import os, io
import subprocess as sp
import numpy as np

from PyQt5 import QtGui, QtWidgets, QtCore, QtSvg
from PyQt5.QtCore import Qt

class export_widget(QtWidgets.QDialog):

    def __init__(self, parent, slice_data):
        super(export_widget, self).__init__(parent)
        self.slice_data = slice_data

        self.setWindowTitle("d3dslic3r - export")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumSize(QtCore.QSize(450, 200))
        
        self.clip_label = QtWidgets.QLabel()
        self.export_status_label = QtWidgets.QLabel()
        pix_map1 = QtGui.QPixmap(resource_filename("d3dslic3r","meta/clippy.png"))
        self.clip_label.setPixmap(pix_map1)

        param_layout = QtWidgets.QGridLayout()
        
        desc = QtWidgets.QLabel("Hmm. It looks like you're exporting some slices and paths. The format will be whatever is set as the prefix, with an integer for the slice number, followed by the path number. For example, if the prefix is 'Slice', then the 3rd path of the 4th slice would be 'Slice_3_2.txt'.")
        desc.setWordWrap(True) 
        
        prefix_label = QtWidgets.QLabel("File prefix:")
        self.prefix = QtWidgets.QLineEdit("Slice")
        
        work_dir_path_label = QtWidgets.QLabel('Working directory:')
        self.work_dir_path = QtWidgets.QLineEdit()
        wd_choose_path = QtWidgets.QPushButton('...')
        wd_choose_path.setMaximumWidth(60)
        wd_choose_path.setAutoDefault(False)
        
        export = QtWidgets.QPushButton('Execute')
        
        param_layout.addWidget(prefix_label,0,0,1,1)
        param_layout.addWidget(self.prefix,0,1,1,2)
        param_layout.addWidget(export,0,3,1,1)
        param_layout.addWidget(work_dir_path_label,1,0,1,1)
        param_layout.addWidget(self.work_dir_path,1,1,1,2)
        param_layout.addWidget(wd_choose_path,1,3,1,1)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(desc)
        main_layout.addLayout(param_layout)
        

        clips_layout = QtWidgets.QHBoxLayout()
        clips_layout.addWidget(self.export_status_label)
        clips_layout.addStretch(1)
        clips_layout.addWidget(self.clip_label)
        
        # clips_layout.addWidget(svg2)
        main_layout.addLayout(clips_layout)
        
        wd_choose_path.clicked.connect(self.set_wd)
        export.clicked.connect(self.export)
        
        self.setLayout(main_layout)
        self.show()

    def set_wd(self):
        dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if dir != '':
            self.work_dir_path.setText(dir)
        else:
            return
    
    def export(self):
        """
        If the current working directory is valid, write out all of the entries of each slice_obj in slice_data to txt files with np.genfromtxt
        """
        
        if not os.path.isdir(self.work_dir_path.text()):
            return
        
        i = 0
        for slice_obj in self.slice_data:
            j = 0
            if slice_obj is not None:
                if slice_obj.paths is not None:
                    for path in slice_obj.paths:
                        np.savetxt(os.path.join(self.work_dir_path.text(),"%s_%i_%i.txt"%(self.prefix.text(),i,j)),path)
                    j+=1
            i+=1
        
        pix_map2 = QtGui.QPixmap(resource_filename("d3dslic3r","meta/dippy.png"))
        self.clip_label.setPixmap(pix_map2)
        self.export_status_label.setText("Complete.")
        self.clip_label.update()
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = export_widget(None, None)
    sys.exit(app.exec_())