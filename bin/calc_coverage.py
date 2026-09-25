#!/usr/bin/env python3
# Tami Leppert
# 8/25/2025
# v 1.0
#
# Program calc_coverage.py reads in the input file.
# Program calc_coverage.py is called from master_vm.script
# fin contains 9 columns
# 1st column is the name of the maple file
# second column is the chromosome
# third column is number of n bases in the maple file for that chromosome
# fourth column is the number of A bases in the maple file for that chromosome
# fifth column is the number of C bases in the maple file for that chromosome
# sixth column is the number of G bases in the maple file for that chromosome
# seventh column is the number of T bases in the maple file for that chromosome
# eighth column is the number of * bases in the maple file for that chromosome 
# ninth column is the number of ? bases in the maple file for that chromosome
#
# and tabulates the number of 'n'/total bases for that chrom AND 'A','C','G','T' or '*'/total bases for each chromosome
#
# Print the filename and chrom and then n/total A+C+G+T+*/total
#
# chrom length in bases
# read in from ../reference/reference.fa.fai
#
from pathlib import Path
parent_dir = Path.cwd().parent
reference_file = parent_dir / 'reference' / 'reference.fa.fai'
flenin = open(reference_file, 'r')
chromosome=0
chromlen = []
for line in flenin:
    # split the line into columns, 4 columns
    chromosome += 1
    columns = line.strip().split('\t')    
    chromlen.append(columns[1])
flenin.close()     # close the input length file
n_chromosomes = chromosome

# open input and output files
flistin = open("tabulated_bases_from_maple.dat", 'r')
# will contain the tally of bases for each maple file (by chromosome) in the input file list of maple files
fout = open("calculated_ratios.dat", 'w')

# for each line in input file, list of maple files to tally
for line in flistin:

    for i in range(1,n_chromosomes):
        # split the line into columns, 9 columns
        columns = line.strip().split(' ')

        # get the integer of the second column put it into position
        # get the integer of the third column put it into number, the number of consecutive times we see this base

        nbase = columns[2].strip().split('=')
        baseA = columns[3].strip().split('=')
        baseC = columns[4].strip().split('=')
        baseG = columns[5].strip().split('=')
        baseT = columns[6].strip().split('=')
        basestar = columns[7].strip().split('=')
    
        count_base = int(baseA[1]) + int(baseG[1]) + int(baseC[1]) + int(baseT[1]) + int(basestar[1])
        count_n = int(nbase[1])

        ratio = int(count_n)/int(chromlen[i])
        formatted_ratio = f"{ratio:.2f}"
        fout.write(columns[0] + " " + columns[1] + " nfract=" + formatted_ratio)
        baseratio = int(count_base)/int(chromlen[i])
        formatted_baseratio = f"{baseratio:.2f}"
        fout.write(" basefract=" + formatted_baseratio + "\n")
        # REPEAT FOR EVERY CHROM
        if i < n_chromosomes:
            line = flistin.readline()
                
# close files            
fout.close()     # close the output file with tabulations
flistin.close()  # close the file with list of files to tabulate
