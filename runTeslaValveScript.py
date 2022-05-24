import sys
import configparser as cp
import numpy as np
import scipy.io
import os
import time
import multiprocessing
from driftDiffusionSimulatorTeslaValve import driftDiffusionSimulatorTeslaValve
from myGeometryFunctions import *

'''
runTeslaValveScript.py reads in a script text file and runs a number of simulations of
a "driftDiffusionSimulatorTelsaValve simulation object. It enables starting from a 
fresh simulation, or taking the results of a previous simulation as initial cond-
itions. 
'''

def main():
	
	initFile = sys.argv[1]
	
	config = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
	config.read(initFile)

	pScatter = config['DEFAULT'].getfloat('Scattering Probability', 0)
	Temp = config['DEFAULT'].getfloat('Temperature', 100)
	sourceDrainRatio = config['DEFAULT'].getfloat('Source Drain Ratio', 1.2)
	expPartDensity = config['DEFAULT'].getfloat('Experimental Particle Density', 1e12)
	simPartDensity = config['DEFAULT'].getfloat('Simulation Particle Density', 20)
	Nsteps = config['DEFAULT'].getint('time steps', 10000)
	dNsave = config['DEFAULT'].getint('save interval', 1000)
	collisionDist = config ['DEFAULT'].getfloat('collision overlap', 0.05)
	stepSize = config['DEFAULT'].getfloat('step size', 0.01)
	makeMovie = config['DEFAULT'].getboolean('make movie?',False)

	fieldRes = config['DEFAULT'].getfloat('histogram resolution',0.1)
    
	Ncpu = config['DEFAULT'].getint('Number of CPUs', 1)
	outPath = config['DEFAULT'].get('base output path', './SIM_data/')
	
	diffusiveEdges = config['DEFAULT'].getboolean('diffusive edges?', False)
	reinjectWithE1 = config['DEFAULT'].getboolean('reinject partilces with unity energy?', False)   
    
	currentDirection = config['DEFAULT'].get('current direction?', 'easy')
    
	tip = config['DEFAULT'].getboolean('add probe tip?', True)
	if tip:
		probeCenterX,probeCenterY = [float(s) for s in config['DEFAULT'].get(
					'probe tip location X,Y','0,0').split(',')]
	
	initCondFile = config['DEFAULT'].get('inital conditions','')

	generateReinjectionProbsYN = config['DEFAULT'].getboolean('generate reinjection probabilities?', False)
	setProbsMethod = config['DEFAULT'].get('set probs method','by length')
	generatedProbs = config['DEFAULT'].get('generated probs by simulation', '[]')
	generatedProbs=np.array(eval(generatedProbs))
	
	splitName = initFile.split('.')
	splitName.remove('txt')
	fnameBase = '.'.join(splitName)

	print(outPath+fnameBase)
	if not os.path.isdir(outPath+fnameBase):
		os.mkdir(outPath+fnameBase)
        
	if generateReinjectionProbsYN:
		print("This simulation will be used to calculate reinjection probabilities.")

	if tip:
		print("Probe tip location:", probeCenterX, probeCenterY)
        
	else:
			print("Mirror Edges")

	dSims = []
	for iterationNum in range(Ncpu):
		
		#set up the simulation from script file
		dSim = driftDiffusionSimulatorTeslaValve()
        
		dSim.generateReinjectionProbsYN = generateReinjectionProbsYN
		dSim.setProbsMethod = setProbsMethod
		dSim.setSourceDrainRatio(sourceDrainRatio)
		dSim.generatedProbs = generatedProbs
		dSim.makeMovie = makeMovie
        
		dSim.tip = tip
		if dSim.tip:
			dSim.probeCenterX, dSim.probeCenterY = probeCenterX, probeCenterY
		dSim.Temp = Temp
		dSim.expPartDensity =expPartDensity
		dSim.simPartDensity= simPartDensity
		dSim.setEmin(dSim.expPartDensity, dSim.Temp,simPartDensity=dSim.simPartDensity)
		#dSim.setEmin(dSim.expPartDensity, dSim.Temp)
        
		dSim.updateBody()
		dSim.calcArea()
		dSim.setNpart(dSim.simPartDensity, dSim.Area)
		dSim.updateNparticles()
        
		dSim.calc_pScatter()
		if pScatter ==0: 
			dSim.updateScatterProb(pScatter)
    
		if reinjectWithE1:
			dSim.consumeAndReinject = dSim.consumeAndReinject_withE1
			print("reinjects particles with energy = 1")
            
		dSim.setFieldResolution(fieldRes)
		dSim.setOverlapRadius(collisionDist)
		dSim.setStepSize(stepSize)
		dSim.updateNparticles()

		if diffusiveEdges:
			dSim.diffusiveWalls()
			print("Diffusive Edges")
		else:
			dSim.mirrorWalls()
			print("Mirror Edges")

		for i in range(int(dSim.Npart/2)):
			thetas = np.random.rand()*2.*np.pi
			dSim.vX[i] = np.cos(thetas)
			dSim.vY[i] = np.sin(thetas)
			dSim.vX[i+int(dSim.Npart/2)] = -np.cos(thetas)
			dSim.vY[i+int(dSim.Npart/2)] = -np.sin(thetas)
		
		if initCondFile:
			if os.path.isfile(outPath+initCondFile+'/'+initCondFile+("_%03d"%iterationNum)+".npz"):
				mat = np.load(outPath+initCondFile+'/'+initCondFile+("_%03d"%iterationNum)+".npz")
				dSim.Nabsorbed = mat['Nabsorbed']
				dSim.Ninjected = mat['Ninjected']
				dSim.Px = mat['Px']
				dSim.Py = mat['Py']
				dSim.pR = mat['pR']
				dSim.Erho = mat['Erho']
				dSim.rho = mat['rho']
				dSim.Xpos = mat['Xpos']
				dSim.Ypos = mat['Ypos']
				dSim.vX = mat['vX']
				dSim.vX = mat['vY']
				dSim.overlaps = mat['overlaps']
				dSim.i_lookup = mat['i_lookup']
				dSim.j_lookup = mat['j_lookup']
				dSim.timeCount = mat['timeCount']
				dSim.frameNum = mat['frameNum']
				dSim.NcornersCrossed = mat['NcornersCrossed']
                
				dSim.Nrestarts = mat['Nrestarts']
				dSim.Nrestarts += 1
				if iterationNum ==0:
					print("Number of Restarts:", dSim.Nrestarts)
					print("timesteps:", dSim.timeCount)
				dSim.symmetrizedNinjected_NEW = mat['symmetrizedNinjected_NEW']
				dSim.symmetrizedNinjected_OLD = mat['symmetrizedNinjected_OLD']
				dSim.symmetrizedNinjected_totalOLD = mat['symmetrizedNinjected_totalOLD']
				dSim.symmetrizedNinjected_DIF = mat['symmetrizedNinjected_DIF']
			
		dSims.append(dSim)
        
	print("Temp SourceDrain Emin expPartDensity simPartDensity pScatter")
	print(Temp, sourceDrainRatio, dSim.Emin, expPartDensity,dSim.simPartDensity, pScatter)
        
	jobs=[]
	for iterationNum,dSim in enumerate(dSims):
		fnameOut = outPath+fnameBase+"/"+fnameBase+("_%03d"%iterationNum)+".npz"
	
		p = multiprocessing.Process(target=dSim.runAndSave, args=(Nsteps-dSim.timeCount,dNsave,fnameOut))
		jobs.append(p)
		p.start()
	p.join()


if __name__== "__main__":
  main()
