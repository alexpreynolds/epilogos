import numpy as np
import sys
from pathlib import Path
import math
import pandas as pd
import time
import operator as op
from functools import reduce
import multiprocessing
import itertools
from contextlib import closing

def main(filename, numStates, saliency, outputDirPath, fileTag, numProcesses):
    dataFilePath = Path(filename)
    outputDirPath = Path(outputDirPath)

    # Reading in the data
    print("\nReading data from file...")
    tRead = time.time()
    dataDF = pd.read_table(dataFilePath, header=None, sep="\t")
    print("    Time: ", time.time() - tRead)

    # Converting to a np array for faster functions later
    print("Converting to numpy array...")
    tConvert = time.time()
    dataArr = dataDF.iloc[:,3:].to_numpy(dtype=int) - 1 
    print("    Time: ", time.time() - tConvert)

    # If user doesn't want to choose number of cores use as many as available
    if numProcesses == 0:
        numProcesses = multiprocessing.cpu_count()

    # Determine saliency and calculate expected frequencies
    if saliency == 1:
        s1Exp(dataDF, dataArr, numStates, outputDirPath, fileTag)
    elif saliency == 2:
        s2Exp(dataDF, dataArr, numStates, outputDirPath, fileTag, numProcesses)
    elif saliency == 3:
        s3Exp(dataDF, dataArr, numStates, outputDirPath, fileTag, numProcesses)
    else:
        print("Inputed saliency value not supported")
        return

sharedArr=None
inputInfo=None

# Initiliazer for multiprocessing
def _init(inputInfo_):
    global inputInfo
    inputInfo = inputInfo_

# Function that calculates the expected frequencies for the S1 metric
def s1Exp(dataDF, dataArr, numStates, outputDirPath, fileTag):
    numRows, numCols = dataArr.shape

    # Calculate the expected frequencies of each state
    # Done column-wise instead of row-wise thus we don't multiprocess as it provides negligible efficiency bonus
    stateIndices = list(range(1, numStates + 1))
    expFreqSeries = pd.Series(np.zeros(numStates), index=stateIndices)
    dfSize = numRows * numCols
    for i in range(3, numCols + 3):
        stateCounts = dataDF[i].value_counts()
        for state, count in stateCounts.items():
            expFreqSeries.loc[state] += count / dfSize
    expFreqArr = expFreqSeries.to_numpy()

    storeExpArray(dataDF, expFreqArr, outputDirPath, fileTag)

# Function that deploys the processes used to calculate the expected frequencies for the s2 metric. Also call function to store expected frequency
def s2Exp(dataDF, dataArr, numStates, outputDirPath, fileTag, numProcesses):
    numRows, numCols = dataArr.shape
    print("NUM PROCESSES:", numProcesses)

    # Split the rows up according to the number of cores we have available
    rowList = []
    for i in range(numProcesses):
        rowsToCalculate = range(i * numRows // numProcesses, (i+1) * numRows // numProcesses)
        rowList.append(rowsToCalculate)

    # Start the processes
    with closing(multiprocessing.Pool(numProcesses, initializer=_init, initargs=((dataArr, numStates, numCols), ))) as pool:
        results = pool.map(s2Calc, rowList)
    pool.join()

    # Sum all the expected frequency arrays from the seperate processes and normalize by dividing by numRows
    expFreqArr = np.sum(results, axis = 0) / numRows

    storeExpArray(dataDF, expFreqArr, outputDirPath, fileTag)


# Function that calculates the expected frequencies for the S2 metric over a chunk of the data
def s2Calc(rowsToCalculate):
    # inputInfo[0] is dataArr
    # inputInfo[1] is numStates
    # inputInfo[2] is numCols

    expFreqArr = np.zeros((inputInfo[1], inputInfo[1]))

    # SumOverRows: (Within a row, how many ways can you choose x and y to be together) / (how many ways can you choose 2 states)
    # SumOverRows: (Prob of choosing x and y)
    # Can choose x and y to be together x*y ways if different and n(n-1)/2 ways if same (where n is the number of times that x/y shows up)
    if (sys.version_info < (3, 8)):
        print("\nFor maximum efficiency please update python to version 3.8 or later")
        print("NOTE: The code will still run in a lower version, but will be slightly slower\n")
        combinations = ncr(inputInfo[2], 2)
        for row in rowsToCalculate:
            uniqueStates, stateCounts = np.unique(inputInfo[0][row], return_counts=True)
            for i in range(len(uniqueStates)):
                for j in range(len(uniqueStates)):
                    if uniqueStates[i] > uniqueStates[j] or uniqueStates[i] < uniqueStates[j]:
                        expFreqArr[uniqueStates[i], uniqueStates[j]] += stateCounts[i] * stateCounts[j] / combinations / 2 # Extra 2 is to account for the symmetric matrix
                    elif uniqueStates[i] == uniqueStates[j]:
                        expFreqArr[uniqueStates[i], uniqueStates[j]] += ncr(stateCounts[i], 2) / combinations
    else:
        combinations = math.comb(inputInfo[2], 2)
        for row in rowsToCalculate:
            uniqueStates, stateCounts = np.unique(inputInfo[0][row], return_counts=True) 
            for i in range(len(uniqueStates)):
                for j in range(len(uniqueStates)):
                    if uniqueStates[i] > uniqueStates[j] or uniqueStates[i] < uniqueStates[j]:
                        expFreqArr[uniqueStates[i], uniqueStates[j]] += stateCounts[i] * stateCounts[j] / combinations / 2 # Extra 2 is to account for the symmetric matrix
                    elif uniqueStates[i] == uniqueStates[j]:
                        expFreqArr[uniqueStates[i], uniqueStates[j]] += math.comb(stateCounts[i], 2) / combinations

    return expFreqArr

# Function that deploys the processes used to calculate the expected frequencies for the s3 metric. Also call function to store expected frequency
def s3Exp(dataDF, dataArr, numStates, outputDirPath, fileTag, numProcesses):
    numRows, numCols = dataArr.shape
    print("NUM PROCESSES:", numProcesses)

    # Gives us everyway to combine the column numbers in numpy indexing form
    basePermutationArr = np.array(list(itertools.permutations(range(numCols), 2))).T

    # Split the rows up according to the number of cores we have available
    rowList = []
    for i in range(numProcesses):
        rowsToCalculate = range(i * numRows // numProcesses, (i+1) * numRows // numProcesses)
        rowList.append(rowsToCalculate)

    # Start the processes
    with closing(multiprocessing.Pool(numProcesses, initializer=_init, initargs=((dataArr, basePermutationArr, numStates, numCols), ))) as pool:
        results = pool.map(s3Calc, rowList)
    pool.join()

    # Sum all the expected frequency arrays from the seperate processes and normalize by dividing
    expFreqArr = np.sum(results, axis = 0) / numRows * numCols * (numCols - 1)

    storeExpArray(dataDF, expFreqArr, outputDirPath, fileTag)

# Function that calculates the expected frequencies for the S3 metric over a chunk of the data
def s3Calc(dataArr, numCols, numStates, rowsToCalculate, basePermutationArr, queue):
    # inputInfo[0] is dataArr
    # inputInfo[1] is basePermutationArr
    # inputInfo[2] is numStates
    # inputInfo[3] is numCols

    expFreqArr = np.zeros((inputInfo[3], inputInfo[3], inputInfo[2], inputInfo[2]))
    
    # We tally a one for all the state/column combinations we observe (e.g. for state 18 in column 2 and state 15 in column 6 we would add one to index [5, 1, 17, 14])
    for row in rowsToCalculate:
        expFreqArr[inputInfo[1][0], inputInfo[1][1], inputInfo[0][row, inputInfo[1][0]], inputInfo[0][row, inputInfo[1][1]]] += np.ones(inputInfo[1].shape[1])

    return expFreqArr

# Helper to store the expected frequency arrays
def storeExpArray(dataDF, expFreqArr, outputDirPath, fileTag):
    # Creating a file path
    locationTag = "{}_{}_{}".format(dataDF.iloc[0, 0], dataDF.iloc[0,1], dataDF.iloc[0,2])
    expFreqFilename = "temp_exp_freq_{}_{}.npy".format(fileTag, locationTag)
    expFreqPath = outputDirPath / expFreqFilename

    np.save(expFreqPath, expFreqArr, allow_pickle=False)

# Helper to calculate combinations
def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n - r, -1), 1)
    denom = reduce(op.mul, range(1, r + 1), 1)
    return numer // denom

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], int(sys.argv[6]))