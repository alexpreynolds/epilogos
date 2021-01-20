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
import itertools
import gzip

def main(file1, file2, numStates, saliency, outputDirPath, expFreqPath, realOrNull):

    tTotal = time.time()

    file1Path = Path(file1)
    file2Path = Path(file2)

    print("______________PATHS______________")
    print(file1Path)
    print(file2Path)

    outputDirPath = Path(outputDirPath)

    # For distinguishing the chunkwise output files
    fileTag = "{}_{}_{}".format(file1Path.parent.name, file2Path.parent.name, file1Path.name.split(".")[0])

    # Loading the expected frequency array
    expFreqArr = np.load(expFreqPath, allow_pickle=False)
    
    print("Expected Frequency Array:")
    print(expFreqArr)
    print()

    # Read in the data
    print("\nReading data from file 1...")
    tRead1 = time.time()
    file1DF = pd.read_table(file1Path, header=None, sep="\t")
    print("    Time: ", time.time() - tRead1)

    print("Reading data from file 2...")
    tRead2 = time.time()
    file2DF = pd.read_table(file2Path, header=None, sep="\t")
    print("    Time: ", time.time() - tRead2)

    if realOrNull.lower() == "real":
        # Converting to a np array for faster functions later
        print("Converting to numpy arrays...")
        tConvert = time.time()
        file1Arr = file1DF.iloc[:,3:].to_numpy(dtype=int) - 1
        file2Arr = file2DF.iloc[:,3:].to_numpy(dtype=int) - 1
        locationArr = file1DF.iloc[:,0:3].to_numpy(dtype=str)
        print("    Time: ", time.time() - tConvert)
    elif realOrNull.lower() == "null":
        # Converting to a np array for faster functions later
        print("Converting to numpy arrays...")
        tConvert = time.time()
        unshuffledFile1Arr = file1DF.iloc[:,3:].to_numpy(dtype=int) - 1
        unshuffledFile2Arr = file2DF.iloc[:,3:].to_numpy(dtype=int) - 1
        locationArr = file1DF.iloc[:,0:3].to_numpy(dtype=str)
        print("    Time: ", time.time() - tConvert)

        print("Shuffling input matrices...")
        tShuffle = time.time()
        # Combining the arrays for per row shuffling
        combinedArr = np.concatenate((unshuffledFile1Arr, unshuffledFile2Arr), axis=1)

        # Row independent vectorized shuffling of the 2 arrays
        randomIndices = np.argsort(np.random.rand(*combinedArr.shape), axis=1)
        shuffledCombinedArr = np.take_along_axis(combinedArr, randomIndices, axis=1)
        file1Arr = shuffledCombinedArr[:,:unshuffledFile1Arr.shape[1]]
        file2Arr = shuffledCombinedArr[:,unshuffledFile1Arr.shape[1]:]
        print("    Time:", time.time() - tShuffle)
    else:
        print("Error determing whether score calculation is for real or null data")
        return

    print("FILE 1 ARR_______________")
    print(file1Arr[:10])
    print()

    print("FILE2 ARR_________________")
    print(file2Arr[:10])
    print()


    print("Calculating Scores...")
    tScore = time.time()
    score1Arr = determineSaliency(saliency, file1Arr, numStates, expFreqArr)
    score2Arr = determineSaliency(saliency, file2Arr, numStates, expFreqArr)
    print("    Time: ", time.time() - tScore)

    print("Calculating Raw Differences...")
    tDiff = time.time()
    diffArr = score1Arr - score2Arr
    print("    Time:", time.time() - tDiff)

    print("Score Arr 1:")
    print(score1Arr[:10])

    print()
    print("Score Arr 2:")
    print(score2Arr[:10])

    print()
    print("Diff Arr")
    print(diffArr[:10])

    # Only calculate the distances for the null data in this step
    if realOrNull.lower() == "null":
        print("Calculating Squared Euclidean Distance and Maximum Contributing Difference...")
        tDistance = time.time()
        diffSign = np.sign(np.sum(diffArr, axis=1))
        nullDistancesArr = np.sum(np.square(diffArr), axis=1) * diffSign
        print("    Time:", time.time() - tDistance)

    print("Writing output to disk...")
    tWrite = time.time()
    # If it's the real data, we will just write the delta and calculate metrics in computeEpilogosPairwiseVisual
    # If it's the null data, we will just write the signed squared euclidean distances
    if realOrNull.lower() == "real":
        writeReal(locationArr, diffArr, outputDirPath, fileTag)
    elif realOrNull.lower() == "null":
        writeNull(locationArr, nullDistancesArr, outputDirPath, fileTag)
    else:
        print("Error determining if writing real or null data")
        return
    print("    Time:", time.time() - tWrite)

    print("Total Time:", time.time() - tTotal)

# Helper function to determine the pick the correct saliency function
def determineSaliency(saliency, fileArr, numStates, expFreqArr):
    if saliency == 1:
        return s1Score(fileArr, numStates, expFreqArr)
    elif saliency == 2:
        return s2Score(fileArr, numStates, expFreqArr)
    elif saliency == 3:
        print("A saliency value of 3 is not supported for pairwise comparison")
        return
    else:
        print("Inputed saliency value not supported")
        return


# Function that calculates the scores for the S1 metric
def s1Score(dataArr, numStates, expFreqArr):
    numRows, numCols = dataArr.shape

    # Calculate the observed frequencies and final scores in one loop
    scoreArr = np.zeros((numRows, numStates))
    for row in range(numRows):
        uniqueStates, stateCounts = np.unique(dataArr[row], return_counts=True)
        for i in range(len(uniqueStates)):
            # Function input is obsFreq and expFreq
            scoreArr[row, uniqueStates[i]] = klScore(stateCounts[i] / (numCols), expFreqArr[uniqueStates[i]])

    return scoreArr


# Function that calculates the scores for the S2 metric
def s2Score(dataArr, numStates, expFreqArr):
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

    # Calculate the actual scores using the just calculated obsFreqArr and the previously calculated expFreqArr
    scoreArr = np.zeros((numRows, numStates))
    for row in range(numRows):
        scoreArr[row] = klScoreND(obsFreqArr[row], expFreqArr).sum(axis=0)

    return scoreArr


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


# Helper for writing when we are working with real data
def writeReal(locationArr, diffArr, outputDirPath, fileTag):
    if not outputDirPath.exists():
        outputDirPath.mkdir(parents=True)

    deltaTxtPath = outputDirPath / "pairwiseDelta_{}.txt.gz".format(fileTag)
    deltaTxt = gzip.open(deltaTxtPath, "wt")

    # Creating a string to write out the raw differences (faster than np.savetxt)
    deltaTemplate = "{0[0]}\t{0[1]}\t{0[2]}\t" + "".join("{1[%d]:.5f}\t" % i for i in range(diffArr.shape[1] - 1)) + "{1[%d]:.5f}\n" % (diffArr.shape[1] - 1)
    deltaStr = "".join(deltaTemplate.format(locationArr[i], diffArr[i]) for i in range(diffArr.shape[0]))

    deltaTxt.write(deltaStr)
    deltaTxt.close()


# Helper for writing when we are working with null data
def writeNull(locationArr, nullDistancesArr, outputDirPath, fileTag):
    if not outputDirPath.exists():
        outputDirPath.mkdir(parents=True)

    nullDistancesTxtPath = outputDirPath / "nullDistances_{}.txt.gz".format(fileTag)
    nullDistancesTxt = gzip.open(nullDistancesTxtPath, "wt")

    # Creating a string to write out the nullDistancess array
    nullDistancesTemplate = "{0[0]}\t{0[1]}\t{0[2]}\t{1}\n"
    nullDistancesStr = "".join(nullDistancesTemplate.format(locationArr[i], nullDistancesArr[i]) for i in range(len(nullDistancesArr)))

    nullDistancesTxt.write(nullDistancesStr)
    nullDistancesTxt.close()


# Helper to store the score arrays combined with the location arrays
def storeScores(dataArr, scoreArr, locationArr, outputDirPath, fileTag, filename):
    # Creating a file path
    scoreFilename = "temp_scores_{}_{}.npy".format(fileTag, filename)
    scoreFilePath = outputDirPath / scoreFilename

    # Concatenating the locationArr and dataArr into one helps writing later
    combinedArr = np.concatenate((locationArr, scoreArr), axis=1)

    np.save(scoreFilePath, combinedArr, allow_pickle=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6], sys.argv[7])