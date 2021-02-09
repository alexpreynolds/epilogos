import math
import time
import operator as op
import numpy as np
from functools import reduce
import multiprocessing
import ctypes as c
import itertools
import random
from pathlib import Path
import glob
import pandas as pd
import os
import sys
import subprocess
from pathlib import PurePath
import glob
import gzip
import numpy.ma as ma
import click

def main(file1, file2, numStates):
    
    # file1Path = Path(file1)
    # file2Path = Path(file2)
    
    # colNames = ["chr", "binStart", "binEnd"] + ["s{}".format(i) for i in range(1, numStates+1)]
    # chrOrder = []
    # for i in range(1, 23):
    #     chrOrder.append("chr{}".format(i))
    # chrOrder.append("chrX")

    # print("\nReading data from file 1...")
    # tRead1 = time.time()
    # file1DF = pd.read_table(file1Path, header=None, sep="\t", names=colNames)
    # print("    Time: ", time.time() - tRead1)

    # if "all127" in file1.split("/"):
    #     for chr in chrOrder:
    #         index = file1DF["chr"].where(file1DF["chr"] == chr).last_valid_index()
    #         file1DF.drop(index, inplace=True)

    # print("Reading data from file 2...")
    # tRead2 = time.time()
    # file2DF = pd.read_table(file2Path, header=None, sep="\t", names=colNames)
    # print("    Time: ", time.time() - tRead2)

    # # Sorting the dataframes by chromosomal location
    # file1DF["chr"] = pd.Categorical(file1DF["chr"], categories=chrOrder, ordered=True)
    # file2DF["chr"] = pd.Categorical(file2DF["chr"], categories=chrOrder, ordered=True)
    # file1DF.sort_values(by=["chr", "binStart", "binEnd"], inplace=True)
    # file2DF.sort_values(by=["chr", "binStart", "binEnd"], inplace=True)

    # print(file1DF.shape)
    # print(file2DF.shape)

    # print("Converting to numpy arrays...")
    # tConvert = time.time()
    # file1Arr = file1DF.iloc[:,3:].to_numpy(dtype=int)
    # file2Arr = file2DF.iloc[:,3:].to_numpy(dtype=int)
    # print("    Time: ", time.time() - tConvert)

    # print("Calculating percent difference...")
    # tDiff = time.time()
    # maxStateArr1 = np.argmax(file1Arr, axis=1) + 1
    # maxStateArr2 = np.argmax(file2Arr, axis=1) + 1
    # error = np.mean(maxStateArr1 != maxStateArr2)
    # print("    Time: ", time.time() - tDiff)
    
    # print("Percent Difference is:", error)








    # print("\nReading python expFreqARr")
    # pythonArr = np.load(Path(file1), allow_pickle=False)

    print("\nReading c expFreqARr")
    tRead1 = time.time()
    file2DF = pd.read_table(Path(file2), header=None, sep="\t")
    print("    Time: ", time.time() - tRead1)

    print("Converting to numpy arrays...")
    tConvert = time.time()
    file2Arr = file2DF.to_numpy(dtype=int)
    print("    Time: ", time.time() - tConvert)

    print(file2Arr.shape)

    numCols = 127

    epigenomeCombinations = np.array(list(itertools.combinations(range(numCols), 2)), dtype=np.int16).T
    stateCombinations = np.array(list(itertools.product(range(numStates), repeat=2)), dtype=np.int16).T

    cArr = np.zeros((numCols, numCols, numStates, numStates), dtype=np.float32)

    # loop over all rows in erics txt file
    print("putting txt into numpy array...")
    for i in range(file2Arr.shape[0]):
        for j in range(file2Arr.shape[1]):
            cArr[epigenomeCombinations[0, i], epigenomeCombinations[1, i], stateCombinations[0, j], stateCombinations[1, j]] = file2Arr[i, j]
            cArr[epigenomeCombinations[1, i], epigenomeCombinations[0, i], stateCombinations[0, j], stateCombinations[1, j]] = file2Arr[i, j]
    
    cArr /= (15181508 * numCols * (numCols - 1))

    print("C Arr contains zeros?", np.isin(cArr, np.array([0])))

    # print("Calculating top 100...")
    # diffArr = np.abs(pythonArr - cArr)

    # sortedIndices = np.argsort(-diffArr, axis=None)[:100]

    # fourDIndices = np.unravel_index(sortedIndices, (numCols, numCols, numStates, numStates))

    # flatPython = pythonArr.flatten()
    # flatC = cArr.flatten()
    # flatDiff = diffArr.flatten()

    # for i in range(100):
    #     print("{}. Python: {}\t\tC: {}\t\tDiff: {}\t\tIndices:({},{},{},{})".format(i, flatPython[sortedIndices[i]], flatC[sortedIndices[i]], flatDiff[sortedIndices[i]], fourDIndices[0][i], fourDIndices[1][i], fourDIndices[2][i], fourDIndices[3][i]))


    # print(np.sum(pythonArr))
    # print(np.sum(cArr))


    print("\nReading c expFreqARr")
    tRead1 = time.time()
    wholeGenomeDF = pd.read_table(Path("/home/jquon/RoadmapStateByGroup/all127/matrix.txt.gz"), header=None, sep="\t")
    print("    Time: ", time.time() - tRead1)

    print("Converting to numpy arrays...")
    tConvert = time.time()
    genomeArr = wholeGenomeDF[:, 3:].to_numpy(dtype=int)
    print("    Time: ", time.time() - tConvert)


    # where column 107 == 2 and column 72 == 10
    print("1.", np.where((genomeArr[:, 107] == 2) & (genomeArr[:, 72] == 10))[0])

    # where column 114 == 2 and column 75 == 10
    print("2.", np.where((genomeArr[:, 114] == 9) & (genomeArr[:, 75] == 5))[0])
    
    # where column 107 == 3 and column 98 == 1
    print("3.", np.where((genomeArr[:, 107] == 3) & (genomeArr[:, 98] == 1))[0])

    # where column 107 == 3 and column 98 == 0
    print("4.", np.where((genomeArr[:, 107] == 3) & (genomeArr[:, 98] == 0))[0])

    # where column 69 == 3 and column 27 == 9
    print("5.", np.where((genomeArr[:, 69] == 3) & (genomeArr[:, 27] == 9))[0])

    # where column 69 == 3 and column 27 == 10
    print("6.", np.where((genomeArr[:, 69] == 3) & (genomeArr[:, 27] == 10))[0])

    # where column 114 == 10 and column 75 == 2
    print("7.", np.where((genomeArr[:, 114] == 10) & (genomeArr[:, 75] == 2))[0])

    # where column 69 == 3 and column 27 == 10
    print("8.", np.where((genomeArr[:, 69] == 5) & (genomeArr[:, 27] == 9))[0])

    


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))