#!/usr/bin/env python
'''
Contains methods/functions used to skeletonize thin-walled features
'''

__author__ = "Z. Miao & M. J. Roy"
__version__ = "0.1"
__status__ = "Experimental"


import numpy as np
from scipy.spatial import distance

from d3dslic3r.common import line_intersection, get_intersections, get_limits

##Main thin wall functions
def get_skeleton_dict(outline,whole_angle,step_size,suggested_hatching_offset, break_point_index):
    """
    Returns a dictionary of skeleton lines comprised of the midpoints of intersections of hatch lines at each hatch angle

    skeleton_dict structure:
    {
        hatch_angle1: {  
            skeleton1: [midpoint1, midpoint2, ..., midpointN]
            skeleton1: [midpoint1, midpoint2, ..., midpointN]
        }
        hatch_angleN: {
            skeleton1: [midpoint1, midpoint2, ..., midpointN]
            skeletonN: [midpoint1, midpoint2, ..., midpointN]
        }
    }
    """
    
    midpoint_line_dict = {hatch_angle: [] for hatch_angle in np.arange(0, whole_angle, step_size)}
    for hatch_angle in np.arange(0, whole_angle, step_size):
        
        intersecting_lines, _, num_of_line_list = get_intersections(outline,hatch_angle,
                                                                    suggested_hatching_offset,0.5,break_point_index)

        # Get all the unique values in num_of_line_list
        lines_index_list = list(set(num_of_line_list))
        midpoint_line_dict[hatch_angle] = {line_index: [] for line_index in lines_index_list}
        
        for line_index, number_of_line in enumerate(num_of_line_list):
            if number_of_line in lines_index_list:
                midpoint = (intersecting_lines[line_index][0] + intersecting_lines[line_index][1]) / 2
                midpoint_line_dict[hatch_angle][number_of_line].append(midpoint)
        
    return midpoint_line_dict

def get_central_line_path(skeleton_dict):
    """
    Returns a numpy array of central line paths for each entry in the received skeleton_dict
    """
    central_line_path = []
    for rotate_angle_line1, path_index_line1 in skeleton_dict.items():
        for skeleton_line1 in path_index_line1.values():
            z_val = skeleton_line1[0][2]
            if len(skeleton_line1) > 1:
                for line_index1 in range(len(skeleton_line1) - 1):
                    P1 = skeleton_line1[line_index1][:2]
                    P2 = skeleton_line1[line_index1 + 1][:2]
                    line1 = [P1, P2]
                    for rotate_angle_line2, path_index_line2 in skeleton_dict.items():
                        if rotate_angle_line2 != rotate_angle_line1:
                            for skeleton_line2 in path_index_line2.values():
                                if len(skeleton_line2) > 1:
                                    for line_index2 in range(len(skeleton_line2) - 1):
                                        P3 = skeleton_line2[line_index2][:2]
                                        P4 = skeleton_line2[line_index2 + 1][:2]
                                        line2 = [P3, P4]
                                        local_intersection = line_intersection(line1, line2)
                                        if local_intersection is not None:
                                            central_line_path.append(np.array([local_intersection[0],
                                                                    local_intersection[1],z_val]))

    return np.array(central_line_path)


def order_points_cdist(points, closed = False):
    """
    Reorders incoming numpy array of points by euclidean distances using scipy.spatial.distance.cdist
    Setting closed to be True forces the first point to be the same as the last point
    """
    if len(points) < 2:
        return points

    ordered_points = [points[0]]
    points = np.delete(points, 0, axis=0)

    while len(points) > 0:
        last_point = ordered_points[-1]
        distances = distance.cdist([last_point], points)
        nearest_index = np.argmin(distances)
        ordered_points.append(points[nearest_index])
        points = np.delete(points, nearest_index, axis=0)

    #Check if the loop is closed and connect the last to the first point if necessary
    if not np.array_equal(ordered_points[0], ordered_points[-1]) and closed:
        ordered_points.append(ordered_points[0])

    return np.array(ordered_points)

def get_ordered_central_line_path(outline, break_point_indices, step_size = 30.01, hatch_interval = 15):
    '''
    Main function which calls get_skeleton_dict to first generate a dictionary of all line intersections. The central path is then calculated on that premise. Further functions sort and order the result. Operates only on single outlines, or single parent/child outline pairs, returns None if these conditions are not met.
    '''
    
    def get_starting_point(inp):
        """
        get the starting point of the outline based on the distance between points
        if the distance between two points is the largest, the starting point is the first point
        """
        points = inp[:,0:2]
        dist = []
        for i in range(len(points)-1):
            distance = np.linalg.norm(points[i+1] - points[i])
            dist.append(distance)
            
        mean = np.mean(dist)
        std = np.std(dist)
        z_scores = [(x - mean) / std for x in dist]
        outliers = np.argmax(z_scores)
        return outliers
    
    def remove_repeated_points_preserve_order(points):
        '''
        Performs the following described as a function:
        def f(a):
            indexes = np.unique(a, axis=0, return_index=True)[1]
            return a[np.sort(indexes)]

        np.asarray[f(i) for i in dup_arr]
        #https://stackoverflow.com/questions/65686531/how-to-remove-duplicates-in-a-numpy-array-and-keep-its-sorting
        # '''
        # return np.asarray([i[np.sort(np.unique(i, axis=0, return_index=True)[1])] for i in points])
        #the above should return the following
        seen = set()
        unique_points = []
        for point in points:
            point_tuple = tuple(point)
            if point_tuple not in seen:
                seen.add(point_tuple)
                unique_points.append(point)
        return np.array(unique_points)
    
    def split_central_line(ordered_central_line_path, outline):
        """
        Returns a list of central line paths for each entry
        """
        break_point_index_list = []
        for line_index1 in range(len(ordered_central_line_path) - 1):
            P1 = ordered_central_line_path[line_index1][:2]
            P2 = ordered_central_line_path[line_index1 + 1][:2]
            line1 = [P1, P2]

            for line_index2 in range(len(outline) - 1):
                P3 = outline[line_index2][:2]
                P4 = outline[line_index2 + 1][:2]
                line2 = [P3, P4]
                local_intersection = line_intersection(line1, line2)
                if local_intersection is not None:
                    break_point_index_list.append(line_index1+1)

        break_point_index_list = list(set(break_point_index_list))
        
        break_point_index_list.sort()
        if len(break_point_index_list) != 0:

            ordered_central_line_path = np.concatenate((ordered_central_line_path[break_point_index_list[0]:], 
                                                        ordered_central_line_path[:break_point_index_list[0]]), axis=0)
            break_point_index_list = [x - break_point_index_list[0] for x in break_point_index_list][1:]
            cleaned_central_line_path = np.split(ordered_central_line_path, break_point_index_list)
            # remove the line if the length is less than 2
            cleaned_central_line_path = [x for x in cleaned_central_line_path if len(x) > 2]
        else:
            cleaned_central_line_path = [ordered_central_line_path]
        
        return cleaned_central_line_path
    
    limits = get_limits(outline,0)

    suggested_hatching_offset = min((limits[1]-limits[0]),(limits[3]-limits[2]))/hatch_interval
    whole_angle = 180
    
    #ensure that the break_point_indices has only one entry
    if break_point_indices is None:
        skeleton_dict = get_skeleton_dict(outline,whole_angle,step_size,
                                                suggested_hatching_offset, break_point_indices)
    elif len(break_point_indices) == 1:
        skeleton_dict = get_skeleton_dict(outline,whole_angle,step_size,
                                                suggested_hatching_offset, break_point_indices)
    else:
        return None

    central_line_path = get_central_line_path(skeleton_dict)
    ordered_central_line_path = order_points_cdist(central_line_path, True)
    starting_point_index = get_starting_point(ordered_central_line_path)
    ordered_central_line_path = np.concatenate((ordered_central_line_path[starting_point_index:], 
                                                ordered_central_line_path[:starting_point_index]), axis=0)
    ordered_central_line_path = remove_repeated_points_preserve_order(ordered_central_line_path)
    ordered_central_line_path = order_points_cdist(ordered_central_line_path, True)
    #unsure how this is used:
    # ordered_central_line_path = split_central_line(ordered_central_line_path, outline)
    #debug
    # # get the skeleton of the outline
    # skeleton = []
    # for key in skeleton_dict.keys():
        # for value in skeleton_dict[key].values():
            # skeleton.append(value)
    #because the preceding functions are based on all being 'closed' loops, return everything except the last point
    return ordered_central_line_path[:-1]#, skeleton