import sys
from pathlib import Path
import os
import subprocess
import scipy.stats as st

def main(file1, file2, outputDir, binEnd):
    print("Submitting Slurm Jobs....")

    distributions = [st.betaprime, st.halfgennorm, st.pareto, st.lomax, st.genpareto, st.gamma, 
                    st.genexpon, st.expon, st.mielke, st.exponweib, st.loglaplace, st.chi, st.chi2,
                    st.nakagami, st.burr, st.ncx2, st.pearson3]

    outputDirPath = Path(outputDir)
    jobIDArr = []
    for distNum in range(len(distributions)):
        jobName = "{}_{}_{}".format(distributions[distNum].name, file1.split(".")[0], file2.split(".")[0])
        jobOutPath = outputDirPath / (".out/" + jobName + ".out")
        jobErrPath = outputDirPath / (".err/" + jobName + ".err")

        # Creating the out and err files for the batch job
        if jobOutPath.exists():
            os.remove(jobOutPath)
        if jobErrPath.exists():
            os.remove(jobErrPath)
        try:
            jout = open(jobOutPath, 'x')
            jout.close()
            jerr = open(jobErrPath, 'x')
            jerr.close()
        except FileExistsError:
            # This error should never occur because we are deleting the files first
            print("ERROR: sbatch '.out' or '.err' file already exists")

        fitDistributionPy = Path.cwd / "fitDistribution.py"

        pythonCommand = "python {} {} {} {} {}".format(fitDistributionPy, file1, file2, distNum, binEnd)

        slurmCommand = "sbatch --job-name={}.job --output={} --error={} --nodes=1 --ntasks=1 --mem-per-cpu=4000 --wrap='{}'".format(jobName, jobOutPath, jobErrPath, pythonCommand)

        sp = subprocess.run(slurmCommand, shell=True, check=True, universal_newlines=True, stdout=subprocess.PIPE)

        if not sp.stdout.startswith("Submitted batch"):
            print("ERROR: sbatch not submitted correctly")

        jobIDArr.append(int(sp.stdout.split()[-1]))

    jobIDStr = str(jobIDArr).strip('[]').replace(" ", "")
    print("    JobIDs:", jobIDStr)
if __name__ == "__main__":
    main(sys.argv[1])