#!/usr/bin/env python
'''
Constructor functions/methods for transformation widgets. make_x_button could be abstracted.
'''

import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import importlib.resources


def make_transformation_button_layout(parent_window):
    '''
    Makes a button group that contains a translation and reset button
    '''
    button_layout = QtWidgets.QHBoxLayout()
    parent_window.trans_reset_button = QtWidgets.QPushButton('Reset')
    parent_window.trans_reset_button.setToolTip('Reset all current transformations')
    parent_window.trans_reset_button.setEnabled(False)
    parent_window.translate_drop_button = make_translate_button(parent_window)
    button_layout.addWidget(parent_window.translate_drop_button)
    parent_window.rotate_drop_button = make_rotate_button(parent_window)
    button_layout.addWidget(parent_window.rotate_drop_button)
    parent_window.scale_drop_button = make_scale_button(parent_window)
    button_layout.addWidget(parent_window.scale_drop_button)
    button_layout.addWidget(parent_window.trans_reset_button)
    button_layout.addStretch(1)
    return button_layout


def make_translate_button(parent_window):
    ico = importlib.resources.files('d3dslic3r') / 'meta/translate_icon.png'
    with importlib.resources.as_file(ico) as path:
        translate_icon = QtGui.QIcon(QtGui.QIcon(path.__str__()))
    translate_drop_button = QtWidgets.QToolButton()
    translate_drop_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    translate_drop_button.setCheckable(True)
    translate_drop_button.setMenu(QtWidgets.QMenu(translate_drop_button))
    trans_action = QtWidgets.QWidgetAction(translate_drop_button)
    parent_window.trans_widget = transform_box(parent_window,'translate')
    trans_action.setDefaultWidget(parent_window.trans_widget)
    translate_drop_button.menu().addAction(trans_action)
    translate_drop_button.setIcon(translate_icon)
    translate_drop_button.setToolTip('Translate to new origin')
    return translate_drop_button

def make_rotate_button(parent_window):
    ico = importlib.resources.files('d3dslic3r') / 'meta/rotate_icon.png'
    with importlib.resources.as_file(ico) as path:
        rotate_icon = QtGui.QIcon(QtGui.QIcon(path.__str__()))
    rotate_drop_button = QtWidgets.QToolButton()
    rotate_drop_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    rotate_drop_button.setCheckable(True)
    rotate_drop_button.setMenu(QtWidgets.QMenu(rotate_drop_button))
    trans_action = QtWidgets.QWidgetAction(rotate_drop_button)
    parent_window.rotation_widget = transform_box(parent_window, 'rotate')
    trans_action.setDefaultWidget(parent_window.rotation_widget)
    rotate_drop_button.menu().addAction(trans_action)
    rotate_drop_button.setIcon(rotate_icon)
    rotate_drop_button.setToolTip('Rotate about origin')
    return rotate_drop_button
    
def make_scale_button(parent_window):
    ico = importlib.resources.files('d3dslic3r') / 'meta/scale_icon.png'
    with importlib.resources.as_file(ico) as path:
        scale_icon = QtGui.QIcon(QtGui.QIcon(path.__str__()))
    scale_drop_button = QtWidgets.QToolButton()
    scale_drop_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    scale_drop_button.setCheckable(True)
    scale_drop_button.setMenu(QtWidgets.QMenu(scale_drop_button))
    trans_action = QtWidgets.QWidgetAction(scale_drop_button)
    parent_window.scale_widget = transform_box(parent_window, 'scale')
    trans_action.setDefaultWidget(parent_window.scale_widget)
    scale_drop_button.menu().addAction(trans_action)
    scale_drop_button.setIcon(scale_icon)
    scale_drop_button.setToolTip('Scale over main axes')
    return scale_drop_button

def get_trans_from_euler_angles(ax,ay,az):
    '''
    Based on incoming arguments in *degrees*, return a 4x4 transformation matrix
    '''
    ax = np.deg2rad(ax)
    Rx = np.array([[1,0,0],[0, np.cos(ax), -np.sin(ax)],[0, np.sin(ax), np.cos(ax)]])
    ay = np.deg2rad(ay)
    Ry = np.array([[np.cos(ay), 0, np.sin(ay)],[0,1,0],[-np.sin(ay), 0, np.cos(ay)]])
    az = np.deg2rad(az)
    Rz = np.array([[np.cos(az), -np.sin(az), 0],[np.sin(az), np.cos(az), 0],[0,0,1]])
    R = Rx @ Ry @ Rz
    
    trans = np.identity(4)
    trans[0:3,0:3] = R
    return trans

class transform_box(QtWidgets.QWidget):
    def __init__(self, parent_window, cond, *args, **kwargs):
        '''
        Makes a complete reorientation widget
        '''
        
        super().__init__(*args, **kwargs)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        
        vl = QtWidgets.QVBoxLayout()
        hl = QtWidgets.QHBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()
        translate_box = QtWidgets.QGroupBox('Translate:')
        translate_layout = QtWidgets.QVBoxLayout()
        rotate_box = QtWidgets.QGroupBox('Rotate about:')
        rotate_layout = QtWidgets.QVBoxLayout()
        scale_box = QtWidgets.QGroupBox('Scale over:')
        scale_layout = QtWidgets.QVBoxLayout()
        
        
        self.setLayout(button_layout)
        
        #right hand button group
        self.choose_vertex_button = QtWidgets.QPushButton('Vertex')
        self.choose_vertex_button.setEnabled(False)
        self.choose_vertex_button.setCheckable(True)
        self.choose_vertex_button.setToolTip("Select vertex from viewport")
        self.first_centroid = QtWidgets.QPushButton('Centroid')
        self.first_centroid.setToolTip("Select centroid of first slice")
        self.first_centroid.setEnabled(False)
        
        self.trans_origin_button = QtWidgets.QPushButton('Update')
        self.trans_origin_button.setToolTip('Apply transformation')
        self.trans_origin_button.setEnabled(False)
        
        self.translate_x = QtWidgets.QDoubleSpinBox()
        self.translate_x.setMinimum(-1000)
        self.translate_x.setValue(0)
        self.translate_x.setMaximum(1000)
        self.translate_x.setPrefix('X ')
        self.translate_x.setSuffix(' mm')
        
        translate_y_label =QtWidgets.QLabel("Y")
        self.translate_y = QtWidgets.QDoubleSpinBox()
        self.translate_y.setMinimum(-1000)
        self.translate_y.setValue(0)
        self.translate_y.setMaximum(1000)
        self.translate_y.setPrefix('Y ')
        self.translate_y.setSuffix(' mm')
        
        translate_z_label =QtWidgets.QLabel("Z")
        self.translate_z = QtWidgets.QDoubleSpinBox()
        self.translate_z.setMinimum(-1000)
        self.translate_z.setValue(0)
        self.translate_z.setMaximum(1000)
        self.translate_z.setPrefix('Z ')
        self.translate_z.setSuffix(' mm')

        #make button group for STL origin rotation
        self.rotate_x = QtWidgets.QDoubleSpinBox()
        self.rotate_x.setSingleStep(15)
        self.rotate_x.setMinimum(-345)
        self.rotate_x.setValue(0)
        self.rotate_x.setMaximum(345)
        self.rotate_x.setPrefix('X ')
        self.rotate_x.setSuffix(' °')
        
        self.rotate_y = QtWidgets.QDoubleSpinBox()
        self.rotate_y.setSingleStep(15)
        self.rotate_y.setMinimum(-345)
        self.rotate_y.setValue(0)
        self.rotate_y.setMaximum(345)
        self.rotate_y.setPrefix('Y ')
        self.rotate_y.setSuffix(' °')
        
        self.rotate_z = QtWidgets.QDoubleSpinBox()
        self.rotate_z.setSingleStep(15)
        self.rotate_z.setMinimum(-345)
        self.rotate_z.setValue(0)
        self.rotate_z.setMaximum(345)
        self.rotate_z.setPrefix('Z ')
        self.rotate_z.setSuffix(' °')

        #scaling
        self.scale_x = QtWidgets.QDoubleSpinBox()
        self.scale_x.setSingleStep(1)
        self.scale_x.setMinimum(0.0001)
        self.scale_x.setValue(1)
        self.scale_x.setMaximum(10000)
        self.scale_x.setPrefix('X ')
        self.scale_x.setSuffix(' ×')
        
        self.scale_y = QtWidgets.QDoubleSpinBox()
        self.scale_y.setSingleStep(1)
        self.scale_y.setMinimum(0.0001)
        self.scale_y.setValue(1)
        self.scale_y.setMaximum(10000)
        self.scale_y.setPrefix('Y ')
        self.scale_y.setSuffix(' ×')
        
        self.scale_z = QtWidgets.QDoubleSpinBox()
        self.scale_z.setSingleStep(1)
        self.scale_z.setMinimum(0.0001)
        self.scale_z.setValue(1)
        self.scale_z.setMaximum(10000)
        self.scale_z.setPrefix('Z ')
        self.scale_z.setSuffix(' ×')
        
        
        self.scale_uniform_cb = QtWidgets.QCheckBox('Uniform scaling')

        #transform origin button layout
        translate_layout.addWidget(self.translate_x)
        translate_layout.addWidget(self.translate_y)
        translate_layout.addWidget(self.translate_z)
        
        rotate_layout.addWidget(self.rotate_x)
        rotate_layout.addWidget(self.rotate_y)
        rotate_layout.addWidget(self.rotate_z)
        
        scale_layout.addWidget(self.scale_x)
        scale_layout.addWidget(self.scale_y)
        scale_layout.addWidget(self.scale_z)
        
        translate_box.setLayout(translate_layout)
        rotate_box.setLayout(rotate_layout)
        scale_box.setLayout(scale_layout)
        if cond == 'translate':
            vl.addWidget(self.choose_vertex_button)
            vl.addWidget(self.first_centroid)
            hl.addWidget(translate_box)
        vl.addWidget(self.trans_origin_button)
        if cond == 'rotate':
            hl.addWidget(rotate_box)
        if cond == 'scale':
            vl.addWidget(self.scale_uniform_cb)
            hl.addWidget(scale_box)
        
        button_layout.addLayout(vl)
        button_layout.addLayout(hl)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    layout = make_transformation_button_layout(window)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())