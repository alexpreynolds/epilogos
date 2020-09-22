import numpy as np
import sys
from pathlib import Path
import math
import pandas as pd
import time
import numpy.ma as ma
import operator as op
from functools import reduce
import multiprocessing

def main(filename, numStates, saliency, outputDirPath, expFreqPath, fileTag):
    dataFilePath = Path(filename)
    outputDirPath = Path(outputDirPath)

    # Read in the data
    print("\nReading data from file...")
    tRead = time.time()
    dataDF = pd.read_table(dataFilePath, header=None, sep="\t")
    print("    Time: ", time.time() - tRead)

    # Converting to a np array for faster functions later
    print("Converting to numpy array...")
    tConvert = time.time()
    dataArr = dataDF.iloc[:,3:].to_numpy(dtype=int) - 1 
    locationArr = dataDF.iloc[:,0:3].to_numpy(dtype=str)
    print("    Time: ", time.time() - tConvert)

    # Loading the expected frequency array
    expFreqArr = np.load(expFreqPath, allow_pickle=False)

    if saliency == 1:
        s1Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag)
    elif saliency == 2:
        s2Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag)
    elif saliency == 3:
        s3Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag)
    else:
        print("Inputed saliency value not supported")
        return

# Function that calculates the scores for the S1 metric
def s1Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag):
    numRows, numCols = dataArr.shape

    # Calculate the observed frequencies and final scores in one loop
    scoreArr = np.zeros((numRows, numStates))
    for row in range(numRows):
        uniqueStates, stateCounts = np.unique(dataArr[row], return_counts=True)
        for i in range(len(uniqueStates)):
            if (i > 14):
                print("i ==", i)
                print("len(uniqueStates)=", len(uniqueStates))
                print("row =", row)
            if (row == 9223372036854775807):
                print("row = 9223372036854775807")
                print("len(uniqueStates)=", len(uniqueStates))
            if (uniqueStates[i] > 15):
                print("uniqueStates has an errored value")
                print("uniqueState =", uniqueStates[i])
                print("row=", row)
                print("stateCount=",stateCounts[i])
                print(dataArr[row])
                print(uniqueStates)
                print(stateCounts)
            if (stateCounts[i] > 127):
                print("state counts is greater than 15: ", stateCounts[i])
            # Function input is obsFreq and expFreq
            scoreArr[row, uniqueStates[i]] = klScore(stateCounts[i] / (numCols), expFreqArr[uniqueStates[i]])

    storeScores(dataArr, scoreArr, locationArr, outputDirPath, fileTag)

# Function that calculates the scores for the S2 metric
def s2Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag):
    numRows, numCols = dataArr.shape

    # Calculate the observed frequencies
    obsFreqArr = np.zeros((numRows, numStates, numStates))

    # SumOverRows: (Within a row, how many ways can you choose x and y to be together) / (how many ways can you choose 2 states)
    # SumOverRows: (Prob of choosing x and y)
    # Can choose x and y to be together x*y ways if different and n(n-1)/2 ways if same (where n is the number of times that x/y shows up)
    if sys.version_info < (3, 8):
        print("\nFor maximum efficiency please update python to version 3.8 or later")
        print("NOTE: The code will still run in a lower version, but will be slightly slower\n")
        combinations = ncr(numCols, 2)
        for row in range(numRows):
            uniqueStates, stateCounts = np.unique(dataArr[row], return_counts=True)
            for i in range(len(uniqueStates)):
                for j in range(len(uniqueStates)):
                    if uniqueStates[i] > uniqueStates[j] or uniqueStates[i] < uniqueStates[j]:
                        obsFreqArr[row, uniqueStates[i], uniqueStates[j]]  = stateCounts[i] * stateCounts[j] / combinations / 2 # Extra 2 is to account for the symmetric matrix
                    elif uniqueStates[i] == uniqueStates[j]:
                        obsFreqArr[row, uniqueStates[i], uniqueStates[j]]  = ncr(stateCounts[i], 2) / combinations
    else:
        combinations = math.comb(numCols, 2)
        for row in range(numRows):
            uniqueStates, stateCounts = np.unique(dataArr[row], return_counts=True)
            for i in range(len(uniqueStates)):
                for j in range(len(uniqueStates)):
                    if uniqueStates[i] > uniqueStates[j] or uniqueStates[i] < uniqueStates[j]:
                        obsFreqArr[row, uniqueStates[i], uniqueStates[j]]  = stateCounts[i] * stateCounts[j] / combinations / 2 # Extra 2 is to account for the symmetric matrix
                    elif uniqueStates[i] == uniqueStates[j]:
                        obsFreqArr[row, uniqueStates[i], uniqueStates[j]]  = math.comb(stateCounts[i], 2) / combinations

    scoreArr = np.zeros((numRows, numStates))
    for row in range(numRows):
        scoreArr[row] = klScoreND(obsFreqArr[row], expFreqArr).sum(axis=0)

    storeScores(dataArr, scoreArr, locationArr, outputDirPath, fileTag)
    
# Function that calculates the scores for the S3 metric
def s3Score(dataDF, dataArr, locationArr, numStates, outputDirPath, expFreqArr, fileTag):
    numRows, numCols = dataArr.shape
    numProcesses = multiprocessing.cpu_count()

    # Because each epigenome, epigenome, state, state combination only occurs once per row, we can precalculate all the scores assuming a frequency of 1/(numCols*(numCols-1))
    # This saves a lot of time in the loop as we are just looking up references and not calculating
    scoreArrOnes = klScoreND(np.ones((numCols, numCols, numStates, numStates)) / (numCols * (numCols - 1)), expFreqArr)

    # Initializing necessary variables
    scoreArr = np.zeros((numRows, numStates))
    obsQueue = multiprocessing.Queue()
    obsProcesses = []

    # Creating the observed frequency/score processes and starting them
    for i in range(numProcesses):
        rowsToCalculate = range(i * numRows // numProcesses, (i+1) * numRows // numProcesses)
        p = multiprocessing.Process(target=s3Obs, args=(dataArr, numCols, numStates, rowsToCalculate, basePermutationArr, scoreArrOnes, obsQueue))
        obsProcesses.append(p)
        p.start()

    # Move all the scores from the queue to the score array
    for i in range(numRows):
        scoreRow = obsQueue.get()
        scoreArr[scoreRow[0]] = scoreRow[1]

    # Shut down all the processes
    for process in obsProcesses:
        process.join()

    storeScores(dataArr, scoreArr, locationArr, outputDirPath, fileTag)

# Helper for the multiprocessing implemented in s3
def s3Obs(dataArr, numCols, numStates, rowsToCalculate, basePermutationArr, scoreArrOnes, queue):
    for row in rowsToCalculate:
        # Pull the scores from the precalculated score array
        rowScoreArr = np.zeros((numCols, numCols, numStates, numStates))
        rowScoreArr[basePermutationArr[0], basePermutationArr[1], dataArr[row, basePermutationArr[0]], dataArr[row, basePermutationArr[1]]] = scoreArrOnes[basePermutationArr[0], basePermutationArr[1], dataArr[row, basePermutationArr[0]], dataArr[row, basePermutationArr[1]]]

        queue.put((row, rowScoreArr.sum(axis=(0,1,2))))

# Helper to store the score arrays combined with the location arrays
def storeScores(dataArr, scoreArr, locationArr, outputDirPath, fileTag):
    # Creating a file path

    # MAKE IT CHROMOSOME AN DLOCATION ON CHROMOSOME
    
    chromosomeNumber = str(locationArr[0, 0])
    scoreFilename = "temp_scores_{}_{}.npy".format(fileTag, chromosomeNumber)
    scoreFilePath = outputDirPath / scoreFilename

    # Concatenating the locationArr and dataArr into one helps writing later
    combinedArr = np.concatenate((locationArr, scoreArr), axis=1)

    np.save(scoreFilePath, combinedArr, allow_pickle=False)

# Helper to calculate KL-score (used because math.log2 errors out if obsFreq = 0)
def klScore(obs, exp):
    if obs == 0.0:
        return 0.0
    else:
        return obs * math.log2(obs / exp)

# Helper to calculate KL-score for 2d arrays (cleans up the code)
def klScoreND(obs, exp):
    return obs * ma.log2(ma.divide(obs, exp).filled(0)).filled(0)

# Helper to calculate combinations
def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n - r, -1), 1)
    denom = reduce(op.mul, range(1, r + 1), 1)
    return numer // denom

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6])