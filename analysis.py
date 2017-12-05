import math
import os
import sys
import numpy as np
from ConfigParser import SafeConfigParser
import matplotlib.pyplot as plt

cfile = sys.argv[-4]
npres = int(sys.argv[-3])
dmult = int(sys.argv[-2])
tmult = int(sys.argv[-1])

current_dir = os.getcwd()
config = SafeConfigParser()
config.read(current_dir+'/'+cfile)

name = config.get('Parameters','name')
rad = config.get('Parameters','radius (um)')
thk = config.get('Parameters','thickness (um)')
stretch = config.get('Parameters','stretch (-)')
stiff = config.get('Parameters','stiffness (nm^-1)')
tforce = config.get('Parameters','target force (un)')

mod = dmult*1e-4*npres*float(rad)/(float(thk)*math.log(float(stretch)))

jobname = "P"+str(npres)+"_M"+str(dmult)+"_H"+str(tmult)
dir_path = current_dir+"/output/"+str(name)+"/R"+str(rad)+"_T"+str(thk)+"_A"+str(stiff)+"_S"+str(stretch)+'/'+jobname

move = []
force = []
if os.path.isfile(dir_path+'/indent.dat'):
        data = np.loadtxt(dir_path+'/indent.dat')
        max_time = np.amax(data[:,0])
        max_force = np.amax(data[:,2])
        for x in range(len(data[:,2])): 
                unit = data[x,2]*1e6
                if (0.2 < unit < (float(tforce)*0.5)): 
                        move.append(1e-6 * data[x,0])
                        force.append(2.0 * data[x,2])
    
        fit = np.polyfit(move, force, 1)

        edata = np.loadtxt(dir_path+'/expand.dat')
        result = SafeConfigParser()
        result.add_section("Output")
        result.set("Output", "Turgor Pressure (MPa)", str(npres*1e-2))
        result.set("Output", "Young's Modulus (MPa)", str(int(mod)))
        result.set("Output", "Simulated Stiffness (Nm^-1)", str(int(1e2*fit[0])*1e-2))
        result.set("Output", "Simulated Stretch (-)", str(int(1e3*edata[-1,1]/edata[0,1])*1e-3))
        result.set("Output", "Simulated Thickness (um)", str(int(1e3*edata[-1,2]*1e3)*1e-3))
        result.set("Output", "Simulated Depth (um)", str(max_time))
        result.set("Output", "Simulated Force (uN)", str(max_force*2))

        with open(dir_path+"/result.dat", "w") as result_file:
                result.write(result_file)
     


