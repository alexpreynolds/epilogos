<h1 align="center">
  <a href="https://github.com/meuleman/epilogos"><img src="./data/logo.png" width="840"></a>
</h1>

---

<h2 align="center">
    Information-theoretic navigation of multi-tissue functional genomic annotations
</h2>

Epilogos is an approach for analyzing, visualizing, and navigating multi-biosample functional genomic annotations, with an emphasis on chromatin state maps generated with e.g. ChromHMM or Segway.

The software provided in this repository implements the methods underlying Epilogos using only python. We provide a proof-of-principle dataset based on chromatin state calls from the BOIX dataset.

---

<div align="center"><a name="menu"></a>
  <h3>
    <a href="#prerequisites">Prerequisites</a> •
    <a href="#installation">Installation</a> •
    <a href="#running-epilogos">Running Epilogos</a> •
    <a href="#slurm-examples">SLURM Examples</a> •
    <a href="#non-slurm-examples">Non-SLURM Examples</a> •
    <a href="#command-line-options">Command Line Options</a> •
    <a href="#pairwise-epilogos">Pairwise Epilogos</a>
  </h3>
</div>

---

<br>


<a name="prerequisites"></a>

## Prerequisites

To compute epilogos, you will need to have the following python libraries: [click](https://click.palletsprojects.com/en/7.x/), [numpy](https://numpy.org/), [scipy](https://www.scipy.org/), [matplotlib](https://matplotlib.org/stable/index.html), and [pandas](https://pandas.pydata.org/). These can be installed with one of the following commands.
```bash
$ pip install click, numpy, scipy, matplotlib, pandas
```
or while in the epilogos directory
```bash
$ pip install requirements.txt
```

Additionally, it is recommended that python is updated to version 3.7 or later. In earlier versions, `src/computeEpilogosScores.py` may raise an OSError 16. It is worth noting that in our testing this error has not affected the results. 

<a name="installation"></a>

## Installation

To install Epilogos simply run the following command
```bash
$ pip install epilogos
```

<a name="running-epilogos"></a>

## Running Epilogos

To be presented with minimal documentation of arguments needed to run epilogos, simply run the command `epilogos --help` (More in-depth explanation is given [below](#command-line-options))

By default, Epilogos assumes access to a computational cluster managed by [SLURM](https://slurm.schedmd.com/). A version of epilogos has been created for those without access to a SLURM cluster and can be run by using the `-l` flag to your command (e.g. `epilogos -l`).

<a name="slurm-examples"></a>

## SLURM Examples

<details><summary><b> Minimal example on provided example data</b></summary>
<p></p>

<p>Example data has been provided under <code>data/pyData/male/</code>. The file, <code>epilogos_matrix_chr1.txt.gz</code>, contains chromatin state calls for a 18-state chromatin model, across 200bp genomic bins spanning human chromosome 1. The data was pulled from the <a href="https://docs.google.com/spreadsheets/d/103XbiwChp9sJhUXDJr9ztYEPL00_MqvJgYPG-KZ7WME/edit#gid=1813267486">BOIX dataset</a> and contains only those epigenomes which are tagged <code>Male</code> under the <code>Sex</code> column.</p>

<p>To compute epilogos (using the S1 saliency metric) for this sample data run following command within the <code></code> directory (replacing <code>OUTPUTDIR</code> with the output directory of your choice).</p>

```bash
$ epilogos -i data/pyData/male/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR
```

<p>Upon completion of the run, you should see the files <code>scores_male_s1_epilogos_matrix_chr1.txt.gz</code> and <code>greatestHits_male_s1.txt</code> in <code>OUTPUTDIR</code></p>

<p>To customize your run of epilogos see the <a href="#command-line-options">Command Line Options</a> of the <code>README</code></p>

</details>

<details><summary><b> Running Epilogos with your own data</b></summary>
<p></p>

<p>In order to run Epilogos on your own data, you will need to do two things.</p>

<p>First, you will need to modify your data such that Epilogos can understand it. In order to assist with this, we have provided a bash script which takes ChromHMM files and generates Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```

<p>Second, you will need to create a state info file. This is a tab separated file which tells epilogos various information about each of the states in the state model. We have provided some files already for common models in the <code>data/state_metadata/</code> directory. For more information on the structure of these files see <code>data/state_metadata/README.txt</code> or <a href="#state-info">State Info [-n, --state-info]</a></p>

<p>Once you have completed these two things, you can run epilogos with the following command:</p>

```bash
$ epilogos -i PATH_TO_INPUT_DIR -n PATH_TO_STATE_INFO_TSV -o PATH_TO_OUTPUT_DIR
```

<p>Upon completion of the run, you should see the same number of scores files as in your input directory in <code>OUTPUTDIR</code>. Each of these files will be named <code>scores_*.txt.gz</code>, where 'scores_' is followed by the input directory name, the saliency metric, and the corresponding input file name (extensions removed). Additionally, you will find a <code>greatestHits_*.txt</code> file which follows the same naming convention except for the input file name.</p>

<p>If you would like to visualize these results as on <a href="epilogos.altius.org">epilogos.altius.org</a>, we recommend using higlass.</p>

<p>To further customize your run of epilogos see the <a href="#command-line-options-pairwise">Command Line Options</a> of the <code>README</code></p>

</details>

<a name="non-slurm-examples"></a>

## Non-SLURM Examples

<details><summary><b> Minimal example on provided example data</b></summary>
<p></p>

<p>Example data has been provided under <code>data/pyData/male/</code>. The file, <code>epilogos_matrix_chr1.txt.gz</code>, contains chromatin state calls for a 18-state chromatin model, across 200bp genomic bins spanning human chromosome 1. The data was pulled from the <a href="https://docs.google.com/spreadsheets/d/103XbiwChp9sJhUXDJr9ztYEPL00_MqvJgYPG-KZ7WME/edit#gid=1813267486">BOIX dataset</a> and contains only those epigenomes which are tagged <code>Male</code> under the <code>Sex</code> column.</p>

<p>To compute epilogos (using the S1 saliency metric) for this sample data run following command within the <code></code> directory (replacing <code>OUTPUTDIR</code> with the output directory of your choice).</p>

```bash
$ epilogos -l -i data/pyData/male/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR
```

<p>Upon completion of the run, you should see the file <code>scores_male_s1_epilogos_matrix_chr1.txt.gz</code> and <code>greatestHits_male_s1.txt</code> in <code>OUTPUTDIR</code></p>

<p>To customize your run of epilogos see the <a href="#command-line-options">Command Line Options</a> of the <code>README</code></p>

</details>


<details><summary><b> Running Epilogos with your own data</b></summary>
<p></p>

<p>In order to run Epilogos on your own data, you will need to do two things.</p>

<p>First, you will need to modify your data such that Epilogos can understand it. In order to assist with this, we have provided a bash script which takes ChromHMM files and generates Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```

<p>Second, you will need to create a state info file. This is a tab separated file which tells epilogos various information about each of the states in the state model. We have provided some files already for common models in the <code>data/state_metadata/</code> directory. For more information on the structure of these files see <code>data/state_metadata/README.txt</code> or <a href="#state-info">State Info [-n, --state-info]</a></p>

<p>Once you have completed these two things, you can run epilogos with the following command:</p>

```bash
$ epilogos -l -i PATH_TO_INPUT_DIR -n PATH_TO_STATE_INFO_TSV -o PATH_TO_OUTPUT_DIR
```

<p>Upon completion of the run, you should see the same number of scores files as in your input directory in <code>OUTPUTDIR</code>. Each of these files will be named <code>scores_*.txt.gz</code>, where 'scores_' is followed by the input directory name, the saliency metric, and the corresponding input file name (extensions removed). Additionally, you will find a <code>greatestHits_*.txt</code> file which follows the same naming convention except for the input file name.</p>

<p>If you would like to visualize these results as on <a href="epilogos.altius.org">epilogos.altius.org</a>, we recommend using higlass.</p>

<p>To further customize your run of epilogos see the <a href="#command-line-options">Command Line Options</a> of the <code>README</code></p>

</details>


<a name="command-line-options"></a>

## Command Line Options

<a name="mode"></a>
<details><summary><b> Mode [-m, --mode]</b></summary>
<p></p>
<p>Epilogos supports a single group and a paired group mode. The single group mode finds interesting regions compared to a background of itself. Whereas the paired group mode finds regions which differ significantly between the two groups.</p>

<p>
The argument to this flag either <code>single</code> or <code>paired</code> as the mode of operation, with <code>single</code> being the default.
</p>
</details>

<a name="command-line"></a>
<details><summary><b> Command Line [-l, --cli]</b></summary>
<p></p>
<p>By default, Epilogos assumes use of a SLURM cluster. However, if you would like to run Epilogos directly in the command line enable this flag</p>
</details>

<a name="input-directory"></a>
<details><summary><b> Input Directory [-i, --input-directory]</b></summary>
<p></p>
<p>Rather than just read in one input file, Epilogos reads the contents of an entire directory. This allows the computation to be chunked and parallelized. Note that the genome files in the directory <strong>MUST</strong> be split by chromosome. Input files should be formatted such that the first three columns are the chromosome, bin start, and bin end respectively with the rest of the columns containing state data.</p>

<p>
The argument to this flag is the path to the directory which contains the files to be read in. Note that <strong>ALL</strong> files in this directory will be read in and errors may occur if other files are present.
</p>

<p>Epilogos input data must be formatted specifically for Epilogos. In order to help you create your own input data files, we have provided a script to transform chromHMM files into Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```
</details>

<a name="output-directory"></a>
<details><summary><b> Output Directory [-o, --output-directory]</b></summary>
<p></p>
<p>
The output of Epilogos will vary depending on the number of input files present in the input directory <a href="#input-directory">[-i, --input-directory]</a>. All scores files will be gzipped txt files and of the format <code>scores_*.txt.gz</code> where 'scores_' is followed by the input directory name, the saliency metric, and the corresponding input file name (extensions removed).</p>

<p>Additionally, you will find a <code>greatestHits_*.txt</code> file which follows the same naming convention except for the input file name. This file contains the top 1000 highest scoring regions (with adjacent regions merged). Columns 1-3 contain the locations, column 4 contains name of the largest scoring states, column 5 contains the scores, and column 6 contains the direction of these scores.</p>

<p>
The argument to this flag is the path to the directory to which you would like to output. Note that this may not be the same as the input directory.</p>
</details>

<a name="state-info"></a>
<details><summary><b> State Info [-n, --state-info]</b></summary>
<p></p>
<p>The argument to this flag is a tab separated file specifying information about the state model being used. Example below (for more detail see <code>epilogos/data/state_metadata/README.md</code> or <code>epilogos/data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv</code></p>

| zero_index | one_index | short_name | long_name | hex | rgba | color |
|------------|-----------|------------|-----------|-----|------|-------|
| 0 | 1 | TssA | Active TSS | #ff0000 | rgba(255,0,0,1) | Red |

<p>
Note that tsv must contain a header row with the exact names above and that values within the table should follow the same formatting as above.
</p>
</details>

<a name="saliency"></a>
<details><summary><b> Saliency Level [-s, --saliency]</b></summary>
<p></p>
<p>Epilogos implements information-theoretic metrics to quantify saliency levels of datasets. The <code>-l</code> flag to the coordination script allows one to choose one of three possible metrics:</p>

```
1. Metric S1, implementing a standard Kullback-Leibler relative entropy

2. Metric S2, implementing a version of S1 that additionally models label co-occurrence patterns

3. Metric S3, implementing a version of S2 that additionally models between-biosample similarities
```

<p>
Note that each increase in saliency level involves much more computation and thus each increase requires more time and computational power.
</p>

<p>
The arguement to this flag must be an integer <code>1, 2, or 3</code>. Note that Epilogos defaults to a saliency of 1.
</p>

<p>Example:</p>

```bash
Saliency 1: $ epilogos -i data/pyData/male/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR

Saliency 2: $ epilogos -i data/pyData/male/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR -s 2

Saliency 3: $ epilogos -i data/pyData/male/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR -s 3
```

</details>

<a name="number-of-cores"></a>
<details><summary><b> Number of Cores [-c, --num-cores]</b></summary>
<p></p>
<p>Epilogos will always try and parallelize where it can. Computation done on each input file is parallelized using python's <a href="https://docs.python.org/3/library/multiprocessing.html">multiprocessing library</a>.</p>

<p>
The argument to this flag is an integer number of cores you would like to utilize to perform this multiprocessing. Note that Epilogos defaults to using all available cores (equivalent to <code>-c 0</code>).</p>
</details>

<a name="exit"></a>
<details><summary><b> Exit [-x, --exit]</b></summary>
<p></p>
<p>By default <code>src/computeEpilogosSlurm.py</code> only exits after it has completed all slurm jobs and prints progress updates to the console. If you would like the program to instead exit when all jobs are submitted (allowing use of the terminal while the jobs are running), enable this flag.</p>
</details>

<br>
<br>

<a name="pairwise-epilogos"></a>

<h2 align="center">
    Pairwise Epilogos
</h2>

Pairwise Epilogos, like Epilogos, is an approach for analyzing, visualizing, and navigating multi-biosample functional genomic annotations. However, its role is to provide a structure by which to compare these genomic annotations accross different groups.

The software provided in this repository implements the methods underlying Pairwise Epilogos using only python. We provide a proof-of-principle dataset based on chromatin state calls from the BOIX dataset.

---

<div align="center"><a name="menu"></a>
  <h3>
    <a href="#running-epilogos-pairwise">Running Pairwise Epilogos</a> •
    <a href="#slurm-examples-pairwise">SLURM Examples</a> •
    <a href="#non-slurm-examples-pairwise">Non-SLURM Examples</a> •
    <a href="#command-line-options-pairwise">Command Line Options</a> •
    <a href="#visual-output">Visual Output</a> •
  </h3>
</div>

---

<br>

<a name="running-epilogos-pairwise"></a>

## Running Pairwise Epilogos

To be presented with minimal documentation of arguments needed to run epilogos, simply run the command `epilogos --help` (More in-depth explanation is given [below](#command-line-options-pairwise))

By default, Epilogos assumes access to a computational cluster managed by [SLURM](https://slurm.schedmd.com/). A version of epilogos has been created for those without access to a SLURM cluster and can be run by using the `-l` flag to your command (e.g. `epilogos -l`).

<a name="slurm-examples-pairwise"></a>

## SLURM Examples

<details><summary><b> Minimal example on provided example data</b></summary>
<p></p>

<p>Example data has been provided under <code>data/pyData/male/</code> and <code>data/pyData/female/</code>. The files, both named <code>epilogos_matrix_chr1.txt.gz</code>, contain chromatin state calls for a 18-state chromatin model, across 200bp genomic bins spanning human chromosome 1. The data was pulled from the <a href="https://docs.google.com/spreadsheets/d/103XbiwChp9sJhUXDJr9ztYEPL00_MqvJgYPG-KZ7WME/edit#gid=1813267486">BOIX dataset</a> and contains only those epigenomes which are tagged <code>Male</code> or <code>Female</code> respectively under the <code>Sex</code> column.</p>

<p>To compute epilogos (using the S1 saliency metric) for this sample data run following command within the <code></code> directory (replacing <code>OUTPUTDIR</code> with the output directory of your choice).</p>

```bash
$ epilogos -m paired -a data/pyData/male/ -b data/pyData/female/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR
```

<p>Upon completion of the run, you should see the files <code>pairwiseDelta_male_female_s1_epilogos_matrix_chr1.txt.gz</code>, <code>pairwiseMetrics_male_female_s1.txt.gz</code>, <code>significantLoci_male_female_s1.txt</code>, and <code>greatestHits_male_female_s1.txt</code> as well as the directory <code>manhattanPlots_male_female_s1</code> in <code>OUTPUTDIR</code>. For further explanation of the contents of these outputs see <a href="#output-directory-pairwise">Output Directory [-o, --output-directory]</a></p>

<p>To customize your run of epilogos see the <a href="#command-line-options-pairwise">Command Line Options</a> of the <code>README</code></p>

</details>

<details><summary><b> Running Epilogos with your own data</b></summary>
<p></p>

<p>In order to run Epilogos on your own data, you will need to do two things.</p>

<p>First, you will need to modify your data such that Epilogos can understand it. In order to assist with this, we have provided a bash script which takes ChromHMM files and generates Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```

<p>Second, you will need to create a state info file. This is a tab separated file which tells epilogos various information about each of the states in the state model. We have provided some files already for common models in the <code>data/state_metadata/</code> directory. For more information on the structure of these files see <code>data/state_metadata/README.txt</code> or <a href="#state-info">State Info [-n, --state-info]</a></p>

<p>Once you have completed these two things, you can run epilogos with the following command:</p>

```bash
$ epilogos -m paired -a PATH_TO_FIRST_INPUT_DIR -b PATH_TO_SECOND_INPUT_DIR -n PATH_TO_STATE_INFO_TSV -o PATH_TO_OUTPUT_DIR
```

<p>Upon completion of the run, you should see the files <code>pairwiseDelta_*.txt.gz</code>, <code>pairwiseMetrics_*.txt.gz</code>, <code>significantLoci_*.txt</code>, and <code>greatestHits_*.txt</code> as well as the directory <code>manhattanPlots_*</code> in <code>OUTPUTDIR</code>. Each of the wildcards will be replaced by a string containing the name of input directory one, the name of input directory two, the saliency metric, and the corresponding input file name when relevant (extensions removed)</p>

<p>If you would like to visualize these results as on <a href="epilogos.altius.org">epilogos.altius.org</a>, we recommend using higlass.</p>

<p>To further customize your run of epilogos see the <a href="#command-line-options-pairwise">Command Line Options</a> of the <code>README</code></p>

</details>


<a name="non-slurm-examples-pairwise"></a>

## Non-SLURM Examples

<details><summary><b> Minimal example on provided example data</b></summary>
<p></p>

<p>Example data has been provided under <code>data/pyData/male/</code> and <code>data/pyData/female/</code>. The files, both named <code>epilogos_matrix_chr1.txt.gz</code>, contain chromatin state calls for a 18-state chromatin model, across 200bp genomic bins spanning human chromosome 1. The data was pulled from the <a href="https://docs.google.com/spreadsheets/d/103XbiwChp9sJhUXDJr9ztYEPL00_MqvJgYPG-KZ7WME/edit#gid=1813267486">BOIX dataset</a> and contains only those epigenomes which are tagged <code>Male</code> or <code>Female</code> respectively under the <code>Sex</code> column.</p>

<p>To compute epilogos (using the S1 saliency metric) for this sample data run following command within the <code></code> directory (replacing <code>OUTPUTDIR</code> with the output directory of your choice).</p>

```bash
$ epilogos -m paired -l -a data/pyData/male/ -b data/pyData/female/ -n data/state_metadata/human/Adsera_et_al_833_sample/hg19/18/metadata.tsv -o OUTPUTDIR
```

<p>Upon completion of the run, you should see the files <code>pairwiseDelta_male_female_s1_epilogos_matrix_chr1.txt.gz</code>, <code>pairwiseMetrics_male_female_s1.txt.gz</code>, <code>significantLoci_male_female_s1.txt</code>, and <code>greatestHits_male_female_s1.txt</code> as well as the directory <code>manhattanPlots_male_female_s1</code> in <code>OUTPUTDIR</code>. For further explanation of the contents of these outputs see <a href="#output-directory-pairwise">Output Directory [-o, --output-directory]</a></p>

<p>To customize your run of epilogos see the <a href="#command-line-options-pairwise">Command Line Options</a> of the <code>README</code></p>

</details>

<details><summary><b> Running Epilogos with your own data</b></summary>
<p></p>

<p>In order to run Epilogos on your own data, you will need to do two things.</p>

<p>First, you will need to modify your data such that Epilogos can understand it. In order to assist with this, we have provided a bash script which takes ChromHMM files and generates Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```

<p>Second, you will need to create a state info file. This is a tab separated file which tells epilogos various information about each of the states in the state model. We have provided some files already for common models in the <code>data/state_metadata/</code> directory. For more information on the structure of these files see <code>data/state_metadata/README.txt</code> or <a href="#state-info">State Info [-n, --state-info]</a></p>

<p>Once you have completed these two things, you can run epilogos with the following command:</p>

```bash
$ epilogos -m paired -l -a PATH_TO_FIRST_INPUT_DIR -b PATH_TO_SECOND_INPUT_DIR -n PATH_TO_STATE_INFO_TSV -o PATH_TO_OUTPUT_DIR
```

<p>Upon completion of the run, you should see the files <code>pairwiseDelta_*.txt.gz</code>, <code>pairwiseMetrics_*.txt.gz</code>, <code>significantLoci_*.txt</code>, and <code>greatestHits_*.txt</code> as well as the directory <code>manhattanPlots_*</code> in <code>OUTPUTDIR</code>. Each of the wildcards will be replaced by a string containing the name of input directory one, the name of input directory two, the saliency metric, and the corresponding input file name when relevant (extensions removed)</p>

<p>If you would like to visualize these results as on <a href="epilogos.altius.org">epilogos.altius.org</a>, we recommend using higlass.</p>

<p>To further customize your run of epilogos see the <a href="#command-line-options-pairwise">Command Line Options</a> of the <code>README</code></p>

</details>

<a name="command-line-options-pairwise"></a>

## Command Line Options

In addition to the command line options offered for [single group epilogos](#command-line-options), pairwise Epilogos has some options which are unique to it. These are outlined below.

<a name="directories-pairwise"></a>
<details><summary><b> Input Directories One and Two [-a, --directory-one] and [-b, --directory-two]</b></summary>
<p></p>
<p>Rather than just read in one input file, Epilogos reads the contents of an entire directory. This allows the computation to be chunked and parallelized. Note that the genome files in the directory <strong>MUST</strong> be split by chromosome. Input files should be formatted such that the first three columns are the chromosome, bin start, and bin end respectively with the rest of the columns containing state data.</p>

<p>In the paired group version of epilogos, the user must input two directories (one for each group). Note that <strong>ALL</strong> files in this directory will be read in and errors may occur if other files are present. Additionally, the files to compare within the directories must have the same name in both directories (e.g. chr1Male.txt and chr1Female.txt --> chr1.txt and chr1.txt)
</p>

<p>Epilogos input data must be formatted specifically for Epilogos. In order to help you create your own input data files, we have provided a script to transform chromHMM files into Epilogos input files. This can be found at <code>scripts/preprocess_data_ChromHMM.sh</code>. If you would prefer not to use the script, data is to be formatted as follows:</p>

```
Column 1: Chromosome
Column 2: Start coordinate
Column 3: End coordinate
Column 4: State data for epigenome 1
...
Column n: State data for epigenome n-3
```
</details>

<a name="output-directory-pairwise"></a>
<details><summary><b> Output Directory [-o, --output-directory]</b></summary>
<p></p>
<p>The output of paired group Epilogos will vary depending on the number of input files present in the input directories <a href="#directories-pairwise">[-a, --directory-one]</a> or <a href="#directories-pairwise">[-b, --directory-two]</a>. All score difference files will be gzipped txt files and of the format <code>pairwiseDelta_*.txt.gz</code> where 'pairwiseDelta_' is followed by the names of input directory one, input directory two, the saliency metric, and the name of the corresponding input file (extensions removed). All other outputs follow this same name suffix format, with the exception that the corresponding input file is omitted in the case that the relevant file is a summary accross all input files.</p>

<p>The output directory will contain one <code>pairwiseMetrics_*.txt.gz</code> file. Columns 1-3 contain the locations, column 4 contains the state with the largest difference between the scores, column 5 contains the squared euclidean distance between the scores, and column 6 contains the p-value of this distance.</p>

<p>The output directory will contain one <code>significantLoci_*.txt</code> file. This file contains the all significant loci. Columns 1-3 contain the locations, column 4 contains name of the largest difference states, column 5 contains the squared euclidean distance between the scores, column 6 contains the direction of this distance (determined by whether group 1 or 2 had higher signal), column 7 contains the p-value of the distance, and column 8 contains a number of stars indicating the significance of this p-value adjusted for multiple hypothesis testing (3 stars if they are significant at .01, 2 stars at .05, and 1 star at .1).</p>

<p>The output directory will contain one <code>greatestHits_*.txt</code> file. This file contains the all significant loci with adjacent regions merged. If there are less than 1000 significant loci, it takes the top 1000 highest distance regions and merges those. Columns 1-3 contain the locations, column 4 contains name of the largest difference states, column 5 contains the squared euclidean distance between the scores, column 6 contains the direction of this distance (determined by whether group 1 or 2 had higher signal), column 7 contains the p-value of the distance, and column 8 contains a number of stars indicating the significance of this p-value adjusted for multiple hypothesis testing (3 stars if they are significant at .01, 2 stars at .05, 1 star at .1, and a period if not significant).</p>

<p>The output directory will contain one <code>manhattanPlots_*</code> directory. This directory will contain all the manhattan plots generated by pairwise epilogos. These plots show the signed squared euclidean distances between groups 1 and 2 as well as the p-values of these distances. There is one genome-wide plot generated and another plot generate for each chromosome.</p>

<p>Depending on the <a href="#diagnostic-figures">[-d, --diagnostic-figures]</a> flag the output directory may contain one <code>diagnosticFigures_*</code> directory. This directory will contain figures showing the quality of the fit the null data and comparisons between the null and real data.</p>

<p>The argument to this flag is the path to the directory to which you would like to output. Note that this <strong>CANNOT</strong> be the same as the input directory.</p>
</details>

<a name="diagnostic-figures"></a>
<details><summary><b> Diagnostic Figures [-d, --diagnostic-figures]</b></summary>
<p></p>
<p>If this flag is enabled, Pairwise Epilogos will output diagnostic figures of the gennorm fit on the null data and comparisons between the null and real data. These can be found in a sub-directory of the output directory named <code>diagnosticFigures_*</code> directory where 'diagnosticFigures_' is followed by the names of input directory one, input directory two, and the saliency metric.</p>
</details>

<a name="num-trials"></a>
<details><summary><b> Number of Trials [-t, --num-trials]</b></summary>
<p></p>
<p>In order to save time when fitting in paired group Epilogos, samples of the null data are fit rather than the whole null data and then the median fit is used.</p>

<p>The argument to this flag is the number of times these samples are fit. Epilogos defaults to 101</P>
</details>

<a name="sampling-size"></a>
<details><summary><b> Sampling Size [-z, --sampling-size]</b></summary>
<p></p>
<p>In order to save time when fitting in paired group Epilogos, samples of the null data are fit rather than the whole null data and then the median fit is used.</p>

<p>The argument to this flag is the size of the samples that are fit. Epilogos defaults to 100000</P>
</details>

<a name="visual-output"></a>

## Visual Output

Unlike single group Epilogos, pairwise Epilogos has a visual componenet in the form of manhattan plots. Found in the <code>manhattanPlots_*</code> output directory, these plots offer users a way to visually locate differences between two groups. These plots color in any points deemed to be significant above a threshold of 0.1 according to the colors specifed in the [state info tsv](#state-info) provided by the user. Additionally, the points have varying opacity determined by the ratio between their distance and the largest distance. 

In the example plot below, we have a genome-wide manhattan plot generated by a pairwise Epilogos run of male donors vs female donors in the [BOIX dataset](https://docs.google.com/spreadsheets/d/103XbiwChp9sJhUXDJr9ztYEPL00_MqvJgYPG-KZ7WME/edit#gid=1813267486). It immediately becomes clear that the vast majority of differences between male and female genomes is in the X chromosome.

<h1 align="center">
  <img src="./data/manhattan_male_female_genome.pdf" width="840">
</h1>

Seeing that these differences are primarily present in chromosome X, we now look at another manhattan plot generated by the same Epilogos run which only contains chromosome X. With newfound granularity, we can now begin to identify individual genes where the differences are most pronouced. We can see XIST clearly at 73 Mbp and FIRRE 131 Mbp. Furthermore, because the points are on the female side of the plot, we know that these differences were driven by higher Epilogos scores in the female genome for these regions. This corroborates our knowledge that these genes are primarily active in females and inactive in males.

<h1 align="center">
  <img src="./data/manhattan_male_female_chrX.pdf" width="840">
</h1>
