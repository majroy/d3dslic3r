from os import path
import sys
from setuptools import setup, find_packages


setup(name = 'd3dslic3r',
    version = '0.3post2',
    description = 'DED SLICER',
    long_description = 'https://github.com/majroy/d3dslic3r',
    url = 'https://github.com/majroy/d3dslic3r',
    author = 'M J Roy',
    author_email = 'matthew.roy@manchester.ac.uk',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Win32 (MS Windows)',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python :: 3.11',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        ],

    install_requires=['vtk>=6.0','numpy','scipy','pyyaml>=5.0','matplotlib','PyQt5>=5','h5py','scikit-learn','shapely','pyclipper'],
    license = 'Creative Commons Attribution-Noncommercial-Share Alike license',
    keywords = '3D printing, direct energy deposition, slicer, computer aided manufacturing',
    packages=['d3dslic3r', 'd3dslic3r.meta'],
    package_data = {'d3dslic3r' : ['README.MD',], 'd3dslic3r.meta' : ['*.*',] },
    include_package_data=True
    )