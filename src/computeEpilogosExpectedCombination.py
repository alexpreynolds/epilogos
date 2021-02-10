import sys
import numpy as np
import os
from pathlib import Path
import time

def main(outputDirectory, storedExpInput, fileTag):
    tTotal = time.time()

    outputDirPath = Path(outputDirectory)
    storedExpPath = Path(storedExpInput)

    # Loop over all the expected value arrays and add them up
    expFreqFileCount = 0
    expFreqArr = np.zeros((1,1))
    for file in outputDirPath.glob("temp_exp_freq_{}_*.npy".format(fileTag)):
        if expFreqFileCount == 0:
            expFreqArr = np.load(file, allow_pickle=False)
        else:
            expFreqArr += np.load(file, allow_pickle=False)
        expFreqFileCount += 1
    
    # Clean up temp files
    for file in outputDirPath.glob("temp_exp_freq_*.npy"):
        os.remove(file)

    # normalize expected frequency array
    expFreqArr = (expFreqArr / np.sum(expFreqArr)).astype(np.float32)

    print("Total Sum:", np.sum(expFreqArr))

    # Save the expected frequency array
    np.save(storedExpPath, expFreqArr, allow_pickle=False)

    print("Total Time:", time.time() - tTotal)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

