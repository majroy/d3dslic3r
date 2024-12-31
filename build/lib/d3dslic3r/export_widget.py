#!/usr/bin/env python
'''
d3dslic3r export_widget - popup to allow for directing export formats
'''

__author__ = "M.J. Roy"
__version__ = "0.4"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2024-"


import os, io
import numpy as np

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt
import importlib.resources


class export_widget(QtWidgets.QDialog):

    def __init__(self, parent, slice_data):
        super(export_widget, self).__init__(parent)
        self.slice_data = slice_data

        self.setWindowTitle("d3dslic3r - export")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumSize(QtCore.QSize(450, 200))
        
        self.clip_label = QtWidgets.QLabel()
        self.export_status_label = QtWidgets.QLabel()
        
        ico = importlib.resources.files('d3dslic3r') / 'meta/clippy.png'
        with importlib.resources.as_file(ico) as path:
            pix_map1 = QtGui.QPixmap(u"%s"%path.absolute())
            
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

        output_label = QtWidgets.QLabel("Output format:")
        self.output_box = QtWidgets.QComboBox()
        self.output_box.addItems(["Text", "KUKA"])
        
        param_layout.addWidget(prefix_label,0,0,1,1)
        param_layout.addWidget(self.prefix,0,1,1,2)
        param_layout.addWidget(export,0,3,1,1)
        param_layout.addWidget(work_dir_path_label,1,0,1,1)
        param_layout.addWidget(self.work_dir_path,1,1,1,2)
        param_layout.addWidget(wd_choose_path,1,3,1,1)
        
        param_layout.addWidget(output_label,2,0,1,1)
        param_layout.addWidget(self.output_box,2,1,1,2)
        
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
        If the current working directory is valid, write out all of the entries of each slice_obj in slice_data
        """
        
        if not os.path.isdir(self.work_dir_path.text()):
            return
        
        if self.output_box.currentIndex() == 1:
            self.to_kuka()
        else:
            self.to_txt()
        
        ico = importlib.resources.files('d3dslic3r') / 'meta/dippy.png'
        with importlib.resources.as_file(ico) as path:
            pix_map2 = QtGui.QPixmap(u"%s"%path.absolute())
        
        self.clip_label.setPixmap(pix_map2)
        self.export_status_label.setText("Complete.")
        self.clip_label.update()

    def to_kuka(self):
        """
        Save paths to KUKA code using ArcTech commands 
        """
        from d3dslic3r.d3dslic3r_common import respace_equally
        
        # write a kuka .SRC and .DAT file
        src = open(f'{os.path.join(self.work_dir_path.text(),self.prefix.text())}.src','w')
        dat = open(f'{os.path.join(self.work_dir_path.text(),self.prefix.text())}.dat','w')

        # write strings for header
        src.write(f'DEF {self.prefix.text()}( )' '\n')
        src.write(r';FOLD INI;%{PE}' '\n')
        src.write(r'  ;FOLD BASISTECH INI' '\n')
        src.write(r'    GLOBAL INTERRUPT DECL 3 WHEN $STOPMESS==TRUE DO IR_STOPM ( )' '\n')
        src.write(r'    INTERRUPT ON 3' '\n') 
        src.write(r'    BAS (#INITMOV,0 )' '\n')
        src.write(r'  ;ENDFOLD (BASISTECH INI)' '\n')
        src.write(r'  ;FOLD USER INI' '\n')
        src.write(r'    ;Make your modifications here' '\n' '\n')
        src.write(r'  ;ENDFOLD (USER INI)' '\n')
        src.write(r';ENDFOLD (INI)' '\n\n')

        dat.write(f'DEFDAT  {self.prefix.text()}' '\n')
        dat.write(r';FOLD EXTERNAL DECLARATIONS;%{PE}%MKUKATPBASIS,%CEXT,%VCOMMON,%P' '\n')
        dat.write(r';FOLD BASISTECH EXT;%{PE}%MKUKATPBASIS,%CEXT,%VEXT,%P' '\n')
        dat.write(r'EXT  BAS (BAS_COMMAND  :IN,REAL  :IN )' '\n')
        dat.write(r'DECL INT SUCCESS' '\n')
        dat.write(r';ENDFOLD (BASISTECH EXT)' '\n')
        dat.write(r';FOLD USER EXT;%{E}%MKUKATPUSER,%CEXT,%VEXT,%P' '\n')
        dat.write(r';Make your modifications here' '\n' '\n')
        dat.write(r';ENDFOLD (USER EXT)' '\n')
        dat.write(r';ENDFOLD (EXTERNAL DECLARATIONS)' '\n\n')

        # define zero position (X, Y, Z)
        zero_pos =np.array([1200, -700, 1000])
        tool_angle = np.array([0, 90, 0])
        tool_speed = 100 # m/min

        # write base origin
        src.write(fr'BASE_DATA[1] = {{X {zero_pos[0]},Y {zero_pos[1]}, Z {zero_pos[2]}, A 0,B 0,C 0}}' '\n\n')

        # write first PTP home
        src.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
        src.write(r';FOLD Parameters ;%{h}' '\n')
        src.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
        src.write(r';ENDFOLD' '\n')
        src.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
        src.write(r';ENDFOLD' '\n\n')

        # get paths
        i = 0
        nPos = 0
        for slice_obj in self.slice_data:
            i+=1
            if slice_obj is not None:
                j = 0
                for outline in slice_obj.paths:
                    j+=1
                    if j == 1: # only outlines !!!!! there can be multiple paths for each outline!!!
                        xycoords = np.delete(outline, 2, axis=1)

                        # interpolate points points and include z vals (fixed)
                        spacing = 5.00 # in mm
                        interpoints, perimeter, nPts = respace_equally(xycoords, spacing)
                        interpoints = np.insert(interpoints, 2, path[0,2], axis=1)

                        # write arc commands and teach points
                        for n, points in enumerate(interpoints):
                            nPos+=1
                            if n == 0: # arc on
                                src.write(fr';FOLD ARCON WDAT{nPos} SPTP P{nPos} Vel=100 % PDAT{nPos} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                                src.write(r';FOLD Parameters ;%{h}' '\n')
                                src.write(fr';Params IlfProvider=kukaroboter.arctech.arconstandardsptp; Kuka.IsGlobalPoint=False; Kuka.PointName=P{nPos}; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=PDAT{nPos}; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT1; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                                src.write(r';ENDFOLD' '\n')
                                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#PreDefinition, WDAT{nPos}) DO ArcMainNG(#PreDefinition, WDAT{nPos}, WP{nPos}) PRIO = -1' '\n')
                                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#GasPreflow, WDAT{nPos}) DO ArcMainNG(#GasPreflow, WDAT{nPos}, WP{nPos}) PRIO = -1' '\n')
                                src.write(fr'ArcMainNG(#ArcOnBeforeSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(fr'SPTP XP{nPos} WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FP{nPos}), $BASE = SBASE(FP{nPos}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{nPos}.IPO_FRAME), $LOAD = SLOAD(FP{nPos}.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PPDAT{nPos}), $APO = SAPO_PTP(PPDAT{nPos}), $GEAR_JERK[1] = SGEAR_JERK(PPDAT{nPos}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
                                src.write(fr'ArcMainNG(#ArcOnAfterSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(r';ENDFOLD' '\n\n')

                                dat.write(fr'DECL stArcDat_T WDAT{nPos}={{WdatId[] "WDAT{nPos}",Strike {{JobModeId[] "SLAVE",ParamSetId[] "Set7",StartTime 0.0,PreFlowTime 0.0,Channel1 0.0,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 10.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,PurgeTime 0.0}},Weld {{JobModeId[] "Job mode",ParamSetId[] "Set2",Velocity {(tool_speed/60):.6f},Channel1 0.0,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 10.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                                dat.write(fr'DECL stArcDat_T WP{nPos}={{WdatId[] "WP{nPos}",Info {{Version 303030366}},Strike {{SeamName[] " ",PartName[] " ",SeamNumber 0,PartNumber 0,DesiredLength 0.0,LengthTolNeg 0.0,LengthTolPos 0.0,LengthCtrlActive FALSE}},Advanced {{BitCodedRobotMark 0}}}}' '\n')
                                dat.write(fr'DECL FRAME XP{nPos}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                                dat.write(fr'DECL FDAT FP{nPos}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                                dat.write(fr'DECL PDAT PPDAT{nPos}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n')
                            elif n == len(interpoints)-1: # arc off
                                src.write(fr';FOLD ARCOFF WDAT{nPos} SLIN P{nPos} CPDAT{nPos} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                                src.write(r';FOLD Parameters ;%{h}' '\n')
                                src.write(fr';Params IlfProvider=kukaroboter.arctech.arcoffstandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{nPos}; Kuka.BlendingEnabled=False; Kuka.MoveDataName=CPDAT{nPos}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{nPos}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                                src.write(r';ENDFOLD' '\n')
                                src.write(fr'TRIGGER WHEN PATH = ArcGetPath(#ArcOffBefore, WDAT{nPos}) DELAY = 0 DO ArcMainNG(#ArcOffBeforeOffSplSingle, WDAT{nPos}, WP{nPos}) PRIO = -1' '\n')
                                src.write(fr'TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOff, WDAT{nPos}) DELAY = 0 DO ArcMainNG(#ArcOffSplSingle, WDAT{nPos}, WP{nPos}) PRIO = -1' '\n')
                                src.write(fr'ArcMainNG(#ArcOffBeforeSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(fr'SLIN XP{nPos} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{nPos}), $TOOL = STOOL2(FP{nPos}), $BASE = SBASE(FP{nPos}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{nPos}.IPO_FRAME), $LOAD = SLOAD(FP{nPos}.TOOL_NO), $ACC = SACC_CP(LCPDAT{nPos}), $ORI_TYPE = SORI_TYP(LCPDAT{nPos}), $APO = SAPO(LCPDAT{nPos}), $JERK = SJERK(LCPDAT{nPos}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
                                src.write(fr'ArcMainNG(#ArcOffAfterSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(r';ENDFOLD' '\n\n')

                                dat.write(fr'DECL stArcDat_T WDAT{nPos}={{WdatId[] "WDAT{nPos}",Crater {{JobModeId[] "SLAVE",ParamSetId[] "Set9",CraterTime 0.0,PostflowTime 0.0,Channel1 0.0,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 10.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,BurnBackTime 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                                dat.write(fr'DECL stArcDat_T WP{nPos}={{WdatId[] "WP{nPos}",Info {{Version 303030366}}}}' '\n')
                                dat.write(fr'DECL FRAME XP{nPos}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                                dat.write(fr'DECL FDAT FP{nPos}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                                dat.write(fr'DECL LDAT LCPDAT{nPos}={{VEL 2.00000,ACC 100.000,APO_DIST 100.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n')
                            else: # arc switch
                                src.write(fr';FOLD ARCSWI WDAT{nPos} SLIN P{nPos} CPDAT{nPos} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                                src.write(r';FOLD Parameters ;%{h}' '\n')
                                src.write(fr';Params IlfProvider=kukaroboter.arctech.arcswistandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{nPos}; Kuka.BlendingEnabled=True; Kuka.MoveDataName=CPDAT{nPos}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{nPos}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                                src.write(r';ENDFOLD' '\n')
                                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = 0 DO ArcMainNG(#ArcSwiSplSingle, WDAT{nPos}, WP{nPos}) PRIO = -1' '\n')
                                src.write(fr'ArcMainNG(#ArcSwiBeforeSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(fr'SLIN XP{nPos} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{nPos}), $TOOL = STOOL2(FP{nPos}), $BASE = SBASE(FP{nPos}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{nPos}.IPO_FRAME), $LOAD = SLOAD(FP{nPos}.TOOL_NO), $ACC = SACC_CP(LCPDAT{nPos}), $ORI_TYPE = SORI_TYP(LCPDAT{nPos}), $APO = SAPO(LCPDAT{nPos}), $JERK = SJERK(LCPDAT{nPos}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0) C_Spl' '\n')
                                src.write(fr'ArcMainNG(#ArcSwiAfterSplSingle, WDAT{nPos}, WP{nPos})' '\n')
                                src.write(r';ENDFOLD' '\n\n')

                                dat.write(fr'DECL stArcDat_T WDAT{nPos}={{WdatId[] "WDAT{nPos}",Weld {{JobModeId[] "SLAVE",ParamSetId[] "Set8",Velocity {(tool_speed/60):.6f},Channel1 0.0,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                                dat.write(fr'DECL stArcDat_T WP{nPos}={{WdatId[] "WP{nPos}",Info {{Version 303030366}}}}' '\n')
                                dat.write(fr'DECL FRAME XP{nPos}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                                dat.write(fr'DECL FDAT FP{nPos}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                                dat.write(fr'DECL LDAT LCPDAT{nPos}={{VEL 2.00000,ACC 100.000,APO_DIST 5.00000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n')

        # last PTP
        src.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
        src.write(r';FOLD Parameters ;%{h}' '\n')
        src.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
        src.write(r';ENDFOLD' '\n')
        src.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
        src.write(r';ENDFOLD' '\n\n')

        # end arguments
        src.write('END')
        dat.write('ENDDAT')

    def to_txt(self):
        """
        Save paths on separate text files
        """

        i = 0
        for slice_obj in self.slice_data:

            if slice_obj is not None:
                j = 0
                for outline in slice_obj.paths:
                    for path in outline:
                        np.savetxt(os.path.join(self.work_dir_path.text(),  "%s_%i_%i.txt"%(self.prefix.text(),i,j)),path)
                        j+=1
            i+=1
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = export_widget(None, None)
    sys.exit(app.exec_())