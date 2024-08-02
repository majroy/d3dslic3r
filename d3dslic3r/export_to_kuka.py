import numpy as np
from d3dslic3r_common import respace_equally
import matplotlib.pyplot as plt

# import outline already ordered
A = np.genfromtxt('slice_export/Slice_0_0.txt')

# obtain only x and y coords
xycoords = np.delete(A, 2, axis=1)

# respace the points and include z vals (fixed)
interpoints, perimeter, nPts = respace_equally(xycoords, 5.00)
interpoints = np.insert(interpoints, 2, A[0,2], axis=1)

plt.plot(interpoints[:,0], interpoints[:,1], '.')
#plt.show()

# write a kuka .SRC and .DAT file
file_name = 'BunnyProfile'
fs = open(f'{file_name}.src','w')
fd = open(f'{file_name}.dat','w')

# define zero position X, Y and Z
zero_pos =np.array([1200, -700, 1000])
tool_angle = np.array([0, 90, 0])
tool_speed = 100 # m/min

# write strings for header
fs.write(f'DEF {file_name}( )' '\n')
fs.write(r';FOLD INI;%{PE}' '\n')
fs.write(r'  ;FOLD BASISTECH INI' '\n')
fs.write(r'    GLOBAL INTERRUPT DECL 3 WHEN $STOPMESS==TRUE DO IR_STOPM ( )' '\n')
fs.write(r'    INTERRUPT ON 3' '\n') 
fs.write(r'    BAS (#INITMOV,0 )' '\n')
fs.write(r'  ;ENDFOLD (BASISTECH INI)' '\n')
fs.write(r'  ;FOLD USER INI' '\n')
fs.write(r'    ;Make your modifications here' '\n' '\n')
fs.write(r'  ;ENDFOLD (USER INI)' '\n')
fs.write(r';ENDFOLD (INI)' '\n\n')

fd.write(f'DEFDAT  {file_name}' '\n')
fd.write(r';FOLD EXTERNAL DECLARATIONS;%{PE}%MKUKATPBASIS,%CEXT,%VCOMMON,%P' '\n')
fd.write(r';FOLD BASISTECH EXT;%{PE}%MKUKATPBASIS,%CEXT,%VEXT,%P' '\n')
fd.write(r'EXT  BAS (BAS_COMMAND  :IN,REAL  :IN )' '\n')
fd.write(r'DECL INT SUCCESS' '\n')
fd.write(r';ENDFOLD (BASISTECH EXT)' '\n')
fd.write(r';FOLD USER EXT;%{E}%MKUKATPUSER,%CEXT,%VEXT,%P' '\n')
fd.write(r';Make your modifications here' '\n' '\n')
fd.write(r';ENDFOLD (USER EXT)' '\n')
fd.write(r';ENDFOLD (EXTERNAL DECLARATIONS)' '\n\n')

# write base origin
fs.write(fr'BASE_DATA[1] = {{X {zero_pos[0]},Y {zero_pos[1]}, Z {zero_pos[2]}, A 0,B 0,C 0}}' '\n\n')

# write first PTP
fs.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
fs.write(r';FOLD Parameters ;%{h}' '\n')
fs.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
fs.write(r';ENDFOLD' '\n')
fs.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
fs.write(r';ENDFOLD' '\n\n')

for i, points in enumerate(interpoints):
    
    if i == 0: # write arc on
        fs.write(fr';FOLD ARCON WDAT{i+1} SPTP P{i+1} Vel=100 % PDAT{i+1} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
        fs.write(r';FOLD Parameters ;%{h}' '\n')
        fs.write(fr';Params IlfProvider=kukaroboter.arctech.arconstandardsptp; Kuka.IsGlobalPoint=False; Kuka.PointName=P{i+1}; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=PDAT{i+1}; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT1; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
        fs.write(r';ENDFOLD' '\n')
        fs.write(fr';TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#PreDefinition, WDAT{i+1}) DO ArcMainNG(#PreDefinition, WDAT{i+1}, WP{i+1}) PRIO = -1' '\n')
        fs.write(fr';TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#GasPreflow, WDAT{i+1}) DO ArcMainNG(#GasPreflow, WDAT{i+1}, WP{i+1}) PRIO = -1' '\n')
        fs.write(fr';ArcMainNG(#ArcOnBeforeSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(fr'SPTP XP{i+1} WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FP{i+1}), $BASE = SBASE(FP{i+1}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{i+1}.IPO_FRAME), $LOAD = SLOAD(FP{i+1}.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PPDAT{i+1}), $APO = SAPO_PTP(PPDAT{i+1}), $GEAR_JERK[1] = SGEAR_JERK(PPDAT{i+1}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
        fs.write(fr';ArcMainNG(#ArcOnAfterSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(r';ENDFOLD' '\n\n')

        fd.write(fr'DECL stArcDat_T WDAT{i+1}={{WdatId[] "WDAT1",Strike {{JobModeId[] "Job mode",ParamSetId[] "Set1",StartTime 0.0,PreFlowTime 0.0,Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,PurgeTime 0.0}},Weld {{JobModeId[] "Job mode",ParamSetId[] "Set2",Velocity {(tool_speed/60):.6f},Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
        fd.write(fr'DECL stArcDat_T WP{i+1}={{WdatId[] "WP{i+1}",Info {{Version 303030366}},Strike {{SeamName[] " ",PartName[] " ",SeamNumber 0,PartNumber 0,DesiredLength 0.0,LengthTolNeg 0.0,LengthTolPos 0.0,LengthCtrlActive FALSE}},Advanced {{BitCodedRobotMark 0}}}}' '\n')
        fd.write(fr'DECL FRAME XP{i+1}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
        fd.write(fr'DECL FDAT FP{i+1}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
        fd.write(fr'DECL PDAT PPDAT{i+1}={{VEL 100.000,ACC 100.000,APO_DIST 500.000,APO_MODE #CDIS,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')

    elif i == len(A)-1:
        # write arc off
        fs.write(fr';FOLD ARCOFF WDAT{i+1} SLIN P{i+1} CPDAT{i+1} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
        fs.write(r';FOLD Parameters ;%{h}' '\n')
        fs.write(fr';Params IlfProvider=kukaroboter.arctech.arcoffstandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{i+1}; Kuka.BlendingEnabled=False; Kuka.MoveDataName=CPDAT{i+1}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{i+1}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
        fs.write(r';ENDFOLD' '\n')
        fs.write(fr';TRIGGER WHEN PATH = ArcGetPath(#ArcOffBefore, WDAT{i+1}) DELAY = 0 DO ArcMainNG(#ArcOffBeforeOffSplSingle, WDAT{i+1}, WP{i+1}) PRIO = -1' '\n')
        fs.write(fr';TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOff, WDAT{i+1}) DELAY = 0 DO ArcMainNG(#ArcOffSplSingle, WDAT{i+1}, WP{i+1}) PRIO = -1' '\n')
        fs.write(fr';ArcMainNG(#ArcOffBeforeSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(fr'SLIN XP{i+1} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{i+1}), $TOOL = STOOL2(FP{i+1}), $BASE = SBASE(FP{i+1}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{i+1}.IPO_FRAME), $LOAD = SLOAD(FP{i+1}.TOOL_NO), $ACC = SACC_CP(LCPDAT{i+1}), $ORI_TYPE = SORI_TYP(LCPDAT{i+1}), $APO = SAPO(LCPDAT{i+1}), $JERK = SJERK(LCPDAT{i+1}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
        fs.write(fr';ArcMainNG(#ArcOffAfterSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(r';ENDFOLD' '\n\n')

        fd.write(fr'DECL stArcDat_T WDAT3={{WdatId[] "WDAT{i+1}",Crater {{JobModeId[] "Job mode",ParamSetId[] "Set3",CraterTime 0.0,PostflowTime 0.0,Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,BurnBackTime 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
        fd.write(fr'DECL stArcDat_T WP{i+1}={{WdatId[] "WP{i+1}",Info {{Version 303030366}}}}' '\n')
        fd.write(fr'DECL FRAME XP{i+1}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
        fd.write(fr'DECL FDAT FP{i+1}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
        fd.write(fr'DECL LDAT LCPDAT{i+1}={{VEL 2.00000,ACC 100.000,APO_DIST 100.000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')

    else:
        # write arc switch
        fs.write(fr';FOLD ARCSWI WDAT{i+1} SLIN P{i+1} CPDAT{i+1} Tool[1]:Welder Base[1] ;%{{PE}}' '\n')
        fs.write(r';FOLD Parameters ;%{h}' '\n')
        fs.write(fr';Params IlfProvider=kukaroboter.arctech.arcswistandardslin; Kuka.IsGlobalPoint=False; Kuka.PointName=P{i+1}; Kuka.BlendingEnabled=True; Kuka.MoveDataName=CPDAT{i+1}; Kuka.VelocityFieldEnabled=False; Kuka.ColDetectFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=; ArcTech.WdatVarName=WDAT{i+1}; ArcTech.Basic=3.3.3.366; ArcTech.Advanced=3.3.1.22' '\n')
        fs.write(r';ENDFOLD' '\n')
        fs.write(fr';TRIGGER WHEN DISTANCE = 1 DELAY = 0 DO ArcMainNG(#ArcSwiSplSingle, WDAT{i+1}, WP{i+1}) PRIO = -1' '\n')
        fs.write(fr';ArcMainNG(#ArcSwiBeforeSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(fr'SLIN XP{i+1} WITH $VEL = SVEL_CP(gArcBasVelDefinition, , LCPDAT{i+1}), $TOOL = STOOL2(FP{i+1}), $BASE = SBASE(FP{i+1}.BASE_NO), $IPO_MODE = SIPO_MODE(FP{i+1}.IPO_FRAME), $LOAD = SLOAD(FP{i+1}.TOOL_NO), $ACC = SACC_CP(LCPDAT{i+1}), $ORI_TYPE = SORI_TYP(LCPDAT{i+1}), $APO = SAPO(LCPDAT{i+1}), $JERK = SJERK(LCPDAT{i+1}), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0) C_Spl' '\n')
        fs.write(fr';ArcMainNG(#ArcSwiAfterSplSingle, WDAT{i+1}, WP{i+1})' '\n')
        fs.write(r';ENDFOLD' '\n\n')

        fd.write(fr'DECL stArcDat_T WDAT{i+1}={{WdatId[] "WDAT{i+1}",Weld {{JobModeId[] "Job mode",ParamSetId[] "Set2",Velocity {(tool_speed/60):.6f},Channel1 1.00000,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0}},Weave {{Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0}},Advanced {{IgnitionErrorStrategy 1,WeldErrorStrategy 1,SlopeOption #None,SlopeTime 0.0,SlopeDistance 0.0,OnTheFlyActiveOn FALSE,OnTheFlyActiveOff FALSE,OnTheFlyDistanceOn 0.0,OnTheFlyDistanceOff 0.0}}}}' '\n')
        fd.write(fr'DECL stArcDat_T WP{i+1}={{WdatId[] "WP{i+1}",Info {{Version 303030366}}}}' '\n')
        fd.write(fr'DECL FRAME XP{i+1}={{X {points[0]:.6f},Y {points[1]:.6f},Z {points[2]:.6f},A {tool_angle[0]:.6f},B {tool_angle[1]:.6f},C {tool_angle[2]:.6f}}}' '\n')
        fd.write(fr'DECL FDAT FP{i+1}={{TOOL_NO 1,BASE_NO 1,IPO_FRAME #BASE,POINT2[] " "}}' '\n')
        fd.write(fr'DECL LDAT LCPDAT{i+1}={{VEL 2.00000,ACC 100.000,APO_DIST 5.00000,APO_FAC 50.0000,AXIS_VEL 100.000,AXIS_ACC 100.000,ORI_TYP #VAR,CIRC_TYP #BASE,JERK_FAC 50.0000,GEAR_JERK 100.000,EXAX_IGN 0}}' '\n\n')

# last PTP
fs.write(r';FOLD SPTP HOME Vel=100 % DEFAULT ;%{PE}' '\n')
fs.write(r';FOLD Parameters ;%{h}' '\n')
fs.write(r';Params IlfProvider=kukaroboter.basistech.inlineforms.movement.spline; Kuka.IsGlobalPoint=False; Kuka.PointName=HOME; Kuka.BlendingEnabled=False; Kuka.MoveDataPtpName=DEFAULT; Kuka.VelocityPtp=100; Kuka.VelocityFieldEnabled=True; Kuka.CurrentCDSetIndex=0; Kuka.MovementParameterFieldEnabled=True; IlfCommand=SPTP' '\n')
fs.write(r';ENDFOLD' '\n')
fs.write(r'SPTP XHOME WITH $VEL_AXIS[1] = SVEL_JOINT(100.0), $TOOL = STOOL2(FHOME), $BASE = SBASE(FHOME.BASE_NO), $IPO_MODE = SIPO_MODE(FHOME.IPO_FRAME), $LOAD = SLOAD(FHOME.TOOL_NO), $ACC_AXIS[1] = SACC_JOINT(PDEFAULT), $APO = SAPO_PTP(PDEFAULT), $GEAR_JERK[1] = SGEAR_JERK(PDEFAULT), $COLLMON_TOL_PRO[1] = USE_CM_PRO_VALUES(0)' '\n')
fs.write(r';ENDFOLD' '\n\n')

# close off
fs.write('END')
fd.write('ENDDAT')