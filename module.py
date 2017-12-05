import math
import sys
import os
import errno

from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup

from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from sketch import *
from connectorBehavior import *
from textRepr import *

def tube_setup(myModel,indrad,orad,irad,presf,mod,v,tlenb,tlenf):
	tlen = tlenb+tlenf
	tpart = 0.5
	con = indrad*1.5 #Contact area length in X direction
        side = indrad*2.5 #Contact area length in Z direction

	yo_edge = orad*math.cos(math.asin(con/orad))
	yi_edge = irad*math.cos(math.asin(con/irad))

	yo_mid =  orad*math.cos(math.asin(con*0.5/orad))
	yi_mid =  irad*math.cos(math.asin(con*0.5/irad))

	yt_mid =  (orad-1e-5)*math.cos(math.asin(con/(orad-1e-5)))
	yc_mid =  (orad-1e-5)*math.cos(math.asin(con*0.5/(orad-1e-5)))

	# Tube 
	mySketch = myModel.ConstrainedSketch(name='__profile__', sheetSize=0.2)
	mySketch.ArcByCenterEnds(center=(0.0, 0.0), direction=CLOCKWISE, point1=(0.0, orad), point2=(0.0, -orad))
	mySketch.ArcByCenterEnds(center=(0.0, 0.0), direction=CLOCKWISE, point1=(0.0, irad), point2=(0.0, -irad))
	mySketch.Line(point1=(0.0, orad), point2=(0.0, irad))
	mySketch.Line(point1=(0.0, -irad), point2=(0.0, -orad))
	myPart1b = myModel.Part(dimensionality=THREE_D, name='tubeb', type=DEFORMABLE_BODY)
	myPart1b.BaseSolidExtrude(depth=tlenb, sketch=mySketch)
	myPart1f = myModel.Part(dimensionality=THREE_D, name='tubef', type=DEFORMABLE_BODY)
	myPart1f.BaseSolidExtrude(depth=tlenf, sketch=mySketch)
        del mySketch
		
	# Partitions
	id = myPart1b.DatumPointByEdgeParam(edge=myPart1b.edges[3], parameter=tpart).id
	myPart1b.PartitionCellByPlanePointNormal(cells=myPart1b.cells.findAt(((0.0,orad,tlenb),)) 
    	, normal=myPart1b.edges[3], point=myPart1b.datums[id])

	dp1 = myPart1f.DatumPlaneByPrincipalPlane(offset=con, principalPlane=YZPLANE).id
	myPart1f.PartitionCellByDatumPlane(cells=myPart1f.cells.findAt(((0.0,orad,0.0),)), datumPlane=myPart1f.datums[dp1])

	dp2 = myPart1f.DatumPlaneByPrincipalPlane(offset=tlenf*0.5-side, principalPlane=XYPLANE).id
	dp3 = myPart1f.DatumPlaneByPrincipalPlane(offset=tlenf*0.5+side, principalPlane=XYPLANE).id
	myPart1f.PartitionCellByDatumPlane(cells=myPart1f.cells.findAt(((0.0,orad,0.0),),((0.0,-orad,0.0),)), datumPlane=myPart1f.datums[dp2])
	myPart1f.PartitionCellByDatumPlane(cells=myPart1f.cells.findAt(((0.0,orad,tlenf*0.5),),((0.0,-orad,tlenf*0.5),)), datumPlane=myPart1f.datums[dp3])

	# Hemisphere
	mySketch = myModel.ConstrainedSketch(name='__profile__', sheetSize=0.2)
	mySketch.ConstructionLine(point1=(0.0, -0.1), point2=(0.0, 0.1))
	mySketch.ArcByCenterEnds(center=(0.0, 0.0), direction=CLOCKWISE, point1=(0.0, orad), point2=(orad, 0.0))
	mySketch.ArcByCenterEnds(center=(0.0, 0.0), direction=CLOCKWISE, point1=(0.0, irad), point2=(irad, 0.0))
	
	mySketch.Line(point1=(orad, 0.0), point2=(irad, 0.0))
	mySketch.Line(point1=(0.0, orad), point2=(0.0, irad))
	myPart2 = myModel.Part(dimensionality=THREE_D, name='hemi', type=DEFORMABLE_BODY)
	myPart2.BaseSolidRevolve(angle=180.0, flipRevolveDirection=OFF, sketch=mySketch)
	del mySketch

        dp4 = myPart2.DatumPlaneByPrincipalPlane(offset=0.0, principalPlane=YZPLANE).id
        myPart2.PartitionCellByDatumPlane(cells=myPart2.cells[0:1], datumPlane=myPart2.datums[dp4])

	# Material properties
	myModel.Material(name='Pollen')
	myModel.materials['Pollen'].Elastic(table=((mod, v), ))
	
	myModel.HomogeneousSolidSection(material='Pollen', name='hemiSec', thickness=None)
	myModel.HomogeneousSolidSection(material='Pollen', name='tubeSec', thickness=None)

	myPart1b.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
		cells=myPart1b.cells[0:2]), sectionName='tubeSec', thicknessAssignment=FROM_SECTION)
	myPart1f.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
		cells=myPart1f.cells[0:7]), sectionName='tubeSec', thicknessAssignment=FROM_SECTION)
	myPart2.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
		cells=myPart2.cells[0:2]), sectionName='hemiSec', thicknessAssignment=FROM_SECTION)

	# Assembly
	myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)

	myModel.rootAssembly.Instance(dependent=ON, name='tubeb-1', part=myPart1b)
	myModel.rootAssembly.rotate(angle=180.0, axisDirection=(0.0, orad, 0.0), axisPoint=(0.0, orad, 0.0), instanceList=('tubeb-1',))
	myModel.rootAssembly.rotate(angle=180.0, axisDirection=(0.0, 0.0, orad), axisPoint=(0.0, 0.0, orad), instanceList=('tubeb-1',))
	myModel.rootAssembly.translate(instanceList=('tubeb-1', ), vector=(0, 0, tlen))

	myModel.rootAssembly.Instance(dependent=ON, name='tubef-1', part=myPart1f)
	myModel.rootAssembly.translate(instanceList=('tubef-1', ), vector=(0, 0, 0))

        myModel.rootAssembly.Instance(dependent=ON, name='hemi-1', part=myPart2)
	myModel.rootAssembly.rotate(angle=-90.0, axisDirection=(1,0,0), axisPoint=(0.5, 0.0, 0.0), instanceList=('hemi-1',))
	myModel.rootAssembly.rotate(angle=90.0, axisDirection=(0.0, 0.0, -(tlen+orad)), axisPoint=(0.0, 0.0, tlen+orad), instanceList=('hemi-1',))
	myModel.rootAssembly.translate(instanceList=('hemi-1', ), vector=(0, 0, 0))

	# Surface definition
	myPart1b.Surface(name='innTubeb', side1Faces=myPart1b.faces.findAt(((irad,0,0.5*tlenb),),((irad,0,(tpart+0.1)*tlenb),)))
	myPart1b.Surface(name='outTubeb', side1Faces=myPart1b.faces.findAt(((orad,0,0.5*tlenb),),((orad,0,(tpart+0.1)*tlenb),)))
        myPart1f.Surface(name='outTubef', side1Faces=myPart1f.faces.findAt(((1e-5,orad,0.5*tlenf),),((1e-5,orad,0.75*tlenf),),
		((1e-5,orad,0.25*tlenf),),((1e-5,-orad,0.5*tlenf),),((1e-5,-orad,0.75*tlenf),),((1e-5,-orad,0.25*tlenf),),
		((orad,1e-5,0.5*tlenf),),))
	
	myPart1f.Surface(name='innTubef', side1Faces=myPart1f.faces.findAt(((irad,0,0.5*tlenf),),((1e-5,irad,0.75*tlenf),),
		((1e-5,irad,0.25*tlenf),),((1e-5,irad,0.5*tlenf),),((1e-5,-irad,0.5*tlenf),),((1e-5,-irad,0.25*tlenf),),((1e-5,-irad,0.75*tlenf),)))

	myPart1b.Surface(name='conTubeb1', side1Faces=myPart1b.faces.findAt(((orad-1e-5,0,0),)))
	myPart1b.Surface(name='conTubeb2', side1Faces=myPart1b.faces.findAt(((orad-1e-5,0,tlenb),)))
	myPart1f.Surface(name='conTubef1', side1Faces=myPart1f.faces.findAt(((orad-1e-5,0,0.0),),((con*0.5,yc_mid,0.0),),((con*0.5,-yc_mid,0.0),)))
	myPart1f.Surface(name='conTubef2', side1Faces=myPart1f.faces.findAt(((orad-1e-5,0,tlenf),),((0,orad-1e-5,tlenf),),((0,-(orad-1e-5),tlenf),)))

	myPart2.Surface(name='conHemi2', side1Faces=myPart2.faces.findAt(((1e-5,0.0,orad-4e-5),),((-1e-5,0.0,orad-4e-5),)))

	myPart2.Surface(name='innHemi', side1Faces=myPart2.faces.findAt(((irad/sqrt(2),1e-5,irad/sqrt(2)),),((-irad/sqrt(2),1e-5,irad/sqrt(2)),)))

	# Set definition
	myPart1b.Set(name='sym_tubeb',faces=myPart1b.faces.findAt(((0,-(orad-1e-5),(tpart-0.1)*tlenb),),((0,(orad-1e-5),(tpart-0.1)*tlenb),),
		((0,-(orad-1e-5),(tpart+0.1)*tlenb),),((0,(orad-1e-5),(tpart+0.1)*tlenb),)))	
	myPart1f.Set(name='sym_tubef',faces=myPart1f.faces.findAt(((0,-(orad-1e-5),0.5*tlenf),),((0,(orad-1e-5),0.5*tlenf),),
		((0,(orad-1e-5),0.75*tlenf),),((0,(orad-1e-5),0.25*tlenf),),((0,-(orad-1e-5),0.75*tlenf),),((0,-(orad-1e-5),0.25*tlenf),)))

	myPart1b.Set(name='zsym_tubeb', faces=myPart1b.faces.findAt(((orad-1e-5,0,0),)))

	myPart2.Set(name='sym_hemi2',faces=myPart2.faces.findAt(((-1e-5,orad-2e-5,0),),((1e-5,orad-2e-5,0),)))

	# STEP TIME
	myModel.StaticStep(initialInc=0.0005, maxInc=0.05, maxNumInc=1000, minInc=1e-08, name='intPres', nlgeom=ON, previous='Initial', 
		timePeriod=0.5)

        myModel.steps['intPres'].setValues(adaptiveDampingRatio=0.05, continueDampingFactors=False, 
                stabilizationMagnitude=0.0002, stabilizationMethod=DISSIPATED_ENERGY_FRACTION)

	# INTERACTION

	# Tie Constraint
	myModel.Tie(adjust=ON, master=myModel.rootAssembly.instances['tubeb-1'].surfaces['conTubeb2'], name='tubef-tubeb', positionToleranceMethod=
		COMPUTED, slave=myModel.rootAssembly.instances['tubef-1'].surfaces['conTubef2'], thickness=ON, tieRotations=ON)
	myModel.Tie(adjust=ON, master=myModel.rootAssembly.instances['hemi-1'].surfaces['conHemi2'], name='tubef-hemi', positionToleranceMethod=
		COMPUTED, slave=myModel.rootAssembly.instances['tubef-1'].surfaces['conTubef1'], thickness=ON, tieRotations=ON)

	# MESH
	# Tube meshing
	# Z stretch b
	myPart1b.seedEdgeByNumber(constraint=FIXED, edges=myPart1b.edges.findAt(
		((0,orad,(tpart-0.1)*tlenb),),((0,irad,(tpart-0.1)*tlenb),),((0,-orad,(tpart-0.1)*tlenb),),((0,-irad,(tpart-0.1)*tlenb),),
		), number=14)

	myPart1b.seedEdgeByNumber(constraint=FIXED, edges=myPart1b.edges.findAt(
		((0,orad,(tpart+0.1)*tlenb),),((0,irad,(tpart+0.1)*tlenb),),((0,-orad,(tpart+0.1)*tlenb),),((0,-irad,(tpart+0.1)*tlenb),),	
		), number=14)

	myPart1b.seedEdgeByNumber(constraint=FIXED, edges=myPart1b.edges.findAt(
		((orad,0,tlenb),),((irad,0,tlenb),),((orad,0,tpart*tlenb),),((irad,0,tpart*tlenb),),((orad,0,0),),((irad,0,0),),) , number=14)	

	myPart1b.seedEdgeByNumber(constraint=FIXED, edges=myPart1b.edges.findAt(
		((0,orad-1e-5,tlenb),),((0,-(orad-1e-5),tlenb),),((0,orad-1e-5,tpart*tlenb),),((0,-(orad-1e-5),tpart*tlenb),),
		((0,orad-1e-5,0),),((0,orad-1e-5,0),),), number=1)

	myPart1b.setElementType(elemTypes=(ElemType(elemCode=C3D20, elemLibrary=STANDARD), ElemType(elemCode=C3D15, elemLibrary=STANDARD), 
		ElemType(elemCode=C3D10, elemLibrary=STANDARD)), regions=Region(myPart1b.cells[0:2]))
	myPart1b.generateMesh()

	# Z push f

	# Contact area
	# Z top contact
	myPart1f.seedEdgeByBias(biasMethod=DOUBLE, constraint=FIXED, centerEdges=myPart1f.edges.findAt(
		((0,-orad,0.5*tlenf),),((0,-irad,0.5*tlenf),),((con,-yo_edge,0.5*tlenf),),((con,-yi_edge,0.5*tlenf),),
		((0,orad,0.5*tlenf),),((0,irad,0.5*tlenf),),((con,yo_edge,0.5*tlenf),),((con,yi_edge,0.5*tlenf),),) , number=40, ratio=2.0) #40,4.0

	# Z top non-contact
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(
		((0,orad,0.25*tlenf),),((0,irad,0.25*tlenf),),((con,yo_edge,0.25*tlenf),),((con,yi_edge,0.25*tlenf),),
		((0,orad,0.75*tlenf),),((0,irad,0.75*tlenf),),((con,yo_edge,0.75*tlenf),),((con,yi_edge,0.75*tlenf),),) , number=30)

	# Z bot non-contact
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(
		((0,-orad,0.25*tlenf),),((0,-irad,0.25*tlenf),),((con,-yo_edge,0.25*tlenf),),((con,-yi_edge,0.25*tlenf),),
		((0,-orad,0.75*tlenf),),((0,-irad,0.75*tlenf),),((con,-yo_edge,0.75*tlenf),),((con,-yi_edge,0.75*tlenf),),) , number=30)

	# XY curve bot
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(
		((con*0.5,-yo_mid,0),),((con*0.5,-yi_mid,0),),((con*0.5,-yo_mid,tlenf),),((con*0.5,-yi_mid,tlenf),),) , number=3)
	
	# XY curve top contact
	myPart1f.seedEdgeByBias(biasMethod=SINGLE, constraint=FIXED, end2Edges=myPart1f.edges.findAt(
		((con*0.5,yo_mid,tlenf*0.5-side),),((con*0.5,yi_mid,tlenf*0.5-side),),((con*0.5,yo_mid,tlenf*0.5+side),),
		((con*0.5,yi_mid,tlenf*0.5+side),),), number=16, ratio=2.0) #20,4.0

	# XY curve top non-contact
#	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(((con*0.5,yo_mid,0.0),),
#	        ((con*0.5,yi_mid,0.0),),((con*0.5,yo_mid,tlenf),),((con*0.5,yi_mid,tlenf),),), number=3)

	# XY long
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(((orad,0,0.0),),
		((irad,0,0.0),),((orad,0,tlenf),),((irad,0,tlenf),),), number=40)

	# thickness contact
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(
		((0,orad-1e-5,0.5*tlenf+side),),((0,orad-1e-5,0.5*tlenf-side),),((con,yt_mid-1e-5,0.5*tlenf+side),),
		((con,yt_mid-1e-5,0.5*tlenf-side),),), number=2)

	# thickness non-contact
	myPart1f.seedEdgeByNumber(constraint=FIXED, edges=myPart1f.edges.findAt(
		((0,orad-1e-5,tlenf),),((0,-(orad-1e-5),tlenf),),((0,orad-1e-5,0),),((0,-(orad-1e-5),0),), 
		((con,yt_mid-1e-5,tlenf),),((con,-(yt_mid-1e-5),tlenf),),((con,yt_mid-1e-5,0),),((con,-(yt_mid-1e-5),0),),), number=2)

	# Set element type
	myPart1f.setElementType(elemTypes=(ElemType(elemCode=C3D20, elemLibrary=STANDARD), ElemType(elemCode=C3D15, 
    	        elemLibrary=STANDARD), ElemType(elemCode=C3D10, elemLibrary=STANDARD)), regions=(myPart1f.cells.findAt(((orad,0.0,0.5*tlenf),),
    	        ((0,orad,0.25*tlenf),),((0,orad,0.75*tlenf),),), ))
	myPart1f.setElementType(elemTypes=(ElemType(elemCode=C3D20, elemLibrary=STANDARD), ElemType(elemCode=C3D15, 
    	        elemLibrary=STANDARD), ElemType(elemCode=C3D10, elemLibrary=STANDARD)), regions=(myPart1f.cells.findAt(((0,-orad,0.25*tlenf),),
    	        ((0,-orad,0.75*tlenf),),((0,orad,0.5*tlenf),),((0,-orad,0.5*tlenf),),), ))
	myPart1f.generateMesh()

	# Hemi meshing
	myPart2.seedEdgeByNumber(constraint=FINER, edges=myPart2.edges.findAt(
		((-(orad-1e-5),0,0),),((orad-1e-5,0,0),),((0,orad-1e-5,0),),) , number=1)
	
	myPart2.seedEdgeByNumber(constraint=FINER, edges=myPart2.edges.findAt(
		((-orad/sqrt(2),orad/sqrt(2),0),),((orad/sqrt(2),orad/sqrt(2),0),), 
		((-irad/sqrt(2),irad/sqrt(2),0),),((irad/sqrt(2),irad/sqrt(2),0),),), number=20)
	
	myPart2.seedEdgeByNumber(constraint=FINER, edges=myPart2.edges.findAt(((-orad/sqrt(2),0,orad/sqrt(2)),),((orad/sqrt(2),0,orad/sqrt(2)),),)
	        , number=20)

	myPart2.setElementType(elemTypes=(ElemType(elemCode=C3D20, elemLibrary=STANDARD), ElemType(elemCode=C3D15, elemLibrary=STANDARD), 
		ElemType(elemCode=C3D10, elemLibrary=STANDARD)), regions=Region(myPart2.cells[0:2]))
	myPart2.generateMesh()

	# LOAD
	# Symmetry BC
	myModel.XsymmBC(createStepName='Initial', localCsys=None, name='X_sym_tubeb', region=myModel.rootAssembly.instances['tubeb-1'].
		sets['sym_tubeb'])
	myModel.XsymmBC(createStepName='Initial', localCsys=None, name='X_sym_tubef', region=myModel.rootAssembly.instances['tubef-1'].
		sets['sym_tubef'])
#	myModel.XsymmBC(createStepName='Initial', localCsys=None, name='X_sym_hemi1', region=myModel.rootAssembly.instances['hemi-1'].
#		sets['sym_hemi1'])
	myModel.ZsymmBC(createStepName='Initial', localCsys=None, name='Z_sym_tubeb', region=myModel.rootAssembly.instances['tubeb-1'].
		sets['zsym_tubeb'])
	myModel.XsymmBC(createStepName='Initial', localCsys=None, name='X_sym_hemi2', region=myModel.rootAssembly.instances['hemi-1'].
		sets['sym_hemi2'])

	# Tube pressure BC
	myModel.Pressure(amplitude=UNSET, createStepName='intPres', distributionType=UNIFORM, magnitude=presf, name='innTubeb', region=
    	        myModel.rootAssembly.instances['tubeb-1'].surfaces['innTubeb'])
	myModel.Pressure(amplitude=UNSET, createStepName='intPres', distributionType=UNIFORM, magnitude=presf, name='innTubef', region=
    	        myModel.rootAssembly.instances['tubef-1'].surfaces['innTubef'])
	myModel.Pressure(amplitude=UNSET, createStepName='intPres', distributionType=UNIFORM, magnitude=presf, name='innHemi', region=
    	        myModel.rootAssembly.instances['hemi-1'].surfaces['innHemi'])

	# Displacement BC
	myPart1f.Set(name='surfCheck', nodes=myPart1f.nodes.getByBoundingBox(-1e-6,orad-1e-5,0.5*tlenf-side,1501e-6,orad+1e-5,0.5*tlenf+side))
        myPart1f.Set(name='topCheck', nodes=myPart1f.nodes.getByBoundingBox(-1e-6,orad-1e-5,0.5*tlenf-1e-6,1e-6,orad+1e-5,0.5*tlenf+1e-6))
	myPart1f.Set(name='topCheckl', nodes=myPart1f.nodes.getByBoundingBox(-1e-6,irad-1e-5,0.5*tlenf-1e-6,1e-6,irad+1e-5,0.5*tlenf+1e-6))

	myPart2.Set(name='hemiHoldY', nodes=myPart2.nodes.getByBoundingBox(-1e-6,-1e-6,-1e-6,1e-6,orad+1e-6,orad+1e-6))
	myPart1b.Set(name='tubebHoldY', nodes=myPart1b.nodes.getByBoundingBox(irad-1e-6,-1e-6,-1e-6,orad+1e-6,1e-6,tlenb-1e-6))
	myPart1f.Set(name='tubefHoldY', nodes=myPart1f.nodes.getByBoundingBox(irad-1e-6,-1e-6,1e-6,orad+1e-6,1e-6,tlenf-1e-6))

	myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial', distributionType=UNIFORM, localCsys=None, name='YHoldb', 
    	        region=myModel.rootAssembly.instances['tubeb-1'].sets['tubebHoldY'], u1=UNSET, u2=SET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)
	myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial', distributionType=UNIFORM, localCsys=None, name='YHoldf', 
    	        region=myModel.rootAssembly.instances['tubef-1'].sets['tubefHoldY'], u1=UNSET, u2=SET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)	
        myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial', distributionType=UNIFORM, localCsys=None, name='hemiHold', 
    	        region=myModel.rootAssembly.instances['hemi-1'].sets['hemiHoldY'], u1=UNSET, u2=SET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

	# History output - required to analyze the thickness and the diameter of the tube during the expansion phase 
	myModel.HistoryOutputRequest(createStepName='intPres', name='H-Output-2', rebar=EXCLUDE, region=
    	        myModel.rootAssembly.allInstances['tubef-1'].sets['topCheck'], sectionPoints=DEFAULT, variables=('UT', 'COOR2', 'COOR3'))
	myModel.HistoryOutputRequest(createStepName='intPres', name='H-Output-3', rebar=EXCLUDE, region=
    	        myModel.rootAssembly.allInstances['tubef-1'].sets['topCheckl'], sectionPoints=DEFAULT, variables=('UT', 'COOR2', 'COOR3'))	
	myModel.HistoryOutputRequest(createStepName='intPres', name='H-Output-4', rebar=EXCLUDE, region= MODEL,sectionPoints=DEFAULT, variables=('CFN2', 'CFNM'))	

def CFM_setup(myModel,indrad,orad,irad,inddep,tlen,damp,indenth,indentl):
	# Base
	mySketch = myModel.ConstrainedSketch(name='__profile__', sheetSize=0.2)
	mySketch.Line(point1=(0.0, 0.0), point2=(20e-3, 0.0))
	myPart3 = myModel.Part(dimensionality=THREE_D, name='base', type=ANALYTIC_RIGID_SURFACE)
	myPart3.AnalyticRigidSurfExtrude(depth=tlen+40e-3, sketch=mySketch)
	del mySketch
	myPart3.ReferencePoint(point=myPart3.vertices[2])

	# Indent
	mySketch = myModel.ConstrainedSketch(name='__profile__', sheetSize=0.2)
	mySketch.ConstructionLine(point1=(0.0, -0.1), point2=(0.0, 0.1))
	mySketch.ArcByCenterEnds(center=(0.0, 0.0), direction=CLOCKWISE, point1=(0.0, indrad), point2=(indrad, 0.0))
	mySketch.Line(point1=(indrad, 0), point2=(indrad, indrad-10e-3))
	mySketch.Line(point1=(indrad, indrad-10e-3), point2=(0.0, indrad-10e-3))
	
	myPart4 = myModel.Part(dimensionality=THREE_D, name='indent', type=ANALYTIC_RIGID_SURFACE)
	myPart4.AnalyticRigidSurfRevolve(sketch=mySketch)
	del mySketch
	myPart4.ReferencePoint(point=myPart4.vertices[3])

	# Assembly
	myModel.rootAssembly.Instance(dependent=ON, name='base-1', part=myPart3)
	myModel.rootAssembly.translate(instanceList=('base-1', ), vector=(-5e-3, -indenth+0.2e-3, 40e-3))
	
	myModel.rootAssembly.Instance(dependent=ON, name='indent-1', part=myPart4)
	myModel.rootAssembly.rotate(angle=180.0, axisDirection=(0.1, 0.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=('indent-1',))
#	myModel.rootAssembly.translate(instanceList=('indent-1', ), vector=(0, 2.91386e-3, 1.60265e-2))
	myModel.rootAssembly.translate(instanceList=('indent-1', ), vector=(0, indenth+indrad, indentl))	

	# Surface definition
	myPart3.Surface(name='topBase', side1Faces=myPart3.faces.findAt(((0,0,0),)))
	myPart4.Surface(name='botInd', side1Faces=myPart4.faces.findAt(((0,0,indrad),)))

	# Set definition
	myPart3.Set(name='RP_base',referencePoints=(myPart3.referencePoints[2],))
	myPart4.Set(name='RP_Indent',referencePoints=(myPart4.referencePoints[2],))

	# STEP TIME
	myModel.StaticStep(initialInc=0.0005, maxInc=0.05, maxNumInc=1000, minInc=1e-08, name='appPres', nlgeom=ON, previous='intPres', 
		timePeriod=inddep*1e3)
        
        myModel.steps['appPres'].setValues(adaptiveDampingRatio=0.05, continueDampingFactors=False, stabilizationMagnitude=damp, 
		stabilizationMethod=DISSIPATED_ENERGY_FRACTION)

	# Contact Properties
	myModel.ContactProperty('IntProp-1')
	myModel.interactionProperties['IntProp-1'].TangentialBehavior(formulation=FRICTIONLESS)
	myModel.interactionProperties['IntProp-1'].NormalBehavior(allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    	        pressureOverclosure=HARD)

	# Contact
	myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, clearanceRegion=None, createStepName='appPres', datumAxis=None, 
    	        initialClearance=OMIT, interactionProperty='IntProp-1', master=myModel.rootAssembly.instances['base-1'].surfaces['topBase'], 
    	        name='botConf', slave=myModel.rootAssembly.instances['tubef-1'].surfaces['outTubef'], sliding=FINITE)
	myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, clearanceRegion=None, createStepName='appPres', datumAxis=None, 
    	        initialClearance=OMIT, interactionProperty='IntProp-1', master=myModel.rootAssembly.instances['base-1'].surfaces['topBase'], 
    	        name='botConb', slave=myModel.rootAssembly.instances['tubeb-1'].surfaces['outTubeb'], sliding=FINITE)
	myModel.SurfaceToSurfaceContactStd(adjustMethod=NONE, clearanceRegion=None, createStepName='appPres', datumAxis=None, 
    	        initialClearance=OMIT, interactionProperty='IntProp-1', master=myModel.rootAssembly.instances['indent-1'].surfaces['botInd'], 
    	        name='topCon', slave=myModel.rootAssembly.instances['tubef-1'].surfaces['outTubef'], sliding=FINITE)
        myModel.interactions['botConb'].setValues(bondingSet=None, enforcement=NODE_TO_SURFACE, initialClearance=OMIT, 
                smooth=0.2, supplementaryContact=SELECTIVE, surfaceSmoothing=NONE, thickness=OFF)
        myModel.interactions['botConf'].setValues(bondingSet=None, enforcement=NODE_TO_SURFACE, initialClearance=OMIT, 
                smooth=0.2, supplementaryContact=SELECTIVE, surfaceSmoothing=NONE, thickness=OFF)
        myModel.interactions['topCon'].setValues(bondingSet=None, enforcement=NODE_TO_SURFACE, initialClearance=OMIT, 
                smooth=0.2, supplementaryContact=SELECTIVE, surfaceSmoothing=NONE, thickness=OFF)

	# Displacement BC
	myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial', distributionType=UNIFORM, localCsys=None, name='BaseHold', 
    	        region=myModel.rootAssembly.instances['base-1'].sets['RP_base'], u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)

#	myModel.TabularAmplitude(data=((0.0, 0.0), (0.2, 1.0)), name='Amp-1', smooth=SOLVER_DEFAULT, timeSpan=STEP)

#	myModel.DisplacementBC(amplitude=UNSET, createStepName='appPres', distributionType=UNIFORM, localCsys=None, name='BasePush', 
#    	        region=myModel.rootAssembly.instances['base-1'].sets['RP_base'], u1=SET, u2=2.4e-3, u3=SET, ur1=SET, ur2=SET, ur3=SET)

#	myModel.boundaryConditions['BasePush'].setValues(amplitude='Amp-1')

#	myModel.boundaryConditions['BaseHold'].deactivate('appPres')

	myModel.DisplacementBC(amplitude=UNSET, createStepName='Initial', distributionType=UNIFORM, localCsys=None, name='IndentHold', 
    	        region=myModel.rootAssembly.instances['indent-1'].sets['RP_Indent'], u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)
   	myModel.boundaryConditions['IndentHold'].deactivate('appPres')

	myModel.DisplacementBC(amplitude=UNSET, createStepName='appPres', distributionType=UNIFORM, localCsys=None, name='IndentPush', 
                region=myModel.rootAssembly.instances['indent-1'].sets['RP_Indent'], u1=SET, u2=-inddep, u3=SET, ur1=SET, ur2=SET, ur3=SET)
	myModel.boundaryConditions['hemiHold'].deactivate('appPres')        
        
        myModel.boundaryConditions['YHoldb'].deactivate('appPres')
        myModel.boundaryConditions['YHoldf'].deactivate('appPres')
    
