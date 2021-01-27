import time
from pathlib import Path
import sys
import pandas as pd
import numpy as np

def main(inputDir, outputDir):
    tTotal = time.time()

    inputDirPath = Path(inputDir)
    outputDirPath = Path(outputDir)

    fileInfoList = []

    for file in inputDirPath.glob("*"):
        # read in the first line of the file to determine genome and chromosome
        with open(file, "r") as f:
            line = f.readline()
            lineSplit = line.split()
            genome = lineSplit[0]
            chromosome = lineSplit[1]
        # add to file info list [filename, genome, chromosome]
        fileInfoList.append([file, genome, chromosome])

    directoryDF = pd.DataFrame(fileInfoList, columns=["Filename", "Genome", "Chromosome"])

    genomeList = list(directoryDF["Genome"].unique())
    chromosomeList = list(directoryDF["Chromosome"].unique())

    # Check that all genomes have all chromosomes
    valueCounts = directoryDF["Genome"].value_counts()
    missingBool = False
    for genome, count in valueCounts.iteritems():
        if count != len(genomeList):
            print("{} has {} chromosomes. {} were expected".format(genome, count, len(genomeList)))
            missingBool = True
    if missingBool:
        return

    # Order the dataframe by genome so that we are guaranteed order when sorting later
    directoryDF["Genome"] = pd.Categorical(directoryDF["Genome"], categories=genomeList, ordered=True)
    directoryDF.sort_values(by=["Genome", "Chromosome", "Filename"], inplace=True)

    # Create and store numpy arrays for each chromosome
    for chromosome in chromosomeList:
        stateList = [] 
        # loop over all rows which contain chromosome in question
        for row in directoryDF.loc[directoryDF["Chromosome"] == chromosome].itertuples():
            # Use the stored filename to read and store all but first 2 lines
            with open(row[0], "r") as f:
                stateList.append(f.readlines[2:])
        
        # Because we appended all the lines from each file at once to the list, we must take the transpose so the array has 200bp bins as rows
        stateArr = np.array(stateList).T
        
        # Each row is a 200bp bin, so use that to calculate locations
        locationArr = np.array([[chromosome, 200*i, 200*i+200] for i in range(stateArr.shape[0])])

        # Path contains number of states as chromsome
        chromosomeFilePath = outputDirPath / "{}state_{}.npz".format(np.amax(stateArr), chromosome)

        # Savez saves space allowing location to be stored as string and state as float
        np.savez_compressed(chromosomeFilePath, locationArr=locationArr, scoreArr=stateArr)

    print("Chromosomes:\t{}".format(chromosomeList))
    print("Genome Order:\t{}".format(genomeList))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])