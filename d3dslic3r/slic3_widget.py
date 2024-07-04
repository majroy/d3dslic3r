#!/usr/bin/env python
'''
D3D it with Python
-------------------------------------------------------------------------------
0.1 - Inital release
'''
__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2024-"

import os, sys
import numpy as np
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtGui, QtWidgets, QtCore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import rc
from matplotlib.patches import Polygon
from pkg_resources import Requirement, resource_filename

from d3dslic3r.d3dslic3r_common import *
from d3dslic3r.export_widget import export_widget

def launch(*args, **kwargs):
    '''
    Start Qt/VTK interaction if started independently
    '''
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    app.processEvents()
    
    window = interactor(None) #otherwise specify parent widget
    window.show()
    
    ret = app.exec_()
    
    if sys.stdin.isatty() and not hasattr(sys, 'ps1'):
        sys.exit(ret)
    else:
        return window

class main_window(object):
    """
    Generic object containing all UI
    """
    
    def setup(self, MainWindow):
        '''
        Creates Qt interactor
        '''
        
        #if called as a script, then treat as a mainwindow, otherwise treat as a generic widget
        if hasattr(MainWindow,'setCentralWidget'):
            MainWindow.setCentralWidget(self.centralWidget)
        else:
            self.centralWidget=MainWindow
        MainWindow.setWindowTitle("slic3 widget v%s" %__version__)
        
        #create new layout to hold both VTK and Qt interactors
        mainlayout=QtWidgets.QHBoxLayout(self.centralWidget)

        #create VTK widget
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        
        #create Qt layout to contain interactions
        io_layout = QtWidgets.QGridLayout()
        
        #create VTK widget
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(100)
        self.vtkWidget.setSizePolicy(sizePolicy)
        
        #set fonts
        head_font=QtGui.QFont("Helvetica [Cronyx]",weight=QtGui.QFont.Bold)
        io_font = QtGui.QFont("Helvetica")
        
        #make display layout
        io_box = QtWidgets.QGroupBox('I/O')
        #buttons
        self.load_button = QtWidgets.QPushButton('Load')
        self.load_label = QtWidgets.QLabel("Nothing loaded.")
        self.load_label.setWordWrap(True)
        self.load_label.setFont(io_font)
        self.load_label.setToolTip('Load STL file for slicing')
        #make combo box for slices
        self.slice_num_cb = QtWidgets.QComboBox()
        self.slice_num_cb.setToolTip('Change slice number highlighted')
        self.slice_num_cb.setEnabled(False)
        self.export_slice=QtWidgets.QPushButton("Export")
        self.export_slice.setToolTip('Export indicated slice number')
        self.export_slice.setCheckable(True)
        self.export_slice.setChecked(False)
        self.export_slice.setEnabled(False)
        
        io_layout.addWidget(self.load_button,0,0,1,1)
        io_layout.addWidget(self.slice_num_cb,0,1,1,1)
        io_layout.addWidget(self.export_slice,0,2,1,1)
        io_layout.addWidget(self.load_label,1,0,1,3)
        
        #make slice layout
        self.slice_box = QtWidgets.QGroupBox('Slice')
        slice_layout = QtWidgets.QGridLayout()
        self.spacing_rb=QtWidgets.QRadioButton("Spacing")
        self.quantity_rb=QtWidgets.QRadioButton("Quantity")
        self.spacing_rb.setChecked(True)
        self.slice_rb_group = QtWidgets.QButtonGroup()
        self.slice_rb_group.addButton(self.spacing_rb)
        self.slice_rb_group.addButton(self.quantity_rb)
        self.slice_rb_group.setExclusive(True)
        self.by_height_sb = QtWidgets.QDoubleSpinBox()
        self.by_height_sb.setSuffix(' mm')
        self.by_height_sb.setToolTip('Average height of each slice')
        self.by_height_sb.setMinimum(0.001)
        self.by_height_sb.setMaximum(1000)
        self.by_height_sb.setDecimals(3)
        self.by_height_sb.setValue(4)
        self.by_num_sb = QtWidgets.QSpinBox()
        self.by_num_sb.setPrefix('N = ')
        self.by_num_sb.setMinimum(4)
        self.by_num_sb.setMaximum(10000)
        self.by_num_sb.setValue(20)
        self.by_num_sb.setToolTip('Specify number of slices')
        self.agglom_param_sb = QtWidgets.QDoubleSpinBox()
        self.agglom_param_sb.setPrefix('Threshold = ')
        self.agglom_param_sb.setMinimum(0.001)
        self.agglom_param_sb.setMaximum(1000)
        self.agglom_param_sb.setDecimals(1)
        self.agglom_param_sb.setValue(5)
        self.agglom_param_sb.setToolTip('Threshold for sub-slicing')
        self.update_slice_button = QtWidgets.QPushButton('Slice')
        self.update_slice_button.setToolTip('Slice with given paramters')

        #populate slice box
        slice_layout.addWidget(self.spacing_rb, 1, 0, 1, 1)
        slice_layout.addWidget(self.quantity_rb, 1, 1, 1, 1)
        slice_layout.addWidget(self.by_height_sb,2,0,1,1)
        slice_layout.addWidget(self.by_num_sb,2,1,1,1)
        slice_layout.addWidget(self.agglom_param_sb,3,0,1,1)
        slice_layout.addWidget(self.update_slice_button,3,1,1,1)
        
        self.slice_box.setEnabled(False)
        
        
        #make pathing box
        self.path_box = QtWidgets.QGroupBox('Pathing')
        path_layout = QtWidgets.QVBoxLayout()
        
        #make path_gen layout
        path_gen_layout = QtWidgets.QGridLayout()
        self.path_all_cb = QtWidgets.QCheckBox('Path all')
        self.path_all_cb.setEnabled(False)
        self.path_all_cb.setToolTip('Apply to all slices')
        self.path_outline_cb = QtWidgets.QCheckBox('Path outline')
        self.path_outline_cb.setToolTip('Include outline in pathing')
        self.rotate_z_path_sb = QtWidgets.QDoubleSpinBox()
        self.rotate_z_path_sb.setToolTip('Rotational offset for pathing of slice. Positive is clockwise.')
        self.rotate_z_path_sb.setValue(0)
        self.rotate_z_path_sb.setMaximum(180)
        self.rotate_z_path_sb.setMinimum(-180)
        self.rotate_z_path_sb.setPrefix("\u03b8 = ")
        self.rotate_z_path_sb.setSuffix("\u00b0")
        self.by_width_sb = QtWidgets.QDoubleSpinBox()
        self.by_width_sb.setSuffix(' mm')
        self.by_width_sb.setToolTip('Average width of each path/bead')
        self.by_width_sb.setMinimum(0.001)
        self.by_width_sb.setMaximum(1000)
        self.by_width_sb.setDecimals(3)
        self.by_width_sb.setValue(4)
        self.num_paths_label = QtWidgets.QLabel("No paths.")
        self.num_paths_label.setWordWrap(True)
        self.num_paths_label.setFont(io_font)
        self.num_paths_label.setToolTip('Total number of paths/beads resolved')
        self.bead_offset_sb = QtWidgets.QDoubleSpinBox()
        self.bead_offset_sb.setMinimum(30)
        self.bead_offset_sb.setMaximum(80)
        self.bead_offset_sb.setDecimals(3)
        self.bead_offset_sb.setValue(50)
        self.bead_offset_sb.setSuffix('%')
        self.activate_path_pb = QtWidgets.QPushButton('Update')
        self.activate_path_pb.setToolTip('Segment into specified paths')
        
        #populate pathing layout
        path_gen_layout.addWidget(self.path_all_cb,0,0,1,1)
        path_gen_layout.addWidget(self.path_outline_cb,0,1,1,1)
        path_gen_layout.addWidget(self.rotate_z_path_sb,0,2,1,1)
        path_gen_layout.addWidget(self.by_width_sb,0,3,1,1)
        path_gen_layout.addWidget(self.bead_offset_sb,0,4,1,1)
        path_gen_layout.addWidget(self.num_paths_label,1,0,1,2)
        path_gen_layout.addWidget(self.activate_path_pb,1,4,1,1)
        
        self.path_box.setEnabled(False)
        
        #make outline modification box
        outline_mod_box = QtWidgets.QGroupBox('Outline modification')
        outline_mod_layout = QtWidgets.QGridLayout()
        self.alpha_pb = QtWidgets.QPushButton("Apply")
        self.alpha_pb.setToolTip('Apply alpha shape smoothing to active profile.')
        self.alpha_undo_pb = QtWidgets.QPushButton("Revert")
        self.alpha_undo_pb.setToolTip('Revert to polygon winding')
        self.alpha_param_sb = QtWidgets.QDoubleSpinBox()
        self.alpha_param_sb.setPrefix('Alpha = ')
        self.alpha_param_sb.setMinimum(0.001)
        self.alpha_param_sb.setMaximum(1000)
        self.alpha_param_sb.setDecimals(3)
        self.alpha_param_sb.setValue(1)
        self.alpha_param_sb.setToolTip('Alpha shape semiperimeter threshold for concave outlines')
        
        
        #create figure canvas
        #initialize plot
        self.figure = plt.figure(figsize=(4,4))
        ax = plt.gca()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        img = plt.imread(resource_filename("d3dslic3r","meta/noslice.png"))
        plt.text(0.5, 0.18, "No slice", ha='center', style='italic', fontweight = 'bold', color='darkgray', alpha=0.5, size= 18)
        plt.imshow(img, zorder=1, extent=[0.25, 0.75, 0.25, 0.75], alpha=0.5)
        plt.axis('off')
        #changes the background of the plot, otherwise white
        # self.figure.patch.set_facecolor((242/255,242/255,242/255))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas)
        self.canvas.setSizePolicy(sizePolicy)
        self.canvas.setMinimumSize(QtCore.QSize(500, 375)) #figsize(8,6)

        #add everything to the outline mod layout
        outline_mod_layout.addWidget(self.alpha_param_sb,0,0,1,1)
        outline_mod_layout.addWidget(self.alpha_undo_pb,0,1,1,1)
        outline_mod_layout.addWidget(self.alpha_pb,0,2,1,1)
        
        #add layouts to boxes & main widgets to main layouts
        io_box.setLayout(io_layout)
        self.slice_box.setLayout(slice_layout)
        self.path_box.setLayout(path_layout)
        outline_mod_box.setLayout(outline_mod_layout)
        path_layout.addLayout(path_gen_layout)
        path_layout.addWidget(self.canvas)
        path_layout.addWidget(toolbar)
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        sep.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
        sep.setLineWidth(1)
        path_layout.addWidget(outline_mod_box)
        path_layout.addWidget(sep)
        
        lvlayout=QtWidgets.QVBoxLayout()
        lvlayout.addWidget(io_box)
        lvlayout.addWidget(self.slice_box)
        lvlayout.addWidget(self.path_box)

        lvlayout.addStretch(1)
        
        mainlayout.addWidget(self.vtkWidget)
        mainlayout.addStretch(1)
        mainlayout.addLayout(lvlayout)

        def initialize(self):
            self.vtkWidget.start()
            
class interactor(QtWidgets.QWidget):
    '''
    Inherits most properties from Qwidget, but primes the VTK window, and ties functions and methods to interactors defined in main_window
    '''
    def __init__(self,parent):
        super(interactor, self).__init__(parent)
        self.ui = main_window()
        self.ui.setup(self)
        self.ren = vtk.vtkRenderer()
        colors = vtk.vtkNamedColors()
        self.ren.SetBackground(colors.GetColor3d("white"))

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        style=vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)
        self.iren.AddObserver("KeyPressEvent", self.keypress)
        # self.iren.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.ren.GetActiveCamera().ParallelProjectionOn()
        self.ui.vtkWidget.Initialize()
        
        make_logo(self.ren)
        
        self.slice_data = []
        
        self.ui.load_button.clicked.connect(self.load_stl)
        self.ui.update_slice_button.clicked.connect(self.do_slice)
        self.ui.slice_num_cb.currentIndexChanged.connect(self.draw_slice)
        self.ui.alpha_pb.clicked.connect(self.get_alpha_shape)
        self.ui.alpha_undo_pb.clicked.connect(self.undo_alpha_shape)
        self.ui.activate_path_pb.clicked.connect(self.make_paths)
        self.ui.export_slice.clicked.connect(self.export)
    
    def keypress(self, obj, event):
        '''
        VTK interactor-specific listener for keypresses
        '''
        key = obj.GetKeySym()
        
        if key =="1":
            xyview(self.ren)
        elif key =="2":
            yzview(self.ren)
        elif key =="3":
            xzview(self.ren)
        elif key == "Up":
            self.change_entry(1)
        elif key == "Down":
            self.change_entry(-1)
    
        self.ui.vtkWidget.update()
        
    def change_entry(self,val):
        """
        Handles logic for changing entries in the slice combobox based on keypress. Combobox changes call draw_slice
        """
        if self.ui.slice_num_cb.count() == 0:
            return
        
        if val < 0:
            if self.ui.slice_num_cb.currentIndex() == 0:
                self.ui.slice_num_cb.setCurrentIndex(self.ui.slice_num_cb.count()-1)
            else:
                self.ui.slice_num_cb.setCurrentIndex(self.ui.slice_num_cb.currentIndex()-1)
        else:
            if self.ui.slice_num_cb.currentIndex() == self.ui.slice_num_cb.count()-1:
                self.ui.slice_num_cb.setCurrentIndex(1)
            else:
                self.ui.slice_num_cb.setCurrentIndex(self.ui.slice_num_cb.currentIndex()+1)

        
    
    def load_stl(self):
        """
        Opens file dialog to get stl file, returns polydata and actor to self. Clears polydata and object_actor from attributes on successful load
        """
        
        
        filep = get_file('*.stl')
        
        if filep is None:
            return
        if not(os.path.isfile(filep)):
            print('Data file invalid.')
            return
        self.polydata = get_polydata_from_stl(filep)
        self.ui.load_label.setText(filep)
        self.redraw_stl()


    def redraw_stl(self):
        """
        Redraws the STL object: removes it if it exists then generates a new actor from the current polydata
        """
        if hasattr(self,'object_actor'):
            self.ren.RemoveActor(self.object_actor)
            self.ren.RemoveActor(self.origin_actor)
        if hasattr(self,'current_outline_actor'):
            self.ren.RemoveActor(self.current_outline_actor)
            self.ren.RemoveActor(self.outline_caption_actor)
            self.ui.figure.clear()
        if hasattr(self,'slice_actors'):
            self.ren.RemoveActor(self.slice_actors)
        else:
            self.ren.RemoveAllViewProps()
            self.ui.slice_box.setEnabled(True)
        
            
        
        self.object_actor = actor_from_polydata(self.polydata)
        self.ren.AddActor(self.object_actor)
        
        # make/update an origin actor
        self.origin_actor = vtk.vtkAxesActor()
        # change scale of origin on basis of size of stl_actor, only if this is the first entry
        origin_scale = np.max(self.object_actor.GetBounds())/16
        self.origin_actor.SetTotalLength(origin_scale,origin_scale,origin_scale)
        self.origin_actor.SetNormalizedShaftLength(1,1,1)
        self.origin_actor.SetNormalizedTipLength(0.2,0.2,0.2)
        
        self.origin_actor.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        self.origin_actor.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        self.origin_actor.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        self.ren.AddActor(self.origin_actor)
        
        
        self.ren.ResetCamera()
        self.ui.vtkWidget.setFocus()
        self.ui.vtkWidget.update()
        

    def do_slice(self):
        """
        Performs slicing operation based on ui values
        """
        
        if hasattr(self,'slice_actors'):
            self.ren.RemoveActor(self.slice_actors)
            self.ui.slice_num_cb.clear()
            del self.slice_data
        
        
        if self.ui.quantity_rb.isChecked():
            self.outlines, self.slice_actors = get_slice_data(self.polydata,self.ui.by_num_sb.value())
        else:
            self.outlines, self.slice_actors = get_slice_data(self.polydata,self.ui.by_height_sb.value(), False)
        
        self.outlines = get_sub_slice_data(self.outlines,self.ui.agglom_param_sb.value())
        
        self.slice_data = [None] * len(self.outlines)
        
        for i in range(len(self.outlines)):
            self.ui.slice_num_cb.insertItem(i,'Slice %d'%i)
        self.ui.slice_num_cb.setEnabled(True)
        
        self.ui.path_box.setEnabled(True)
        
        self.ren.AddActor(self.slice_actors)
        self.ui.vtkWidget.update()

    def draw_slice(self):
        
        #get active outline
        entry = self.ui.slice_num_cb.currentIndex()
        
        #make sure inadvertent changes to combobox don't operate
        if not self.slice_data:
            return
        
        if hasattr(self,'current_outline_actor'):
            self.ren.RemoveActor(self.current_outline_actor)
            self.ren.RemoveActor(self.outline_caption_actor)
            self.ui.figure.clear()
        
        #get active outline
        entry = self.ui.slice_num_cb.currentIndex()
        
        #check if there is itemData for the current entry if possible
        if self.slice_data[entry] is None:
            #order the points with polygon winding and add to a slice_obj
            self.slice_data[entry] = slice_obj(sort_ccw(self.outlines[entry]))
        
        outline = self.slice_data[entry].outline
        
        self.current_outline_actor = gen_outline_actor(outline, (1,0,0), 4)
        self.outline_caption_actor = gen_caption_actor('%s'%entry, self.current_outline_actor, (1,0,0))
        
        self.ren.AddActor(self.current_outline_actor)
        self.ren.AddActor(self.outline_caption_actor)
        
        #add to combobox item data
        
        self.ui.vtkWidget.update()
        
        ax = self.ui.figure.add_subplot(111)
        ax.plot(outline[:,0], outline[:,1], 'k-')
        ax.set_ylabel("y (mm)")
        ax.set_xlabel("x (mm)")
        ax.grid(visible=True, which='major', color='#666666', linestyle='-', alpha=0.1)
        ax.minorticks_on()
        ax.grid(visible=True, which='minor', color='#666666', linestyle='-', alpha=0.2)
        ax.set_aspect('equal', adjustable='datalim')
        
        ax.text(0.95, 0.01, 'z = %0.3f'%np.mean(outline[:,2]),
        verticalalignment='bottom', horizontalalignment='right',
        transform=ax.transAxes,
        color='green', fontsize=12)
        
        self.ui.canvas.draw()
        
        #call draw_paths in case there are paths available
        self.draw_paths()
        
    def get_alpha_shape(self):
        """
        Gets parameters from GUI, runs sort_alpha and returns the result.
        """
        
        entry = self.ui.slice_num_cb.currentIndex()
        
        #check if alpha shape processing is on, if it is then call get_alpha_shape on this outline
        alpha_outline = sort_alpha(self.slice_data[entry].outline, self.ui.alpha_param_sb.value())
        if alpha_outline is None:
            print('No alpha')
            pass
        else:
            self.slice_data[entry] = slice_obj(alpha_outline)
        
        self.draw_slice()
    
    def undo_alpha_shape(self):
        """
        Returns profile to raw, sort_ccw form
        """
        
        entry = self.ui.slice_num_cb.currentIndex()
        self.slice_data[entry] = slice_obj(sort_ccw(self.outlines[entry]))
        
        self.draw_slice()
        
    def make_paths(self):
        """
        Updates the slice_obj for each slice to include a 'paths' entry. Calls draw_paths to draw them.
        """
        
        local_path_collection = []
        
        if not self.ui.path_all_cb.isChecked():
        
            entry = self.ui.slice_num_cb.currentIndex()
            outline = self.slice_data[entry].outline
            theta = self.ui.rotate_z_path_sb.value()
            offset = self.ui.bead_offset_sb.value()/100
            if self.ui.path_outline_cb.isChecked():
                interior = offset_poly(outline,-self.ui.by_width_sb.value())
                midline = offset_poly(outline,-self.ui.by_width_sb.value()*0.5)
                intersections, param = get_intersections(midline,theta,self.ui.by_width_sb.value(),offset)
                local_path_collection.append(midline)
            else:
                intersections, param = get_intersections(outline,theta,self.ui.by_width_sb.value(),offset)

            self.ui.bead_offset_sb.setValue(param*100)
            self.ui.num_paths_label.setText('N = %i'%(len(intersections)-1))
            
        #pack up/pair intersections for line paths
        for i in np.arange(len(intersections)-1)[::2]:
            local_path_collection.append(np.array([intersections[i,:], intersections[i+1,:]]))
            
        
        self.slice_data[entry].paths = local_path_collection #list of paths
        self.ui.export_slice.setEnabled(True)
        self.draw_slice() #to clear any existing intersections

    def draw_paths(self):

        #get active outline
        entry = self.ui.slice_num_cb.currentIndex()
        
        #make sure there's something to plot
        if not self.slice_data[entry].paths:
            return
        
        ax = self.ui.figure.gca()
        for path in self.slice_data[entry].paths:
            ax.plot(path[:,0], path[:,1], '--', color = 'k')
    
        self.ui.canvas.draw()

    def export(self):
        '''
        Create pop-up which shows the user what's going to happen
        '''
        ew = export_widget(self, self.slice_data)
        ew.exec_()

        

class slice_obj:
    def __init__(self, outline):
        self.outline = outline
        self.alpha = None
        self.paths = None

if __name__ == "__main__":
    launch()