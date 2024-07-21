import os
import vtk

from PyQt5 import QtCore, QtGui, QtWidgets
import importlib.resources

class collapsible_box(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(collapsible_box, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def set_content_layout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

def make_splash():
    '''
    Makes and returns a Qt splash window object
    '''
    spl_fname = importlib.resources.files('d3dslic3r') / 'meta/Logo.png'
    splash_pix = QtGui.QPixmap(spl_fname.__str__(),'PNG')
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.SplashScreen)
    splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
    
    font = splash.font()
    font.setPixelSize(20)
    font.setWeight(QtGui.QFont.Bold)
    splash.setFont(font)
    
    # splash.showMessage('v%s'%(version('d3dslic3r')),QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom, QtCore.Qt.lightGray)
    splash.showMessage('v%s'%("0.0.1"),QtCore.Qt.AlignRight | QtCore.Qt.AlignTop, QtCore.Qt.darkGray)
    return splash

def make_logo(ren):
    spl_fname = importlib.resources.files('d3dslic3r') / 'meta/background.png'
    img_reader = vtk.vtkPNGReader()
    img_reader.SetFileName(spl_fname)
    img_reader.Update()
    logo = vtk.vtkLogoRepresentation()
    logo.SetImage(img_reader.GetOutput())
    logo.ProportionalResizeOn()
    logo.SetPosition( 0.1, 0.1 ) #lower left
    logo.SetPosition2( 0.8, 0.8 ) #upper right
    logo.GetImageProperty().SetDisplayLocationToBackground()
    ren.AddViewProp(logo)
    logo.SetRenderer(ren)
    return logo

def get_file(*args):
    '''
    Returns absolute path to filename and the directory it is located in from a PyQt5 filedialog. First value is file extension, second is a string which overwrites the window message.
    '''
    ext = args
    launchdir = os.getcwd()
    ftypeName={}
    ftypeName['*.stl']=["STereoLithography file", "*.stl","STL file"]
    
    filter_str = ""
    for entry in args:
        filter_str += ftypeName[entry][2] + ' ('+ftypeName[entry][1]+');;'
    filter_str += ('All Files (*.*)')
    
    filer = QtWidgets.QFileDialog.getOpenFileName(None, ftypeName[ext[0]][0], 
         os.getcwd(),(filter_str))

    if filer[0] == '':
        return None
        
    else: #return the filename/path
        return filer[0]

def generate_sphere(center, radius, color):
    source = vtk.vtkSphereSource()
    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetThetaResolution(20)
    source.SetPhiResolution(20)
    source.Update()
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(source.GetOutput())
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    
    return actor

def xyview(ren):
    camera = ren.GetActiveCamera()
    camera.SetPosition(0,0,1)
    camera.SetFocalPoint(0,0,0)
    camera.SetViewUp(0,1,0)
    ren.ResetCamera()

def yzview(ren):
    camera = ren.GetActiveCamera()
    camera.SetPosition(1,0,0)
    camera.SetFocalPoint(0,0,0)
    camera.SetViewUp(0,0,1)
    ren.ResetCamera()

def xzview(ren):
    vtk.vtkObject.GlobalWarningDisplayOff() #mapping from '3' triggers an underlying stereoview that most displays do not support for trackball interactors
    camera = ren.GetActiveCamera()
    camera.SetPosition(0,1,0)
    camera.SetFocalPoint(0,0,0)
    camera.SetViewUp(0,0,1)
    ren.ResetCamera()