from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup
from odbAccess import *
from textRepr import *
from visualization import *

import math
import os.path
import sys
import errno
from ConfigParser import SafeConfigParser

cfile = sys.argv[-5]
flag = int(sys.argv[-4])
npres = int(sys.argv[-3])
dmult = int(sys.argv[-2])
tmult = int(sys.argv[-1])

#cfile = 'config.dat'
#npres = 33
#flag = 2
#dmult = 110

current_dir = os.getcwd()
config = SafeConfigParser()
config.read(current_dir+'/'+cfile)

name = config.get('Parameters','name')
rad = config.get('Parameters','radius (um)')
thk = config.get('Parameters','thickness (um)')
stretch = config.get('Parameters','stretch (-)')
stiff = config.get('Parameters','stiffness (nm^-1)')


# Odb analysis
#try:
jobname = "P"+str(npres)+"_M"+str(dmult)+"_H"+str(tmult)
dir_path = current_dir+"/output/"+str(name)+"/R"+str(rad)+"_T"+str(thk)+"_A"+str(stiff)+"_S"+str(stretch)+'/'+jobname

odb = openOdb(dir_path+'/'+jobname+'.odb')
#except IOError:
#	sys.exit()

ytop = odb.steps['intPres'].historyRegions['Node TUBEF-1.303'].historyOutputs['COOR2'].data
ytopd = odb.steps['intPres'].historyRegions['Node TUBEF-1.303'].historyOutputs['U2'].data

ytopl = odb.steps['intPres'].historyRegions['Node TUBEF-1.195'].historyOutputs['COOR2'].data
ytopdl = odb.steps['intPres'].historyRegions['Node TUBEF-1.195'].historyOutputs['U2'].data

ztop = odb.steps['intPres'].historyRegions['Node TUBEF-1.303'].historyOutputs['COOR3'].data
ztopd = odb.steps['intPres'].historyRegions['Node TUBEF-1.303'].historyOutputs['U3'].data

#ytop = odb.steps['intPres'].historyRegions['Node TUBEF-1.51'].historyOutputs['COOR2'].data
#ztop = odb.steps['intPres'].historyRegions['Node TUBEF-1.51'].historyOutputs['COOR3'].data

if os.path.exists(dir_path+'/expand.dat'):
	    os.remove(dir_path+'/expand.dat')

f1=open(dir_path+'/expand.dat','w')
for b in range(len(ytop)):
	ys = ytop[b][1] + ytopd[b][1]
	zs = ztop[b][1] + ztopd[b][1]
	yl = ytopl[b][1] + ytopdl[b][1]

        f1.write(str(ytop[b][0])+"\t"+str(ytop[b][1])+"\t"+str(ys-yl)+"\t"+str(ztop[b][1])+"\n") # Time     Outer Y Position     Thickness     Outer Z position    
#	f1.write(str(ytop[b][0])+"\t"+str(ytop[b][1]+float(thk)*0.5e-3)+"\t"+str(ztop[b][1])+"\n") # Time     Outer Y Position     Thickness     Outer Z position    
f1.close()

if (flag == 3):
        ind = odb.steps['appPres'].historyRegions['Node TUBEF-1.303'].historyOutputs['COOR2'].data
#       ind = odb.steps['appPres'].historyRegions['Node TUBEF-1.51'].historyOutputs['COOR2'].data
#	fo = odb.steps['appPres'].historyRegions['NodeSet TUBEF-1.SURFCHECK'].historyOutputs['CFN2     ASSEMBLY_TUBEF-1_OUTTUBEF/ASSEMBLY_INDENT-1_BOTIND'].data
#	fom = odb.steps['appPres'].historyRegions['NodeSet TUBEF-1.SURFCHECK'].historyOutputs['CFNM     ASSEMBLY_TUBEF-1_OUTTUBEF/ASSEMBLY_INDENT-1_BOTIND'].data
        fo = odb.steps['appPres'].historyRegions['NodeSet . Z000003'].historyOutputs['CFN2     ASSEMBLY_TUBEF-1_OUTTUBEF/ASSEMBLY_INDENT-1_BOTIND'].data
     
        if os.path.exists(dir_path+'/indent.dat'):
	        os.remove(dir_path+'/indent.dat')

        f2=open(dir_path+'/indent.dat','w')
	for b in range(len(ind)):
		f2.write(str(ind[b][0])+"\t"+str(ind[b][1])+"\t"+str(fo[b][1])+"\n") #+"\t"+str(fom[b][1])+"\n") # Time     Contact Point Y Position     Normal Force     Total Force
	f2.close()

