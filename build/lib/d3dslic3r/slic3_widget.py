#!/usr/bin/env python
'''
D3D it with Python
-------------------------------------------------------------------------------
0.1 - Inital release
'''
__author__ = "M.J. Roy"
__version__ = "0.2"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2024-"

import os, sys
import numpy as np
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import vtk_to_numpy as v2n
from PyQt5 import QtGui, QtWidgets, QtCore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import rc
import importlib.resources

from d3dslic3r.common import *
from d3dslic3r.gui_common import *
from d3dslic3r.thin_wall import *
from d3dslic3r.export_widget import export_widget
from d3dslic3r.transform_widget import make_transformation_button_layout, get_trans_from_euler_angles
from d3dslic3r.outline_widgets import make_outline_options_button, make_path_outline_button, make_thin_wall_button

class standalone_app(QtWidgets.QMainWindow):
    
    def __init__(self, parent=None):
        
        super(standalone_app, self).__init__(parent)
        self.main_window = interactor(self)
        self.setCentralWidget(self.main_window)
        self.setWindowTitle("slic3 widget v%s" %__version__)
        screen = QtWidgets.QApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.setMinimumSize(QtCore.QSize(int(2*rect.width()/3), int(2*rect.height()/3)))

class main_window(QtWidgets.QWidget):
    """
    Generic object containing all UI
    """
        
    def setup(self, parent):
        '''
        Creates Qt interactor
        '''
        
        #create new layout to hold both VTK and Qt interactors
        mainlayout=QtWidgets.QHBoxLayout(parent)

        #create VTK widget
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(50)
        sizePolicy.setVerticalStretch(50)
        self.vtkWidget.setSizePolicy(sizePolicy)
        
        #set fonts
        head_font=QtGui.QFont("Helvetica [Cronyx]",weight=QtGui.QFont.Bold)
        io_font = QtGui.QFont("Helvetica")
        
        #make io box
        io_layout = QtWidgets.QGridLayout()
        io_box = collapsible_box("I/O")
        self.load_button = QtWidgets.QPushButton('Load')
        self.load_button.setToolTip('Load STL file for slicing')
        self.work_dir_button = QtWidgets.QPushButton('...')
        self.work_dir_button.setToolTip('Set working directory')
        self.export_slice=QtWidgets.QPushButton("Export")
        self.export_slice.setToolTip('Export paths')
        self.export_slice.setCheckable(True)
        self.export_slice.setChecked(False)
        self.export_slice.setEnabled(False)
        
        io_layout.addWidget(self.load_button,0,0,1,1)
        io_layout.addWidget(self.work_dir_button,0,1,1,1)
        io_layout.addWidget(self.export_slice,0,2,1,1)
        
        #Geometry manipulation layout
        geo_button_layout = QtWidgets.QGridLayout()
        self.geo_box = collapsible_box("Geometry manipulation")
        self.op_slider_label = QtWidgets.QLabel("Opacity:")
        self.op_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.op_slider.setRange(0,100)
        self.op_slider.setSliderPosition(100)
        
        self.export_stl_button = QtWidgets.QPushButton('Export')
        self.export_stl_button.setToolTip('Export current model geometry as new STL')
        
        geo_button_layout.addWidget(self.op_slider_label,0,0,1,1)
        geo_button_layout.addWidget(self.op_slider,0,1,1,1)
        geo_button_layout.addLayout(make_transformation_button_layout(self),0,2,1,2)
        geo_button_layout.addWidget(self.export_stl_button,0,4,1,1)
        geo_button_layout.setColumnStretch(0, 0)
        geo_button_layout.setColumnStretch(1, 1)
        
        self.geo_box.setEnabled(False)
        
        #make slice layout
        slice_layout = QtWidgets.QGridLayout()
        self.slice_box = collapsible_box('Slice')
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
        self.by_num_sb.setMinimum(1)
        self.by_num_sb.setMaximum(10000)
        self.by_num_sb.setValue(20)
        self.by_num_sb.setToolTip('Specify number of slices')
        #make combo box for slices
        self.slice_num_cb = QtWidgets.QComboBox()
        self.slice_num_cb.setToolTip('Change slice number highlighted')
        self.slice_num_cb.setEnabled(False)
        self.update_slice_button = QtWidgets.QPushButton('Slice')
        self.update_slice_button.setToolTip('Slice with given parameters')

        #populate slice box
        slice_layout.addWidget(self.spacing_rb, 0, 0, 1, 1)
        slice_layout.addWidget(self.quantity_rb, 0, 1, 1, 1)
        slice_layout.addWidget(self.by_height_sb,1,0,1,1)
        slice_layout.addWidget(self.by_num_sb,1,1,1,1)
        slice_layout.addWidget(self.update_slice_button,0,2,1,1)
        slice_layout.addWidget(self.slice_num_cb,1,2,1,1)
        self.slice_box.setEnabled(False)

        #make path_gen layout
        outline_layout = QtWidgets.QHBoxLayout()
        outline_gen_layout = QtWidgets.QGridLayout()
        self.outline_box = collapsible_box('Outline')
        
        self.outline_all_button = make_outline_options_button(self)
        self.path_outline_cb = make_path_outline_button(self)
        self.thin_wall_button = make_thin_wall_button(self)
        
        #make combo box for outlines
        self.outline_num_cb = QtWidgets.QComboBox()
        self.outline_num_cb.setToolTip('Change outline number active')
        self.outline_num_cb.setEnabled(False)
        #make combobox for paths
        self.path_num_cb = QtWidgets.QComboBox()
        self.path_num_cb.setToolTip('Change path number highlighted')
        self.path_num_cb.setEnabled(False)
        
        self.outline_update_pb = QtWidgets.QPushButton('Path')
        self.outline_update_pb.setToolTip('Generate/update outline paths')
        
        #populate outline layout
        outline_gen_layout.addWidget(self.outline_all_button,0,0,1,1)
        outline_gen_layout.addWidget(self.path_outline_cb,0,1,1,1)
        outline_gen_layout.addWidget(self.thin_wall_button,0,2,1,1)
        outline_gen_layout.addWidget(self.outline_update_pb,0,3,1,2)
        outline_gen_layout.addWidget(self.outline_num_cb,1,3,1,1)
        outline_gen_layout.addWidget(self.path_num_cb,1,4,1,1)
        
        outline_layout.addStretch()
        outline_layout.addLayout(outline_gen_layout)
        
        self.outline_box.setEnabled(False)

        #create figure canvas
        self.figure = plt.figure(figsize=(4,4), layout='constrained')
        plt.rc('font', size = 9)
        ax = self.figure.gca()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        img = plt.imread(importlib.resources.files('d3dslic3r') / 'meta/noslice.png')
        plt.text(0.5, 0.18, "No slice", ha='center', style='italic', fontweight = 'bold', color='darkgray', alpha=0.5, size= 18)
        plt.imshow(img, zorder=1, extent=[0.33, 0.66, 0.33, 0.66], alpha=0.5)
        plt.axis('off')
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas)
        self.canvas.setMinimumWidth(500)
        self.canvas.setMinimumHeight(500)
        
        #add layouts to boxes & main widgets to main layout
        lvlayout=QtWidgets.QVBoxLayout()
        lvlayout.addWidget(io_box)
        io_box.set_content_layout(io_layout)
        io_box.on_pressed() #to initialize dropped
        lvlayout.addWidget(self.geo_box)
        self.geo_box.set_content_layout(geo_button_layout)
        lvlayout.addWidget(self.slice_box)
        self.slice_box.set_content_layout(slice_layout)
        lvlayout.addWidget(self.outline_box)
        self.outline_box.set_content_layout(outline_layout)
        lvlayout.addWidget(self.canvas)
        
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        sep.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
        sep.setLineWidth(1)
        lvlayout.addWidget(toolbar)
        lvlayout.addStretch(1)
        lvlayout.addWidget(sep)

        mainlayout.addWidget(self.vtkWidget)
        
        mainlayout.addLayout(lvlayout)
        mainlayout.addStretch()
        

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
        self.ren.GetActiveCamera().ParallelProjectionOn()
        self.ui.vtkWidget.Initialize()
        

        
        
        make_logo(self.ren)
        
        self.picking = False
        self.slice_data = []
        
        self.ui.load_button.clicked.connect(self.load_stl)
        self.ui.work_dir_button.clicked.connect(self.set_work_dir)
        
        self.ui.op_slider.valueChanged[int].connect(self.change_opacity)
        self.ui.export_stl_button.clicked.connect(self.export_stl)
        self.ui.trans_widget.trans_origin_button.clicked.connect(self.apply_trans)
        self.ui.trans_reset_button.clicked.connect(self.reset_trans)
        self.ui.trans_widget.choose_vertex_button.clicked.connect(self.actuate_vertex_select)
        self.ui.trans_widget.first_centroid.clicked.connect(self.actuate_centroid_select)
        self.ui.rotation_widget.trans_origin_button.clicked.connect(self.apply_rotation)
        self.ui.scale_widget.trans_origin_button.clicked.connect(self.apply_scale)

        self.ui.update_slice_button.clicked.connect(self.do_slice)
        self.ui.slice_num_cb.currentIndexChanged.connect(self.draw_slices)
        self.ui.outline_num_cb.currentIndexChanged.connect(self.draw_outlines)
        self.ui.path_num_cb.currentIndexChanged.connect(self.draw_paths)
        #make sure that pathing of outlines are unique - can't be added to buttongroup
        self.ui.path_outline_cb.toggled.connect(lambda checked: self.ui.thin_wall_button.setChecked(False))
        self.ui.thin_wall_button.toggled.connect(lambda checked: self.ui.path_outline_cb.setChecked(False))
        
        self.ui.outline_update_pb.clicked.connect(self.path_outlines)
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
            self.change_cb(self.ui.slice_num_cb,1)
        elif key == "Down":
            self.change_cb(self.ui.slice_num_cb,-1)
        elif key == "Right":
            self.change_cb(self.ui.outline_num_cb,1)
        elif key == "Left":
            self.change_cb(self.ui.outline_num_cb,-1)
        elif key == "d":
            self.change_cb(self.ui.path_num_cb,1)
        elif key == "a":
            self.change_cb(self.ui.path_num_cb,-1)
    
        self.ui.vtkWidget.update()
    
    def change_cb(self,target,val):
        '''
        Handles logic for changing entries in the target combobox based on keypress.
        '''
        
        if target.count() == 0:
            return
        
        if val < 0:
            if target.currentIndex() == 0:
                target.setCurrentIndex(target.count()-1)
            else:
                target.setCurrentIndex(target.currentIndex()-1)
        else:
            if target.currentIndex() == target.count()-1:
                target.setCurrentIndex(0) #wraparound
            else:
                target.setCurrentIndex(target.currentIndex()+1)


    def set_work_dir(self):
        
        work_dir = get_dir()
        if work_dir is None:
            pass
        else:
            os.chdir(work_dir)
    
    def load_stl(self):
        '''
        Opens file dialog to get stl file, returns polydata and actor to self. Clears polydata and object_actor from attributes on successful load
        '''
        
        filep = get_file('*.stl')
        
        if filep is None:
            return
        if not(os.path.isfile(filep)):
            print('Data file invalid.')
            return
        self.polydata = get_polydata_from_stl(filep)

        self.trans = np.eye(4)
        
        self.ui.trans_widget.trans_origin_button.setEnabled(True)
        self.ui.rotation_widget.trans_origin_button.setEnabled(True)
        self.ui.scale_widget.trans_origin_button.setEnabled(True)
        self.ui.trans_reset_button.setEnabled(True)
        self.ui.trans_widget.choose_vertex_button.setEnabled(True)
        
        self.redraw_stl()

    def export_stl(self):
        '''
        Writes the current model geometry to a new STL file
        '''
        
        fileo = get_save_file('*.stl')
        if fileo is None:
            return
        writer = vtk.vtkSTLWriter()
        writer.SetFileTypeToBinary() #SetFileTypeToASCII() for text files
        writer.SetFileName(fileo)
        writer.SetInputData(self.polydata)
        writer.Write()

    def redraw_stl(self):
        '''
        Redraws the STL object: removes it if it exists then generates a new actor from the current polydata
        '''
        
        if hasattr(self,'object_actor'):
            self.ren.RemoveActor(self.object_actor)
            self.ren.RemoveActor(self.origin_actor)
        if hasattr(self,'current_outline_actor'):
            self.ren.RemoveActor(self.current_outline_actor)
            self.ren.RemoveActor(self.outline_caption_actor)
        if hasattr(self,'slice_actors'):
            self.ren.RemoveActor(self.slice_actors)
        else:
            self.ren.RemoveAllViewProps()
            self.ui.geo_box.setEnabled(True)
            self.ui.slice_box.setEnabled(True)
        
        self.ui.figure.clear()
        
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
        
        self.change_opacity(self.ui.op_slider.value())
        self.ren.ResetCamera()
        self.ui.vtkWidget.setFocus()
        self.ui.vtkWidget.update()

    def change_opacity(self,value):
        '''
        Change the opacity of any surface meshes
        '''
        self.ui.op_slider_label.setText('Opacity: %d%%'%value)
        if hasattr(self,'object_actor'):
            self.object_actor.GetProperty().SetOpacity(value/100)
        self.ui.vtkWidget.update()

    def reset_trans(self):
        '''
        Applies the inverse of the current transformation matrix to revert all transformations, resets inputs for movement
        '''

        T = np.linalg.inv(self.trans)
        self.apply_transformation(T)

    def apply_trans(self):
        '''
        Applies the appropriate translation to the existing model object(s)
        '''
        self.ui.translate_drop_button.setChecked(False)
        
        T = np.eye(4)
        T[0,-1] = self.ui.trans_widget.translate_x.value()
        T[1,-1] = self.ui.trans_widget.translate_y.value()
        T[2,-1] = self.ui.trans_widget.translate_z.value()
        self.apply_transformation(T)
        if self.picking:
            self.actuate_vertex_select()

    def apply_rotation(self):
        '''
        Applies a rotation matrix to the current object
        '''
        
        T = get_trans_from_euler_angles( \
        self.ui.rotation_widget.rotate_x.value(), \
        self.ui.rotation_widget.rotate_y.value(), \
        self.ui.rotation_widget.rotate_z.value())
        self.apply_transformation(T)

    def apply_scale(self):
        
        T = np.eye(4)
        
        if self.ui.scale_widget.scale_uniform_cb.isChecked():
            #Get maximum of entries
            sfactor = np.max([
            self.ui.scale_widget.scale_x.value(),
            self.ui.scale_widget.scale_y.value(),
            self.ui.scale_widget.scale_z.value()
            ])
            self.ui.scale_widget.scale_x.setValue(sfactor)
            self.ui.scale_widget.scale_y.setValue(sfactor)
            self.ui.scale_widget.scale_z.setValue(sfactor)
        
        T[0,0] = self.ui.scale_widget.scale_x.value()
        T[1,1] = self.ui.scale_widget.scale_y.value()
        T[2,2] = self.ui.scale_widget.scale_z.value()
        self.apply_transformation(T)


    def apply_transformation(self,T):
        '''
        Applies transformation matrix T to current STL entry
        '''
        
        #modify relevant aspects of the instance according to the transformation matrix
        np_pts = do_transform(v2n(self.polydata.GetPoints().GetData()),T)
        self.trans = T @ self.trans
        c_points = self.polydata.GetPoints()
        for i in range(len(np_pts)):
            c_points.SetPoint(i, np_pts[i,:])
        self.polydata.Modified()
        
        self.redraw_stl()
        self.ren.ResetCamera()
        self.ui.vtkWidget.update()
    
    def actuate_centroid_select(self):
        '''
        Populates translate widget with centroid coordinates of the first slice
        '''
        try:
            cent = - np.mean(np.vstack([i for i in self.slice_data[0].outlines]), axis=0)
            self.ui.trans_widget.translate_x.setValue(cent[0])
            self.ui.trans_widget.translate_y.setValue(cent[1])
            self.ui.trans_widget.translate_z.setValue(cent[2])
        except Exception as e:
            print('Finding the centroid of the first slice did not happen.')
            print(e)
            return
    
    def actuate_vertex_select(self):
        '''
        Starts picking and handles ui button display
        '''
        
        #selected actor is the vertex highlight
        if hasattr(self,'selected_actor'):
            self.ren.RemoveActor(self.selected_actor)
        
        if self.picking:
            #Remove picking observer and re-initialise
            self.iren.RemoveObservers('LeftButtonPressEvent')
            self.iren.AddObserver('LeftButtonPressEvent',self.default_left_button)
            QtWidgets.QApplication.processEvents()
            self.picking = False
            self.ui.translate_drop_button.setChecked(False)
            self.ui.trans_widget.choose_vertex_button.setChecked(False)

        else:
            self.iren.AddObserver('LeftButtonPressEvent', self.picker_callback)
            self.picking = True
            #meant to keep dropdown engaged through the picking process, but ineffective. Stopping picking suspends, as does 'updating'.
            self.ui.trans_widget.choose_vertex_button.setChecked(True)
            self.ui.translate_drop_button.setChecked(True)

    def default_left_button(self, obj, event):
        #forward standard events according to the default style
        self.iren.GetInteractorStyle().OnLeftButtonDown()

    def picker_callback(self, obj, event):
        """
        Actuates a pick of a node on current component
        """
        colors = vtk.vtkNamedColors()
        
        picker = vtk.vtkPointPicker()
        picker.SetTolerance(1)
        
        pos = self.iren.GetEventPosition()
        
        picker.Pick(pos[0], pos[1], 0, self.ren)

        if picker.GetPointId() != -1:
            
            ids = vtk.vtkIdTypeArray()
            ids.SetNumberOfComponents(1)
            ids.InsertNextValue(picker.GetPointId())

            if hasattr(self,'selected_actor'):
                self.ren.RemoveActor(self.selected_actor)
            centre = self.polydata.GetPoint(picker.GetPointId())
            self.selected_actor = generate_sphere(centre,1,colors.GetColor3d("orchid"))
            
            self.ui.trans_widget.translate_x.setValue(-centre[0])
            self.ui.trans_widget.translate_y.setValue(-centre[1])
            self.ui.trans_widget.translate_z.setValue(-centre[2])
            
            self.ren.AddActor(self.selected_actor)

    def do_slice(self):
        """
        Performs slicing operation based on ui values
        """
        
        if hasattr(self,'slice_actors'):
            self.ren.RemoveActor(self.slice_actors)
            self.ui.slice_num_cb.clear()
            del self.slice_data
        
        if self.ui.quantity_rb.isChecked():
            outlines, break_point_ind, self.slice_actors = get_slice_data(self.polydata,self.ui.by_num_sb.value())
            self.ui.by_height_sb.setValue(outlines[1][0][0,-1]-outlines[0][0][0,-1])
        else:
            outlines, break_point_ind, self.slice_actors = get_slice_data(self.polydata,self.ui.by_height_sb.value(), False)
            self.ui.by_num_sb.setValue(len(outlines))
            
        self.slice_data = [None] * len(outlines)
        
        #add to combobox and linked slice object
        self.ui.slice_num_cb.blockSignals(True)
        for i in range(len(outlines)):
            self.ui.slice_num_cb.insertItem(i,'Slice %d'%i)
            self.slice_data[i] = slice_obj(outlines[i], break_point_ind[i])

        self.ui.slice_num_cb.setEnabled(True)
        self.ui.outline_num_cb.setEnabled(True)
        
        self.ui.outline_box.setEnabled(True)
        self.ui.trans_widget.first_centroid.setEnabled(True)
        
        self.ren.AddActor(self.slice_actors)
        self.ui.vtkWidget.update()
        self.ui.slice_num_cb.setCurrentIndex(0)
        self.ui.slice_num_cb.blockSignals(False)
        self.ui.outline_box.setEnabled(True)
        self.draw_slices()

    def draw_slices(self):
        #get active slice
        entry = self.ui.slice_num_cb.currentIndex()
        
        self.ui.outline_num_cb.blockSignals(True) #block outline from updating
        
        if hasattr(self,'slice_actor_collection'):
            self.ren.RemoveActor(self.slice_actor_collection)
            self.ren.RemoveActor(self.slice_caption_actor)
            self.ui.figure.clear()
            self.ui.outline_num_cb.clear()
            del self.active_outline
        
        outlines = self.slice_data[entry].outlines
        bp = self.slice_data[entry].break_points
        
        for i in range(len(outlines)):
            self.ui.outline_num_cb.insertItem(i,'Outline %d'%i)
        
        #update mpl canvas and vtk
        self.slice_actor_collection = vtk.vtkAssembly()
        ax = self.ui.figure.gca()
        
        color = vtk_color3D_to_tuple('Gray')
        
        for i in range(len(outlines)):
            if len(bp) > 0:
                if bp[i]:
                    start_ind, end_ind = 0, 0
                    for list_value in bp[i]:
                        end_ind += list_value
                        self.slice_actor_collection.AddPart(gen_outline_actor(outlines[i][start_ind:end_ind,:], color, 4))
                        ax.plot(outlines[i][start_ind:end_ind,0], outlines[i][start_ind:end_ind,1], 'k-', alpha=0.2)
                        start_ind = start_ind+list_value
                    #last entry:
                    self.slice_actor_collection.AddPart(gen_outline_actor(outlines[i][start_ind:,:], color, 4))
                    ax.plot(outlines[i][start_ind:,0], outlines[i][start_ind:,1], 'k-', alpha=0.2)
                else:
                    self.slice_actor_collection.AddPart(gen_outline_actor(outlines[i], color, 4))
                    ax.plot(outlines[i][:,0], outlines[i][:,1], 'k-', alpha=0.2)
            else:
                self.slice_actor_collection.AddPart(gen_outline_actor(outlines[i], color, 4))
                ax.plot(outlines[i][:,0], outlines[i][:,1], 'k-', alpha=0.2)

        ax.set_ylabel("y (mm)")
        ax.set_xlabel("x (mm)")
        ax.grid(visible=True, which='major', color='#666666', linestyle='-', alpha=0.1)
        ax.minorticks_on()
        ax.grid(visible=True, which='minor', color='#666666', linestyle='-', alpha=0.2)
        
        
        #z layer height annotation
        ax.text(0.95, 0.01, 'z = %0.3f'%np.mean(outlines[0][:,2]),
        verticalalignment='bottom', horizontalalignment='right',
        transform=ax.transAxes,
        color='k', fontsize=10, alpha=0.2)
        ax.set_aspect(1)
        self.ui.canvas.draw()

        self.slice_caption_actor = gen_caption_actor('%s'%entry, self.slice_actor_collection, color, [5,5,0])
        
        self.ren.AddActor(self.slice_actor_collection)
        self.ren.AddActor(self.slice_caption_actor)
        
        self.ui.vtkWidget.update()
        
        self.ui.outline_num_cb.setCurrentIndex(0)
        self.ui.outline_num_cb.blockSignals(False)
        
        self.draw_outlines()
        
        
    def draw_outlines(self):
        '''
        Redraws current outline
        '''
        #remove any existing outlines from canvas
        if hasattr(self,'active_outline'):
            for i in self.active_outline:
                ref = i.pop(0)
                try: ref.remove() 
                except: pass
                del ref
        if hasattr(self, 'current_outline_actor'):
            self.ren.RemoveActor(self.current_outline_actor)
            self.ren.RemoveActor(self.outline_caption_actor)
        
        #get active outline
        slice_entry = self.ui.slice_num_cb.currentIndex()
        outline_entry = self.ui.outline_num_cb.currentIndex()
        bp = self.slice_data[slice_entry].break_points
        self.active_outline = []
        ax = self.ui.figure.gca()
        self.current_outline_actor = vtk.vtkAssembly()
        
        color = vtk_color3D_to_tuple('Black')
        
        if len(bp) > 0:
            if bp[outline_entry]:
                start_ind, end_ind = 0, 0
                for val in bp[outline_entry]:
                    end_ind += val
                    self.current_outline_actor.AddPart(gen_outline_actor(self.slice_data[slice_entry].outlines[outline_entry][start_ind:end_ind], color, 4))
                    self.active_outline.append(ax.plot(self.slice_data[slice_entry].outlines[outline_entry][start_ind:end_ind,0], self.slice_data[slice_entry].outlines[outline_entry][start_ind:end_ind,1], 'k-', alpha=0.8, label='active'))
                    start_ind = start_ind+val
                #last entry
                self.current_outline_actor.AddPart(gen_outline_actor(self.slice_data[slice_entry].outlines[outline_entry][start_ind:], color, 4))
                self.active_outline.append(ax.plot(self.slice_data[slice_entry].outlines[outline_entry][start_ind:,0], self.slice_data[slice_entry].outlines[outline_entry][start_ind:,1], 'k-', alpha=0.8, label='active'))
            else:
                self.active_outline.append(ax.plot(self.slice_data[slice_entry].outlines[outline_entry][:,0], self.slice_data[slice_entry].outlines[outline_entry][:,1], 'k-', alpha=0.8, label='active'))
            
        else:
            self.current_outline_actor.AddPart(gen_outline_actor(self.slice_data[slice_entry].outlines[outline_entry], color, 4))
            self.active_outline.append(ax.plot(self.slice_data[slice_entry].outlines[outline_entry][:,0], self.slice_data[slice_entry].outlines[outline_entry][:,1], 'k-', alpha=0.8, label='active'))
        self.ui.canvas.draw()
        
        self.outline_caption_actor = gen_caption_actor('%s'%outline_entry, self.current_outline_actor, color)
        
        self.ren.AddActor(self.current_outline_actor)
        self.ren.AddActor(self.outline_caption_actor)
        self.ui.path_num_cb.clear()
        self.draw_paths()
        
    def path_outlines(self):
        """
        Interacts with slice_objs to create paths coinciding with outlines
        """
        
        self.ui.path_num_cb.blockSignals(True)

        #CASE 1 - operate on single selected outline
        if not self.ui.outline_all_button.isChecked():

            slice_entry = self.ui.slice_num_cb.currentIndex()
            outline_entry = self.ui.outline_num_cb.currentIndex()
            
            if not self.slice_data[slice_entry].paths: #empty list
                #populate with empty lists to make sure there's at least one list for paths per outline
                self.slice_data[slice_entry].paths = [ [] for _ in range(len(self.slice_data[slice_entry].outlines))]

            
            local_outline = self.slice_data[slice_entry].outlines[outline_entry]
            if self.slice_data[slice_entry].break_points:
                local_bp = self.slice_data[slice_entry].break_points[outline_entry]
            else:
                local_bp = None
            
            if self.slice_data[slice_entry].paths[outline_entry]:
                path_entry = self.ui.path_num_cb.currentIndex()
            else:
                path_entry = None #outline without any paths
            
            if self.ui.path_outline_cb.isChecked():
                out_ = self.ui.po_widget.outline_outer_offset_sb.value()
                in_ = self.ui.po_widget.outline_inner_offset_sb.value()
                self.slice_data[slice_entry].paths[outline_entry] = [] #wipe out all paths associated with this outline
                if local_bp:
                    start_ind, end_ind = 0, 0
                    for val in local_bp:
                        end_ind += val
                        if start_ind == 0:
                            self.slice_data[slice_entry].paths[outline_entry].append(offset_poly(local_outline[start_ind:end_ind], out_))
                        else:
                            self.slice_data[slice_entry].paths[outline_entry].append(offset_poly(local_outline[start_ind:end_ind], -in_))
                        start_ind = start_ind+val
                    #last entry
                    self.slice_data[slice_entry].paths[outline_entry].append(offset_poly(local_outline[start_ind:], -in_))

                else:
                     self.slice_data[slice_entry].paths[outline_entry].append(offset_poly(local_outline, out_))
                    
            if self.ui.thin_wall_button.isChecked():

                ordered_central_line_path = get_ordered_central_line_path(local_outline, local_bp, self.ui.tw_widget.step_size.value(), self.ui.tw_widget.hatch_interval.value())
                if ordered_central_line_path is not None:
                    if path_entry is not None:
                        self.ui.path_num_cb.removeItem(path_entry)
                        self.slice_data[slice_entry].paths[outline_entry][path_entry] = np.array(ordered_central_line_path)
                        self.ui.path_num_cb.insertItem(path_entry,'Path %d'%path_entry)
                        self.ui.path_num_cb.setCurrentIndex(path_entry)
                    else:
                        self.slice_data[slice_entry].paths[outline_entry].append(np.array(ordered_central_line_path))
                        self.ui.path_num_cb.addItem('Path %d'%(self.ui.path_num_cb.count()))
                        self.ui.path_num_cb.setCurrentIndex(self.ui.path_num_cb.count()-1)
        
        #CASE 2 - do all outlines on selected slice
        elif self.ui.outline_all_button.isChecked() and self.ui.outline_all_widget.current_slice_cb.isChecked():
            slice_entry = self.ui.slice_num_cb.currentIndex()
            
            #populate with empty lists to make sure there's at least one list for paths per outline
            self.slice_data[slice_entry].paths = [ [] for _ in range(len(self.slice_data[slice_entry].outlines))]
            
            for i in range(len(self.slice_data[slice_entry].outlines)):
                local_outline = self.slice_data[slice_entry].outlines[i]
                if self.slice_data[slice_entry].break_points:
                    local_bp = self.slice_data[slice_entry].break_points[i]
                else:
                    local_bp = None
                
                if self.ui.path_outline_cb.isChecked():
                    out_ = self.ui.po_widget.outline_outer_offset_sb.value()
                    in_ = self.ui.po_widget.outline_inner_offset_sb.value()
                    self.slice_data[slice_entry].paths[i] = [] #wipe out all paths associated with this outline
                    if local_bp:
                        start_ind, end_ind = 0, 0
                        for val in local_bp:
                            end_ind += val
                            if start_ind == 0:
                                self.slice_data[slice_entry].paths[i].append(offset_poly(local_outline[start_ind:end_ind], out_))
                            else:
                                self.slice_data[slice_entry].paths[i].append(offset_poly(local_outline[start_ind:end_ind], -in_))
                            start_ind = start_ind+val
                        #last entry
                        self.slice_data[slice_entry].paths[i].append(offset_poly(local_outline[start_ind:], -in_))

                    else:
                         self.slice_data[slice_entry].paths[i].append(offset_poly(local_outline, out_))
                
                if self.ui.thin_wall_button.isChecked():
                    ordered_central_line_path = get_ordered_central_line_path(local_outline, local_bp, self.ui.tw_widget.step_size.value(), self.ui.tw_widget.hatch_interval.value())
                    if ordered_central_line_path is not None:
                        self.slice_data[slice_entry].paths[i].append(np.array(ordered_central_line_path))

        
        #CASE 3 - do all outlines on all slices
        elif self.ui.outline_all_button.isChecked() and self.ui.outline_all_widget.all_slices_cb.isChecked():
            
            for i in range(len(self.slice_data)):
                #populate with empty lists to make sure there's at least one list for paths per outline
                self.slice_data[i].paths = [ [] for _ in range(len(self.slice_data[i].outlines))]

                for j in range(len(self.slice_data[i].outlines)):
                    local_outline = self.slice_data[i].outlines[j]
                    if self.slice_data[i].break_points:
                        local_bp = self.slice_data[i].break_points[j]
                    else:
                        local_bp = None
                
                    if self.ui.path_outline_cb.isChecked():
                        try:
                            paths = simple_fill(local_outline,1)
                            self.slice_data[i].paths[j] = paths
                        except Exception as e:
                            print('Unable to path:', e)
                            self.slice_data[i].paths[j] = [] #for draw_paths
                
                
                    if self.ui.thin_wall_button.isChecked():
                        ordered_central_line_path = get_ordered_central_line_path(local_outline, local_bp, self.ui.tw_widget.step_size.value(), self.ui.tw_widget.hatch_interval.value())
                        if ordered_central_line_path is not None:
                            self.slice_data[i].paths[j].append(np.array(ordered_central_line_path))
                            # self.ui.path_num_cb.addItem('Path %d'%(self.ui.path_num_cb.count()))


        self.ui.path_num_cb.setEnabled(True)
        
        self.ui.path_num_cb.blockSignals(False)
        
        self.ui.export_slice.setEnabled(True)
        # self.draw_slices() #to clear any existing intersections
        self.draw_paths()


    def draw_paths(self):
        
        #make sure there's something to plot
        slice_entry = self.ui.slice_num_cb.currentIndex()
        if not self.slice_data[slice_entry].paths:
            return
        
        outline_entry = self.ui.outline_num_cb.currentIndex()
        
        if self.ui.path_num_cb.currentIndex() == -1: #it's been cleared by draw_outlines
            for i in range(len(self.slice_data[slice_entry].paths[outline_entry])):
                self.ui.path_num_cb.insertItem(i,'Path %d'%i)
                self.ui.path_num_cb.setCurrentIndex(0)
                
        path_entry = self.ui.path_num_cb.currentIndex()
        
        #remove any existing active path from canvas
        if hasattr(self,'active_path'):
            for i in self.active_path:
                if type(i) is list:
                    ref = i.pop(0)
                else:
                    ref = i
                try: ref.remove() 
                except: pass
                del ref
            del self.active_path

        #plot paths
        self.active_path = []
        ax = self.ui.figure.gca()
        
        for i in range(len(self.slice_data[slice_entry].paths)):
            if self.slice_data[slice_entry].paths[i]:
                for j in range(len(self.slice_data[slice_entry].paths[i])):
                    path = self.slice_data[slice_entry].paths[i][j]
                    if j == path_entry and i == outline_entry:
                        self.active_path.append(ax.plot(path[:,0], path[:,1], '-', color = 'r'))
                        self.active_path.append(ax.plot(path[0,0], path[0,1], 'ro'))
                        self.active_path.append(ax.text(path[-1,0], path[-1,1],'END'))
                    else: #any other path beyond what's selected
                        self.active_path.append(ax.plot(path[:,0], path[:,1], '--', color = 'r', alpha=0.2))
    
        self.ui.canvas.draw()

    def export(self):
        '''
        Create pop-up which shows the user what's going to happen
        '''
        ew = export_widget(self, self.slice_data)
        ew.exec_()

        

class slice_obj:
    def __init__(self, outlines, break_points):
        self.outlines = outlines
        self.break_points = break_points
        self.alpha = None
        self.paths = []
        self.central_line = []
        self.intermediate_line = []

if __name__ == "__main__":
    app=QtWidgets.QApplication(sys.argv)
    window = standalone_app()
    window.show()
    sys.exit(app.exec_())