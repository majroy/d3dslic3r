#!/usr/bin/env python
'''
Constructor functions/methods for outlining widgets.
'''

import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


def make_outline_options_button(parent_window):
    outline_all_drop_button = QtWidgets.QToolButton()
    outline_all_drop_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    outline_all_drop_button.setMenu(QtWidgets.QMenu(outline_all_drop_button))
    outline_action = QtWidgets.QWidgetAction(outline_all_drop_button)
    outline_action.setText('All')
    outline_action.setCheckable(True)
    outline_all_drop_button.setDefaultAction(outline_action) #need to set on the action for text instead of labels
    parent_window.outline_all_widget = outline_all_options_box(parent_window)
    outline_action.setDefaultWidget(parent_window.outline_all_widget)
    outline_all_drop_button.menu().addAction(outline_action)
    outline_all_drop_button.setToolTip('Operate on all slices or all outlines on slice')
    return outline_all_drop_button
    
def make_path_outline_button(parent_window):
    path_outline_button = QtWidgets.QToolButton()
    path_outline_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    path_outline_button.setMenu(QtWidgets.QMenu(path_outline_button))
    po_action = QtWidgets.QWidgetAction(path_outline_button)
    po_action.setText('Path outline')
    po_action.setCheckable(True)
    path_outline_button.setDefaultAction(po_action) #need to set on the action for text instead of labels
    parent_window.po_widget = path_outline_options_box(parent_window)
    po_action.setDefaultWidget(parent_window.po_widget)
    path_outline_button.menu().addAction(po_action)
    path_outline_button.setToolTip('Create paths on outline')
    return path_outline_button

def make_thin_wall_button(parent_window):
    thin_wall_drop_button = QtWidgets.QToolButton()
    thin_wall_drop_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    thin_wall_drop_button.setMenu(QtWidgets.QMenu(thin_wall_drop_button))
    tw_action = QtWidgets.QWidgetAction(thin_wall_drop_button)
    tw_action.setText('Path central')
    tw_action.setCheckable(True)
    thin_wall_drop_button.setDefaultAction(tw_action) #need to set on the action for text instead of labels
    parent_window.tw_widget = thin_wall_options_box(parent_window)
    tw_action.setDefaultWidget(parent_window.tw_widget)
    thin_wall_drop_button.menu().addAction(tw_action)
    thin_wall_drop_button.setToolTip('Path the central line of enclosed and paired outlines')
    return thin_wall_drop_button

class outline_all_options_box(QtWidgets.QWidget):
    def __init__(self, parent_window, *args, **kwargs):
        '''
        Allows setting the options for processing thin-walled features
        '''
        
        super().__init__(*args, **kwargs)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        
        button_group = QtWidgets.QButtonGroup(self)
        button_group.setExclusive(True)
        self.current_slice_cb = QtWidgets.QCheckBox('Current slice')
        self.current_slice_cb.setToolTip('Apply to all outlines on the current slice')
        self.current_slice_cb.setChecked(True)
        button_group.addButton(self.current_slice_cb)
        self.all_slices_cb = QtWidgets.QCheckBox('All slices')
        self.all_slices_cb.setToolTip('Apply to all outlines on all slices')
        button_group.addButton(self.all_slices_cb)

        this_layout = QtWidgets.QVBoxLayout()
        self.setLayout(this_layout)
        this_layout.addWidget(self.current_slice_cb)
        this_layout.addWidget(self.all_slices_cb)

class path_outline_options_box(QtWidgets.QWidget):
    def __init__(self, parent_window, *args, **kwargs):
        '''
        Allows setting the options for processing thin-walled features
        '''
        
        super().__init__(*args, **kwargs)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        
        self.outline_outer_offset_sb = QtWidgets.QDoubleSpinBox()
        self.outline_outer_offset_sb.setSingleStep(1)
        self.outline_outer_offset_sb.setMinimum(0.0)
        self.outline_outer_offset_sb.setDecimals(3)
        self.outline_outer_offset_sb.setValue(0)
        self.outline_outer_offset_sb.setToolTip('Value to offset path of outer outlines')
        self.outline_outer_offset_sb.setMaximum(10000000)
        self.outline_outer_offset_sb.setPrefix('Outer offset =  ')

        self.outline_inner_offset_sb = QtWidgets.QDoubleSpinBox()
        self.outline_inner_offset_sb.setSingleStep(1)
        self.outline_inner_offset_sb.setMinimum(0.0)
        self.outline_inner_offset_sb.setDecimals(3)
        self.outline_inner_offset_sb.setValue(0)
        self.outline_inner_offset_sb.setToolTip('Value to offset path of inner outlines')
        self.outline_inner_offset_sb.setMaximum(10000000)
        self.outline_inner_offset_sb.setPrefix('Inner offset =  ')

        this_layout = QtWidgets.QVBoxLayout()
        self.setLayout(this_layout)
        this_layout.addWidget(self.outline_outer_offset_sb)
        this_layout.addWidget(self.outline_inner_offset_sb)

class thin_wall_options_box(QtWidgets.QWidget):
    def __init__(self, parent_window, *args, **kwargs):
        '''
        Allows setting the options for processing thin-walled features
        '''
        
        super().__init__(*args, **kwargs)
        
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        
        self.step_size = QtWidgets.QDoubleSpinBox()
        self.step_size.setSingleStep(1)
        self.step_size.setMinimum(0.1)
        self.step_size.setDecimals(2)
        self.step_size.setValue(30.01)
        self.step_size.setMaximum(180)
        self.step_size.setToolTip('Step between 0 & 180°')
        self.step_size.setPrefix('\u03b1 ')
        self.step_size.setSuffix(' °')

        self.hatch_interval = QtWidgets.QDoubleSpinBox()
        self.hatch_interval.setSingleStep(1)
        self.hatch_interval.setMinimum(0.1)
        self.hatch_interval.setDecimals(3)
        self.hatch_interval.setValue(15)
        self.hatch_interval.setToolTip('Hatching interval variable: the bounding box limits divided by this value provide the spacing between hatch lines.')
        self.hatch_interval.setMaximum(10000000)
        self.hatch_interval.setPrefix('Hatch  ')

        this_layout = QtWidgets.QVBoxLayout()
        self.setLayout(this_layout)
        this_layout.addWidget(self.step_size)
        this_layout.addWidget(self.hatch_interval)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    layout.addWidget(make_outline_options_button(window))
    layout.addWidget(make_path_outline_button(window))
    layout.addWidget(make_thin_wall_button(window))
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())