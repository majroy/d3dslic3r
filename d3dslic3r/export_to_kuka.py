import numpy as np
from d3dslic3r.d3dslic3r_common import respace_equally
import matplotlib.pyplot as plt
from natsort import natsorted
import os

# locate exported slices
path = 'slice_export'
dir_list = os.listdir(path)
file_name = dir_list[0].partition('_')[0]

# write a kuka .SRC and .DAT file
src = open(f'{file_name}.src','w')
dat = open(f'{file_name}.dat','w')

# write strings for header
src.write(f'DEF {file_name}( )' '\n')
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

dat.write(f'DEFDAT  {file_name}' '\n')
dat.write(r';FOLD EXTERNAL DECLARATIONS;%{PE}%MKUKATPBASIS,%CEXT,%VCOMMON,%P' '\n')
dat.write(r';FOLD BASISTECH EXT;%{PE}%MKUKATPBASIS,%CEXT,%VEXT,%P' '\n')
dat.write(r'EXT  BAS (BAS_COMMAND  :IN,REAL  :IN )' '\n')
dat.write(r'DECL INT SUCCESS' '\n')
dat.write(r';ENDFOLD (BASISTECH EXT)' '\n')
dat.write(r';FOLD USER EXT;%{E}%MKUKATPUSER,%CEXT,%VEXT,%P' '\n')
dat.write(r';Make your modifications here' '\n' '\n')
dat.write(r';ENDFOLD (USER EXT)' '\n')
dat.write(r';ENDFOLD (EXTERNAL DECLARATIONS)' '\n\n')

# define zero position X, Y and Z
zero_pos =np.array([1200, -700, 1000])
tool_angle = np.array([0, 90, 0])
tool_speed = 100 # m/min

# write base origin
src.write(fr'BASE_DATA[1] = {{X {zero_pos[0]},Y {zero_pos[1]}, Z {zero_pos[2]}, A 0,B 0,C 0}}' '\n\n')

# write first PTP
src.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
src.write(r';FOLD Parameters ;%{h}' '\n')
src.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
src.write(r';ENDFOLD' '\n')
src.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
src.write(r';ENDFOLD' '\n\n')

# get exported files from d3dslic3r
j = 1
for file in natsorted(dir_list):
    if file[-6:] == '_0.txt': # only outlines
        A = np.genfromtxt(path + '/' + file)
        xycoords = np.delete(A, 2, axis=1)

        # respace the points and include z vals (fixed)
        interpoints, perimeter, nPts = respace_equally(xycoords, 5.00)
        interpoints = np.insert(interpoints, 2, A[0,2], axis=1)

        # plot
        plt.plot(interpoints[:,0], interpoints[:,1], '.')
        #plt.show()

        # for every point write the arc command and position
        for i, points in enumerate(interpoints):
            if i == 0: # arc on
                src.write(fr';FOLD ARCON WDAT{j} SPTP P{j} Vel=100 % PDAT{j} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                src.write(r';FOLD Parameters ;%{h}' '\n')
                src.write(fr';Params IlfProvider=kukaroboter.arctech.arconstandardsptp; Kuka.IsGlobalPoint=False; Kuka.PointName=P{j}; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=PDAT{j}; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT1; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                src.write(r';ENDFOLD' '\n')
                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#PreDefinition, WDAT{j}) DO ArcMainNG(#PreDefinition, WDAT{j}, WP{j}) PRIO = -1' '\n')
                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#GasPreflow, WDAT{j}) DO ArcMainNG(#GasPreflow, WDAT{j}, WP{j}) PRIO = -1' '\n')
                src.write(fr'ArcMainNG(#ArcOnBeforeSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(fr'SPTP XP{j} WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FP{j}), $BASE = SBASE(FP{j}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{j}.IPO_FRAME), $LOAD = SLOAD(FP{j}.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PPDAT{j}), $APO = SAPO_PTP(PPDAT{j}), $GEAR_JERK[1] = SGEAR_JERK(PPDAT{j}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
                src.write(fr'ArcMainNG(#ArcOnAfterSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(r';ENDFOLD' '\n\n')

                dat.write(fr'DECL stArcDat_T WDAT{j}={{WdatId[] "WDAT1",Strike {{JobModeId[] "Job mode",ParamSetId[] "Set1",StartTime 0.0,PreFlowTime 0.0,Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,PurgeTime 0.0}},Weld {{JobModeId[] "Job mode",ParamSetId[] "Set2",Velocity {(tool_speed/60):.6f},Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                dat.write(fr'DECL stArcDat_T WP{j}={{WdatId[] "WP{j}",Info {{Version 303030366}},Strike {{SeamName[] " ",PartName[] " ",SeamNumber 0,PartNumber 0,DesiredLength 0.0,LengthTolNeg 0.0,LengthTolPos 0.0,LengthCtrlActive FALSE}},Advanced {{BitCodedRobotMark 0}}}}' '\n')
                dat.write(fr'DECL FRAME XP{j}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                dat.write(fr'DECL FDAT FP{j}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                dat.write(fr'DECL PDAT PPDAT{j}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')

            elif i == len(interpoints)-1: # arc off
                src.write(fr';FOLD ARCOFF WDAT{j} SLIN P{j} CPDAT{j} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                src.write(r';FOLD Parameters ;%{h}' '\n')
                src.write(fr';Params IlfProvider=kukaroboter.arctech.arcoffstandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{j}; Kuka.BlendingEnabled=False; Kuka.MoveDataName=CPDAT{j}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{j}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                src.write(r';ENDFOLD' '\n')
                src.write(fr'TRIGGER WHEN PATH = ArcGetPath(#ArcOffBefore, WDAT{j}) DELAY = 0 DO ArcMainNG(#ArcOffBeforeOffSplSingle, WDAT{j}, WP{j}) PRIO = -1' '\n')
                src.write(fr'TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOff, WDAT{j}) DELAY = 0 DO ArcMainNG(#ArcOffSplSingle, WDAT{j}, WP{j}) PRIO = -1' '\n')
                src.write(fr'ArcMainNG(#ArcOffBeforeSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(fr'SLIN XP{j} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{j}), $TOOL = STOOL2(FP{j}), $BASE = SBASE(FP{j}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{j}.IPO_FRAME), $LOAD = SLOAD(FP{j}.TOOL_NO), $ACC = SACC_CP(LCPDAT{j}), $ORI_TYPE = SORI_TYP(LCPDAT{j}), $APO = SAPO(LCPDAT{j}), $JERK = SJERK(LCPDAT{j}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
                src.write(fr'ArcMainNG(#ArcOffAfterSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(r';ENDFOLD' '\n\n')

                dat.write(fr'DECL stArcDat_T WDAT{j}={{WdatId[] "WDAT{j}",Crater {{JobModeId[] "Job mode",ParamSetId[] "Set3",CraterTime 0.0,PostflowTime 0.0,Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,BurnBackTime 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                dat.write(fr'DECL stArcDat_T WP{j}={{WdatId[] "WP{j}",Info {{Version 303030366}}}}' '\n')
                dat.write(fr'DECL FRAME XP{j}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                dat.write(fr'DECL FDAT FP{j}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                dat.write(fr'DECL LDAT LCPDAT{j}={{VEL 2.00000,ACC 100.000,APO_DIST 100.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')

            else: # arc switch
                src.write(fr';FOLD ARCSWI WDAT{j} SLIN P{j} CPDAT{j} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
                src.write(r';FOLD Parameters ;%{h}' '\n')
                src.write(fr';Params IlfProvider=kukaroboter.arctech.arcswistandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{j}; Kuka.BlendingEnabled=True; Kuka.MoveDataName=CPDAT{j}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{j}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
                src.write(r';ENDFOLD' '\n')
                src.write(fr'TRIGGER WHEN DISTANCE = 1 DELAY = 0 DO ArcMainNG(#ArcSwiSplSingle, WDAT{j}, WP{j}) PRIO = -1' '\n')
                src.write(fr'ArcMainNG(#ArcSwiBeforeSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(fr'SLIN XP{j} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{j}), $TOOL = STOOL2(FP{j}), $BASE = SBASE(FP{j}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{j}.IPO_FRAME), $LOAD = SLOAD(FP{j}.TOOL_NO), $ACC = SACC_CP(LCPDAT{j}), $ORI_TYPE = SORI_TYP(LCPDAT{j}), $APO = SAPO(LCPDAT{j}), $JERK = SJERK(LCPDAT{j}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0) C_Spl' '\n')
                src.write(fr'ArcMainNG(#ArcSwiAfterSplSingle, WDAT{j}, WP{j})' '\n')
                src.write(r';ENDFOLD' '\n\n')

                dat.write(fr'DECL stArcDat_T WDAT{j}={{WdatId[] "WDAT{j}",Weld {{JobModeId[] "Job mode",ParamSetId[] "Set2",Velocity {(tool_speed/60):.6f},Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
                dat.write(fr'DECL stArcDat_T WP{j}={{WdatId[] "WP{j}",Info {{Version 303030366}}}}' '\n')
                dat.write(fr'DECL FRAME XP{j}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
                dat.write(fr'DECL FDAT FP{j}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
                dat.write(fr'DECL LDAT LCPDAT{j}={{VEL 2.00000,ACC 100.000,APO_DIST 5.00000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')
            j += 1

# last PTP
src.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
src.write(r';FOLD Parameters ;%{h}' '\n')
src.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
src.write(r';ENDFOLD' '\n')
src.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
src.write(r';ENDFOLD' '\n\n')

# close off
src.write('END')
dat.write('ENDDAT')