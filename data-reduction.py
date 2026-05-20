import os
import fnmatch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re

class dataRed:
    def __init__(self, filename, samplename, topdir, channels, maxenergy):
        self.filename = filename
        self.samplename = samplename
        self.topdir = topdir
        self.channels = channels
        self.maxenergy = maxenergy
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
                    sum = df.filter(regex=self.regexfunction()).sum(axis=1)
                    energy = df[df.filter(regex='Bragg').columns[0]].to_numpy()                    
        return [energy, sum, time]
    def acquisitionTime(self):
        return self.dataOpening()[2]
    def plot(self):
        energy = self.dataOpening()[0]
        counts = self.dataOpening()[1]
        fig = plt.figure(figsize=(5,3), facecolor=(1,1,1))
        plt.plot(energy, counts, color='red')
        plt.xlim(np.min(energy-10), self.maxenergy)
        plt.xlabel('energy')
        plt.ylabel('counts')
        plt.title(self.samplename)
        plt.savefig("plot.png",dpi=600, bbox_inches='tight')
        
channels = [
           '01', 
           '02',
           '03',
           #'04', #bad channel
           '05',
           '06',
           '07',
           '08',
           '09',
           '10',
           '11',
           '12',
           '13']

data = dataRed('ge.xdi', 'ge-electrode', 'data', channels, 11600)
data.plot()
