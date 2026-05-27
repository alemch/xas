import os
import fnmatch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from scipy.interpolate import interp1d

me = 0.511 #[Mev/c^2] electron mass
hBarC = 1.973269804*10e-3 #[Mev*A]

class dataRed:
    def __init__(self, filename, samplename, topdir, channels):
        self.filename = filename
        self.samplename = samplename
        self.topdir = topdir
        self.channels = channels

    def regexfunction(self):
        return '|'.join(self.channels)
        
    def dataOpening(self):
        acquistionTime = []
        for root, dirs, files in os.walk(self.topdir):
            for file in files:
                if fnmatch.fnmatch(file, self.filename):
                    xasfile = os.path.join(root, file)
                    with open(xasfile) as myfile:
                        firstLine = myfile.readline()
                        time = myfile.readline().split()[2]
                        skippedlines = 0
                        for line in myfile:
                            match = re.match("#", line)
                            if match is not None:
                                skippedlines += 1
                    df = pd.read_csv(xasfile, sep=" +", 
                                     skiprows=skippedlines+1, 
                                     engine='python', 
                                     encoding='utf-8')
                    cols = df.columns[1:]
                    df = df.drop(df.columns[-1], axis=1)
                    df.columns = cols
                    df = df.drop(df.columns[~df.columns.str.contains('fluo|Bragg', regex=True)], axis=1) 
                    sum = df.filter(regex=self.regexfunction()).sum(axis=1).to_numpy()
                    energy = df[df.filter(regex='Bragg').columns[0]].to_numpy()      
        return [energy, sum, time]
    
    def acquisitionTime(self):
        return self.dataOpening()[2]
    
    def muPlot(self, maxenergy, Rbkg, kMax, kMin, absEdge):
        energy = self.dataOpening()[0]
        counts = self.dataOpening()[1]
        deltaE = (energy-absEdge)*10e-6 #energy difference in Mev
        
        indDeltaE = [i for i in range(len(deltaE)) if deltaE[i] > 0] #indexes of deltaE array where deltaE is >0
        deltaE = deltaE[indDeltaE] #deltaE >0
        
        k = (1/hBarC)*((2*me*deltaE)**(1/2)) #energy-wavevector conversion
        n = round(1+(2*Rbkg*(kMax-kMin)/np.pi)) #nknots, shannon-nyquist sampling theorem
        indKnots = np.linspace(0, len(energy)-1, n, dtype=int) #indexes of the knots
        energyInterp = energy[indKnots] #energy values of the knots
        countsInterp = counts[indKnots] #counts values of the knots
        
        xInterp = np.linspace(np.min(energyInterp), 
                              np.max(energyInterp), 
                              np.size(energy))
                
        yInterp = interp1d(energyInterp, countsInterp, kind='linear') #spline interpolation
        spline = yInterp(xInterp) #spline computed for the xInterp values

        fig = plt.figure(figsize=(5,3), facecolor=(1,1,1))
        #plt.plot(k, counts, color='#666666')
        plt.plot(xInterp, spline, color='grey', label='background')
        plt.plot(energy, counts, color='red', label='data')
        plt.xlim(np.min(energy-10), maxenergy)
        plt.xlabel('energy')
        plt.ylabel('counts')
        plt.title(f'{self.samplename}, absorption spectrum')
        plt.legend()
        plt.savefig("abs-spectrum.png",dpi=600, bbox_inches='tight')

        difference = counts-spline
        difference = difference[indDeltaE]
        fig = plt.figure(figsize=(5,3), facecolor=(1,1,1))       
        plt.plot(k, (k**2)*difference, color='blue')
        plt.xlabel('k')
        plt.ylabel(r'$k\chi(k)$')
        plt.title(f'{self.samplename}, fine structure')
        plt.savefig("finestructure.png",dpi=600, bbox_inches='tight')
        plt.show()
        plt.close(fig)
        
channels = ['01', '02', '03', '05', '06', '07', '08', '09', '10', '11', '12', '13']

data = dataRed('ge2.xdi', #filename
               'ge-electrode', #title
               'data', #top directory
               channels) #list of the good channels

data.muPlot(11400, #max energy in the plot
            1.7, #Rbkg, cutoff frequency 
            10, #max value of k wave-vector
            2, #min value of k wave-vector
            11100) #absorption edge
