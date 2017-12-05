# **************************************************
# * Abaqus python script/CAE Release 6.14-1        *
# * Authors: G. Munglani            			   *
# * Copyright, IfB ETH Zurich					   *
# *												   *
# * Script to generate soft indentation setup      * 
# **************************************************

import math
import sys
import os
import errno
from ConfigParser import SafeConfigParser
from module import tube_setup, CFM_setup
from job import *

# **************************************************

# Parameters - Iterate
cfile = sys.argv[-7]
flag = int(sys.argv[-6])
npres = int(sys.argv[-5])
dmult = int(sys.argv[-4])
tmult = int(sys.argv[-3])
ih = int(sys.argv[-2])
il = int(sys.argv[-1])

# Parameters - Config
current_dir = os.getcwd()
config = SafeConfigParser()
config.read(current_dir+'/'+cfile)

name = config.get('Parameters','name')
rad = config.get('Parameters','radius (um)')
thk = config.get('Parameters','thickness (um)')
stretch = config.get('Parameters','stretch (-)')
stiff = config.get('Parameters','stiffness (nm^-1)')
indrad = config.get('Parameters','indentor radius (um)')
inddep = config.get('Parameters','indentor depth (um)')
indpos = config.get('Parameters','indent axis position (um)')
tlen = config.get('Parameters','tube length (um)')
damp = config.get('Parameters','damping (-)')

# Unit translation - Abaqus
mod = dmult*1e-4*npres*float(rad)/(float(thk)*math.log(float(stretch)))
thick = float(thk)*1e-3*tmult*1e-2
orad = float(rad)*1e-3 
irad = orad - thick

indenth = ih*1e-6 + 0.2e-3
indentl = il*1e-6

# Fixed parameters
v = 0.01
tlenf = (float(indpos) - 3)*2e-3
tlenb = float(tlen)*1e-3 - tlenf

jobname = "P"+str(npres)+"_M"+str(dmult)+"_H"+str(tmult)
dir_path = current_dir+"/output/"+str(name)+"/R"+str(rad)+"_T"+str(thk)+"_A"+str(stiff)+"_S"+str(stretch)+'/'+jobname

try:
	os.makedirs(dir_path)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise

os.chdir(dir_path)

# Model creation
Mdb() 
mdb.models.changeKey(fromName='Model-1', toName='CFM')
myModel=mdb.models['CFM']

tube_setup(myModel,float(indrad)*1e-3,orad,irad,float(npres*1e-2),mod,v,tlenb,tlenf)
if (flag == 3):
	CFM_setup(myModel,float(indrad)*1e-3,orad,irad,float(inddep)*1e-3,float(tlen)*1e-3,float(damp),indenth,indentl)	


# Job
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=7, memoryUnits=GIGA_BYTES, model='CFM', modelPrint=OFF, multiprocessingMode=DEFAULT, name=jobname, 
    nodalOutputPrecision=SINGLE, numCpus=6, numDomains=6, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=ANALYSIS, 
    userSubroutine='', waitHours=0, waitMinutes=0)

mdb.saveAs(pathName=dir_path+"/model.cae")

# RUN
myModel.rootAssembly.regenerate()
mdb.jobs[jobname].writeInput(consistencyChecking=OFF)
mdb.jobs[jobname].submit(consistencyChecking=OFF)

