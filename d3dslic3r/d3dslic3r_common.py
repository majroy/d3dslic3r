import os
import vtk
import numpy as np
from scipy.spatial.distance import cdist
from scipy.spatial import Delaunay
from vtk.util.numpy_support import vtk_to_numpy as v2n
from vtk.util.numpy_support import numpy_to_vtk as n2v
from PyQt5 import QtCore, QtGui, QtWidgets
from sklearn.cluster import AgglomerativeClustering
from shapely.ops import unary_union, polygonize
import shapely.geometry as geometry
from pyclipper import PyclipperOffset, scale_to_clipper, scale_from_clipper, JT_SQUARE, ET_CLOSEDPOLYGON
from scipy.interpolate import interp1d
from importlib.resources import Resource


def make_splash():
    '''
    Makes and returns a Qt splash window object
    '''
    spl_fname=resource_filename("d3slic3r","meta/Logo.png")
    splash_pix = QtGui.QPixmap(spl_fname,'PNG')
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
    spl_fname=resource_filename("d3dslic3r","meta/background.png")
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

def get_slice_data(polydata,param,num_slices = True):
    """
    Obtains x,y pairs corresponding to a vtkCutter operation on input polydata 
    Params:
    polydata is a vtkPolydata object to be sliced
    param is either the number of slices or height of each slice
    num_slices sets slicing on number of total slices (True, default)
    Returns:
    slices: list of numpy arrays corresponding to each polydata intersection
    plane_collection: vtkAssembly of slices for display
    """
    #suppress output from the vtk logger
    vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_OFF)
    
    bbox = polydata.GetBounds()
    xy_origin = [(bbox[1] + bbox[0]) / 2.0,
                    (bbox[3] + bbox[2]) / 2.0]
    #Assumes polydata starts at 0.001 above minimum z value of the bounding box, and the first slice is the 'footprint' of the polydata. Additional value is to avoid the last 'slice' consistent with the upper boundary.
    if num_slices:
        z_vals = np.linspace(bbox[4]+0.001,bbox[5],param+1)[0:-1]
    else:
        # z_vals based on fixed height of each layer
        num_z_vals = int(np.floor((bbox[5] - bbox[4]+0.001)/param))
        z_vals = np.linspace(bbox[4]+0.001,bbox[5],num_z_vals+1)[0:-1]

    plane_collection = vtk.vtkAssembly()
    slices = []
    for i in range(len(z_vals)):
        plane = vtk.vtkPlane()
        plane.SetNormal(0,0,1) 
        plane.SetOrigin(tuple([xy_origin[0],xy_origin[1],z_vals[i]]))
        
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(polydata)
        cutter.Update()
        slices.append(v2n(cutter.GetOutput().GetPoints().GetData()))
        
        cutter_mapper = vtk.vtkPolyDataMapper()
        cutter_mapper.SetInputConnection(cutter.GetOutputPort())
    
        # Create the cut actor.
        actor = vtk.vtkActor()
        actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Tomato'))
        actor.GetProperty().SetLineWidth(2)
        actor.SetMapper(cutter_mapper)
        plane_collection.AddPart(actor)
        
    return slices, plane_collection

def get_sub_slice_data(outlines, threshold):
    
    #make agglomerative clustering object
    agg_cluster = AgglomerativeClustering(n_clusters = None, metric ='euclidean', memory=None, connectivity=None, compute_full_tree='auto', linkage='single', distance_threshold=threshold, compute_distances=False)
    
    new_outlines=[]
    for outline in outlines:
        clustering = agg_cluster.fit(outline[:,0:2])
        #make list of truth arrays for each cluster
        for i in range(clustering.n_clusters_):
            new_outlines.append(outline[(clustering.labels_ == i),:])
            
    return new_outlines

def get_polydata_from_stl(fname):
    """
    Load the given STL file, and return a vtkPolyData object from it.
    Params:
    fname the filename of the stl file
    Returns: 
    vtkPolydata object for processing/rendering
    """
    
    reader = vtk.vtkSTLReader()
    reader.SetFileName(fname)
    reader.Update()
    
    polydata = reader.GetOutput()

    return polydata

def actor_from_polydata(polydata):
    """
    Wrap the provided vtkPolyData object in a mapper and an actor, returning
    the actor.
    """
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)

    stl_actor = vtk.vtkActor()
    stl_actor.SetMapper(mapper)

    stl_actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Gray'))

    return stl_actor

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

def gen_outline_actor(pts, color = (1,1,1), size = 2):
    '''
    Returns an outline actor with specified numpy array of points, color and size. pts should be ordered
    '''
    if color[0]<=1 and color != None:
        color=(int(color[0]*255),int(color[1]*255),int(color[2]*255))
    if color[0]>=1 and color != None:
        color=(color[0]/float(255),color[1]/float(255),color[2]/float(255))
    points=vtk.vtkPoints()

    points.SetData(n2v(pts))

    lineseg=vtk.vtkPolygon()
    lineseg.GetPointIds().SetNumberOfIds(len(pts))
    for i in range(len(pts)):
        lineseg.GetPointIds().SetId(i,i)
    linesegcells=vtk.vtkCellArray()
    linesegcells.InsertNextCell(lineseg)
    outline=vtk.vtkPolyData()
    outline.SetPoints(points)
    outline.SetVerts(linesegcells)
    outline.SetLines(linesegcells)
    mapper=vtk.vtkPolyDataMapper()
    mapper.SetInputData(outline)
    outline_actor=vtk.vtkActor()
    outline_actor.SetMapper(mapper)
    outline_actor.GetProperty().SetColor(color)
    outline_actor.GetProperty().SetPointSize(size)
    return outline_actor

def gen_caption_actor(message, actor = None, color = (0,0,0)):
    '''
    Captions an actor
    '''
    caption_actor = vtk.vtkCaptionActor2D()
    b = actor.GetBounds()
    caption_actor.SetAttachmentPoint((b[0],b[2],b[4]))
    caption_actor.SetCaption(message)
    caption_actor.SetThreeDimensionalLeader(False)
    caption_actor.BorderOff()
    caption_actor.LeaderOff()
    caption_actor.SetWidth(0.25 / 3.0)
    caption_actor.SetHeight(0.10 / 3.0)
    
    p = caption_actor.GetCaptionTextProperty()
    p.SetColor(color)
    p.BoldOn()
    p.ItalicOff()
    p.SetFontSize(36)
    p.ShadowOn()
    return caption_actor

def sort_ccw(inp):
    """
    Sorts in 2D x,y pairs according to ccw position from the centroid.
    Params:
    inp is a numpy array of shape (N, 3) corresponding to 3D points with uniform z values
    Returns:
    Points are sorted ccw based on angular position. Points with the same angular position are subsequently sorted such that shortest distance from the centroid come first. Ensures that the polygon is closed, such that the first point is the last point.
    """
    
    points = inp[:,0:2]
    # Get centroid/centre of mass
    cent = np.reshape(np.mean(points, axis=0), (-1, 2))
    
    # Compute angles
    angles = np.arctan2((points-cent)[:, 1], (points-cent)[:, 0])

    # Calculate distances from centroid to point
    dist = cdist(points,cent)
    dist = np.reshape(dist,(-1,1))
    
    # Transform angles from [-pi,pi] -> [0, 2*pi]
    angles[angles < 0] = angles[angles < 0] + 2 * np.pi
    angles = np.reshape(angles,(-1,1))

    # Stack angles and dist together for sorting
    c = np.hstack((angles,dist))
    
    # Sort with angles as the first criteria, distance the second: if the same angle is found then the shortest distance should come first
    ind = np.lexsort((c[:,1],c[:,0]))
    B = inp[ind]
    return np.vstack((B, B[0,:]))

def sort_alpha(inp, alpha = 1):
    """
    Triangulates incoming points and performs an alpha-shape sort suited for outlines that have concave features.
    Params:
        inp is a numpy array of shape (N, 3) corresponding to 3D points with uniform z values
        sp is the semiperimeter cutoff corresponding to the alpha shape to be used. The higher this value, the more points will remain.
    Returns:
        Ordered, closed polygon with the last point equal to the first point
    """
    points = inp[:,0:2]
    zval = np.mean(inp[:,-1])
    tri = Delaunay(points)
    
    coords = points.copy()
    
    triangles = coords[tri.simplices]
    a = ((triangles[:,0,0] - triangles[:,1,0]) ** 2 + (triangles[:,0,1] - triangles[:,1,1]) ** 2) ** 0.5
    b = ((triangles[:,1,0] - triangles[:,2,0]) ** 2 + (triangles[:,1,1] - triangles[:,2,1]) ** 2) ** 0.5
    c = ((triangles[:,2,0] - triangles[:,0,0]) ** 2 + (triangles[:,2,1] - triangles[:,0,1]) ** 2) ** 0.5
    s = ( a + b + c ) / 2.0 #semiperimeter
    areas = (s*(s-a)*(s-b)*(s-c)) ** 0.5 #Heron's formula
    triangles = coords[tri.simplices]
    
    #make sure the areas are valid
    valid = np.isreal(areas) & ~np.isnan(areas) & ~np.isinf(areas)

    np.seterr(divide='ignore', invalid='ignore')
    co = a[valid] * b[valid] * c[valid] / (4.0 * areas[valid]) #circumradius
    np.seterr(divide='warn', invalid='warn')
    
    cutoff = np.mean(co[np.isreal(co) & ~np.isnan(co) & ~np.isinf(co)])
    filtered = triangles[valid][co < (alpha*cutoff)] #as opposed to the published 1 / alpha

    edge1 = filtered[:,(0,1)]
    edge2 = filtered[:,(1,2)]
    edge3 = filtered[:,(2,0)]
    edge_points = np.unique(np.concatenate((edge1,edge2,edge3)), axis = 0).tolist()
    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    chull = unary_union(triangles)
    try:
        x,y = chull.exterior.coords.xy
        outline = np.column_stack((x,y,np.ones(len(x))*zval)) #return outline appearing at z=0
        return outline
    except:
        #if chull doesn't have the exterior attribute (alpha was too small)
        return None

def do_transform(points, T):
    '''
    Applies 4x4 transformation matrix to points and returns the result
    @Param - points, Nx3 matrix of points; T - 4x4 homologous matrix
    '''
    X = points.copy()
    X = X.transpose()
    X = np.append(X, np.ones((1, X.shape[1])), axis=0) #pad with 1's
    X = T @ X #apply by matrix multiplication
    return X[0:3].transpose() #return an Nx3

def get_limits(pts, factor = 0.1):
    '''
    Returns a bounding box with x,y values bumped out by factor
    '''
    RefMin = np.amin(pts,axis=0)
    RefMax = np.amax(pts,axis=0)

    extents=RefMax-RefMin #extents
    rl=factor*(np.amin(extents[0:2])) #linear 'scale' to set up interactor
    return [RefMin[0]-rl, \
      RefMax[0]+rl, \
      RefMin[1]-rl, \
      RefMax[1]+rl, \
      RefMin[2],RefMax[2]]

def get_intersections(outline, angular_offset, width, bead_offset = 0.5):
    """
    Returns intersections running from a series of lines drawn from -x to +x, -y to +y for a constant z value
    Params:
    outline - ordered 3D outline points, z must be constant
    angular_offset - rotation which intersection lines are solved for
    pass_param - either the number of lines or the distance between lines (default) depending on if 'number' is true or false.
    Returns:
    Intersections in all cases, the width of each pass or the number of passes depending on pass_param
    """
    
    zval = np.mean(outline[:,-1])
    # outline = outline[:,0:2]
    trans = np.eye(4)
    #move outline to centroid and rotate by angular_offset
    a = np.deg2rad(angular_offset) #negative for counterclockwise
    trans[0:2,0:2]=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    trans[0:3,-1] = -np.mean(outline, axis=0)
    X = do_transform(outline,trans)
    
    
    limits = get_limits(X,0.)

    yrange = [limits[2]*1.2,limits[3]*1.2]
    #break up on the basis of bead width
    num_passes = int(np.floor((limits[1]-(width*bead_offset) - limits[0]+(width*bead_offset))/(width*bead_offset)))
    xrange = np.linspace(limits[0]+(width*bead_offset),limits[1]-(width*bead_offset),num_passes)
        
    intersections = []
    for k in range(len(xrange)):
        line = np.array([[xrange[k],yrange[0]], [xrange[k],yrange[1]]])
        line1 = tuple([tuple(x) for x in line.tolist()])

        for i in range(len(X)-1):
            line2 = tuple([tuple(x) for x in X[i:i+2,:]])
            local_intersection = line_intersection(line1, line2)
            if local_intersection is not None:
                intersections.append(np.array(local_intersection,zval))
    intersections = np.column_stack((np.asarray(intersections),np.ones(len(intersections))*zval)) 
    
    #return intersections in original coordinate system, actual bead offset
    return do_transform(intersections,np.linalg.inv(trans)), (xrange[1]-xrange[0])/width

def line_intersection(line1, line2):
    '''
    Returns the x,y intersection intersection of line1 and line2 if it exists.
    Params:
    line1, line2: tuple pairs of x,y points
    Returns:
    x & y values of intersection
    '''

    x1, x2, x3, x4 = line1[0][0], line1[1][0], line2[0][0], line2[1][0]
    y1, y2, y3, y4 = line1[0][1], line1[1][1], line2[0][1], line2[1][1]

    dx1 = x2 - x1
    dx2 = x4 - x3
    dy1 = y2 - y1
    dy2 = y4 - y3
    dx3 = x1 - x3
    dy3 = y1 - y3

    det = dx1 * dy2 - dx2 * dy1
    det1 = dx1 * dy3 - dx3 * dy1
    det2 = dx2 * dy3 - dx3 * dy2

    if det == 0.0:  # lines are parallel
    
        if line1[0] == line2[0] or line1[1] == line2[0]:
            return line2[0]
        elif line1[0] == line2[1] or line1[1] == line2[1]:
            return line2[1]
        
        #Special cases
        # if det1 != 0.0 or det2 != 0.0:  # lines are not co-linear
            # pass  # so no solution (or return None)

        # if dx1:
            # if x1 < x3 < x2 or x1 > x3 > x2:
                # pass  # infinitely many solutions (or return np.inf)
        # else:
            # if y1 < y3 < y2 or y1 > y3 > y2:
                # pass  # infinitely many solutions (or return np.inf)

        return None #no intersection

    s = det1 / det
    t = det2 / det

    if 0.0 < s < 1.0 and 0.0 < t < 1.0:
        return x1 + t * dx1, y1 + t * dy1

def respace_equally(X,input):
    '''
    Takes X, a 2D array of points, respaces them on the basis of input, either a floating point value of what the target interval between points is, or an integer which is the total number of points. Returns the new array of points, the perimeter and the number of points.
    '''
    distance=np.sqrt(np.sum(np.diff(X,axis=0)**2,axis=1))
    s=np.insert(np.cumsum(distance),0,0)
    Perimeter=np.sum(distance)

    if not isinstance(input,(int)):
        nPts=round(Perimeter/input)
    else:
        nPts=input
    
    sNew=np.linspace(0,s[-1],nPts)
    fx = interp1d(s,X[:,0])
    fy = interp1d(s,X[:,1])
    
    Xnew=fx(sNew)
    Ynew=fy(sNew)
    
    X_new=np.stack((Xnew,Ynew),axis=-1)
    X_new = np.vstack((X_new, X_new[0,:]))#make sure last point is the same as the first point
    return X_new,Perimeter,nPts

def offset_poly(poly, offset):
    '''
    Uses pyclipper to offset param poly and return an offset polygon according to offset param. poly is 3D (XYZ by N), and returns the same.
    '''
    zval = np.mean(poly[:,-1])
    X = tuple(map(tuple, poly[:,:2]))
    scaled_poly = scale_to_clipper(X)
    pco = PyclipperOffset()
    pco.AddPath(scaled_poly, JT_SQUARE, ET_CLOSEDPOLYGON)
    scaled_result = pco.Execute(scale_to_clipper(offset))
    
    result = scale_from_clipper(scaled_result)
    two_d = np.asarray(result[0])
    
    #make sure the number of points and therefore polygon interval is preserved
    two_d = respace_equally(two_d,len(poly))[0]
    
    return np.column_stack((two_d,np.ones(len(two_d))*zval)) 
    

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