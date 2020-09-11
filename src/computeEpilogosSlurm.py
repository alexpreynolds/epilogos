import gzip
import numpy as np
from pathlib import Path
import pandas as pd
import time
import click
import os
import subprocess
from pathlib import PurePath

@click.command()
@click.option("-f", "--file-directory", "fileDirectory", type=str, required=True, help="Path to directory that contains files to read from (Please ensure that this directory contains only files you want to read from)")
@click.option("-m", "--state-model", "numStates", type=int, required=True, help="Number of states in chromatin state model")
@click.option("-s", "--saliency-level", "saliency", type=int, required=True, help="Saliency level (1, 2, or 3)")
@click.option("-o", "--output-directory", "outputDirectory", type=str, required=True, help="Output Directory")
@click.option("-e", "--store-expected", "storeExp", is_flag=True, help="[Flag] Store the expected frequency array for later calculations (Must be used in conjunction with '-d' and cannot be used in conjunction with '-u')")
@click.option("-u", "--use-expected", "useStoredExp", is_flag=True, help="[Flag] Use previously stored expected frequency array (Must be used in conjunction with '-d' and cannot be used in conjunction with '-e')")
@click.option("-d", "--expected-directory", "expFreqDir", type=str, default="null", help="Path to the stored expected frequency array (Must be used in conjunction with either '-e' or '-u')")
def main(fileDirectory, numStates, saliency, outputDirectory, storeExp, useStoredExp, expFreqDir):
    tTotal = time.time()
    dataFilePath = Path(fileDirectory)
    outputDirPath = Path(outputDirectory)

    fileTag = "_".join(str(dataFilePath).split("/")[-5:])

    print("FILETAG: ", fileTag)
    print("CWD: ", Path.cwd())

    print("DataFilePath Absolute: ", dataFilePath.is_absolute)
    print("outputDirPath Absolute: ", outputDirPath.is_absolute)

    if not PurePath(outputDirPath).is_absolute():
        outputDirPath = Path.cwd() / outputDirPath

    if not PurePath(dataFilePath).is_absolute():
        dataFilePath = Path.cwd() / dataFilePath

    print("DataFilePath Absolute: ", dataFilePath.is_absolute)
    print("outputDirPath Absolute: ", outputDirPath.is_absolute)

    # Check that paths are valid before doing anything
    if not dataFilePath.exists() or not dataFilePath.is_dir():
        print("ERROR: Given file path does not exist or is not a directory")
        return

    if list(dataFilePath.glob("*")):
        print("ERROR: Ensure that file directory is not empty")

    # If the output directory does not exist yet, make it for the user 
    if not outputDirPath.exists():
        outputDirPath.mkdir(parents=True)

    if not outputDirPath.is_dir():
        print("ERROR: Output directory is not a directory")
        return

    # Calculate the number of epigenomes (just read one line of one of the data files)
    for x in dataFilePath.glob("*"):
        numEpigenomes = pd.read_table(x, header=None, sep="\t", nrows=1).shape[1] - 3
        break

    # Path for storing/retrieving the expected frequency array
    # Expected frequency arrays are stored according to the number of epigenomes, number of states, and saliency metric involved in the calculation
    if expFreqDir != "null":
        expFreqFilename = "exp_freq_{}.npy".format(fileTag)#.format(numEpigenomes, numStates, saliency)
        storedExpPath = Path(expFreqDir) / expFreqFilename

    # Finding the location of the .py files that must be run
    if PurePath(__file__).is_absolute():
        pythonFilesDir = Path(__file__).parents[0]
    else:
        pythonFilesDir = Path.cwd() / Path(__file__).parents[0]

    # Check if its already been calculated before
    if useStoredExp:
        try:
            expFreqArr = np.load(storedExpPath, allow_pickle=False)
        except IOError:
            print("ERROR: Could not load stored expected value array.\n\tPlease check that the directory is correct or that the file exists")
    else:     
        expJobIDArr = []   
        print("Calculating expected frequencies....")
        for file in dataFilePath.glob("*"):
            if not file.is_dir():
                filename = file.name.split(".")[0]
                jobName = "exp_freq_calc_{}_{}".format(fileTag, filename)
                jobOutPath = outputDirPath / (".out/" + jobName + ".out")
                jobErrPath = outputDirPath / (".err/" + jobName + ".err")

                # Creating the out and err files for the batch job
                try:
                    jout = open(jobOutPath, 'x')
                    jout.close()
                    jerr = open(jobErrPath, 'x')
                    jerr.close()
                except FileExistsError:
                    print("ERROR: sbatch '.out' or '.err' file already exists")

                computeExpectedPy = pythonFilesDir / "computeEpilogosExpected.py"

                pythonCommand = "python {} {} {} {} {}".format(computeExpectedPy, file, numStates, saliency, outputDirPath, fileTag)

                slurmCommand = "sbatch --job-name={}.job --output={} --error={} --nodes=1 --ntasks=1 --wrap='{}'".format(jobName, jobOutPath, jobErrPath, pythonCommand)

                print(pythonCommand)
                print(slurmCommand)

                # sp = subprocess.run(slurmCommand, shell=True, check=True, universal_newlines=True)

                # if not sp.stdout.startswith("Submitted batch"):
                #     print("ERROR: sbatch not submitted correctly")
                
                # expJobIDArr.append(int(sp.stdout.split()[-1]))

        # Combining all the different chromosome expected frequency arrays into one
        # create a string for slurm dependency to work
        for i in range(10):
            teststr = "Submitted batch {}".format(i)
            expJobIDArr.append(int(teststr.split()[-1]))
        jobIDStrComb = str(expJobIDArr).strip('[]').replace(" ", "")
        print("expJobIDArr: ", expJobIDArr)
        print("jobIDStrComb: ", jobIDStrComb)

        print("Combining expected frequencies....")

        jobName = "exp_freq_comb_{}".format(fileTag)
        jobOutPath = outputDirPath / (".out/" + jobName + ".out")
        jobErrPath = outputDirPath / (".err/" + jobName + ".err")

        # Creating the out and err files for the batch job
        try:
            jout = open(jobOutPath, 'x')
            jout.close()
            jerr = open(jobErrPath, 'x')
            jerr.close()
        except FileExistsError:
            print("ERROR: sbatch '.out' or '.err' file already exists")

        computeExpectedCombinationPy = pythonFilesDir / "computeEpilogosExpectedCombination.py"

        pythonCommand = "python {} {} {} {} {}".format(computeExpectedCombinationPy, outputDirPath, fileTag, storeExp, storedExpPath)

        slurmCommand = "sbatch --dependency=afterok:{} --job-name={}.job --output={} --error={} --nodes=1 --ntasks=1 --wrap='{}'".format(jobIDStrComb, jobName, jobOutPath, jobErrPath, pythonCommand)

        print(pythonCommand)
        print(slurmCommand)

        # sp = subprocess.run(slurmCommand, shell=True, check=True, universal_newlines=True)

        # if not sp.stdout.startswith("Submitted batch"):
        #     print("ERROR: sbatch not submitted correctly")
        
        # combinationJobID = int(sp.stdout.split()[-1])
        combinationJobId = 1

    # Calculate the observed frequencies and scores
    print("Calculating Scores....")
    expFreqFilename = "temp_exp_freq_{}.npy".format(fileTag)
    expFreqPath = outputDirPath / expFreqFilename
    scoreJobIDArr = []
    for file in dataFilePath.glob("*"):
        if not file.is_dir():
            filename = file.name.split(".")[0]
            jobName = "score_calc_{}_{}".format(fileTag, filename)
            jobOutPath = outputDirPath / (".out/" + jobName + ".out")
            jobErrPath = outputDirPath / (".err/" + jobName + ".err")

            # Creating the out and err files for the batch job
            try:
                jout = open(jobOutPath, 'x')
                jout.close()
                jerr = open(jobErrPath, 'x')
                jerr.close()
            except FileExistsError:
                print("ERROR: sbatch '.out' or '.err' file already exists")
            
            computeScorePy = pythonFilesDir / "computeEpilogosScores.py"

            pythonCommand = "python {} {} {} {} {} {}".format(computeScorePy, file, numStates, saliency, outputDirPath, expFreqPath)
            slurmCommand = "sbatch --dependency=afterok:{} --job-name={}.job --output={} --error={} --nodes=1 --ntasks=1 --wrap='{}'".format(combinationJobID, jobName, jobOutPath, jobErrPath, pythonCommand)

            print(pythonCommand)
            print(slurmCommand)

            # sp = subprocess.run(slurmCommand, shell=True, check=True, universal_newlines=True)

            # if not sp.stdout.startswith("Submitted batch"):
            #     print("ERROR: sbatch not submitted correctly")
            
            # scoreJobIDArr.append(int(sp.stdout.split()[-1]))

    # WRITING TO SCORE FILES
    print("Writing to score files....")
    # create a string for slurm dependency to work
    for i in range(10):
        teststr = "Submitted batch {}".format(i)
        scoreJobIDArr.append(int(teststr.split()[-1]))
    jobIDStrWrite = str(scoreJobIDArr).strip('[]').replace(" ", "")
    print("scoreJobIDArr: ", scoreJobIDArr)
    print("jobIDStrWrite: ", jobIDStrWrite)


    jobName = "write_{}".format(fileTag)
    jobOutPath = outputDirPath / (".out/" + jobName + ".out")
    jobErrPath = outputDirPath / (".err/" + jobName + ".err")

    # Creating the out and err files for the batch job
    try:
        jout = open(jobOutPath, 'x')
        jout.close()
        jerr = open(jobErrPath, 'x')
        jerr.close()
    except FileExistsError:
        print("ERROR: sbatch '.out' or '.err' file already exists")

    computeExpectedWritePy = pythonFilesDir / "computeEpilogosWrite.py"

    pythonCommand = "python {} {} {} {}".format(computeExpectedWritePy, fileTag, outputDirPath, numStates)

    slurmCommand = "sbatch --dependency=afterok:{} --job-name={}.job --output={} --error={} --nodes=1 --ntasks=1 --wrap='{}'".format(jobIDStrWrite, jobName, jobOutPath, jobErrPath, pythonCommand)

    print(pythonCommand)
    print(slurmCommand)

    # sp = subprocess.run(slurmCommand, shell=True, check=True, universal_newlines=True)

    # if not sp.stdout.startswith("Submitted batch"):
    #     print("ERROR: sbatch not submitted correctly")

if __name__ == "__main__":
    main()