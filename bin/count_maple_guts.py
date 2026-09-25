#!/usr/bin/env python3
# Tami Leppert
# 8/16/2025
# v 1.0
#
# program count_maple_guts.py reads in input file
# program count_maple_guts.py is called from master_vm.script
# fin contains three columns
# 1st column is either '-' or 'n'
# second column is position
# third column is number of consecutive positions
# A new chromosomes is indicated by a 1 in the second column, C. auris has 7 chromosomes, flag if not 7 found
#
# and tabulates the number of 'n','A','C','G','T' or '*' for each chromosome
# if the third column has no number then count for the base (first column) one count, increment the tally
# if the third column is a number, the count for the base (first column) is the number, sum this to the tally
#
# Print the filename and then n=X A=X C=X G=X T=X *=X
#

import os
from pathlib import Path
import subprocess
import glob
import sys

# open input and output files
current_directory = Path.cwd()                               # find current directory
maple_directory = os.path.join(current_directory,"maple")    # find maple subdirectory
maples = glob.glob(os.path.join(maple_directory,"*.maple"))  # find all of the maple files in them maple subdirectory

# will contain the tally of bases for each maple file (by chromosome) in the input file list of maple files
fout = open("tabulated_bases_from_maple.dat", 'w')

# for each line in input file, list of maple files to tally
for line in maples:

    # debug print("line: " + line.strip())
    # Open the maple file for reading
    fin = open(line.strip(), 'r') 

    #clean up tally for next maple file
    count_base = [0] * 7   # order is 'n', 'A', 'C', 'G', 'T', '*', 'something else'

    # Reset the chromosome count
    chrom = -1

    for aline in fin:  # For each line in the maple file

        # set if not at the beginning of a chromosomes
        position = 0

        # if at the header line skip to the next line (now at beginning of chromosome)
        if '>' in aline:
            aline = fin.readline()
            position = 1
            
        # split the line into columns, may be two or three columns
        columns = aline.strip().split('\t')

        # debug print("n columns: " + str(len(columns)))

        # get the integer of the second column put it into position
        # get the integer of the third column put it into number, the number of consecutive times we see this base
        match columns[0]:
            case "n":
                base_index = 0
            case "A":
                base_index = 1
            case "C":
                base_index = 2
            case "G":
                base_index = 3
            case "T":
                base_index = 4
            case "*":
                base_index = 5
            case _:
                base_index = 6  # something else occurred
                something_else = columns[0]
                
        if (position == 1):  # for the first chromosome, at the top of the file, increment chromosome # to 0
            chrom += 1


        if (position == 1) and (chrom != 0):  # position == 1 means a new chromosome, total of 7 for C auris
            fout.write(line.strip() + " chrom=" + str(chrom) + " n=" + str(count_base[0]) + " A=" + str(count_base[1]))
            fout.write(" C=" + str(count_base[2]) + " G=" + str(count_base[3]) + " T=" + str(count_base[4]))
            fout.write(" *=" + str(count_base[5]))
            if int(count_base[6]) > 0:
                fout.write(" " + str(something_else) + "=" + str(count_base[6]) + "\n")
            else:
                fout.write(" ?=" + str(count_base[6]) + "\n")

            #clean up tally for next chromosome
            count_base = [0] * 7   # order is 'n', 'A', 'C', 'G', 'T', '*', 'something else'


        # The number of times we see the base - if a third column then thats the number of consecutive times
        # Note: 'n' can have a consecutive number of times of 1
        #        bases do not have a column 3, because a substitution at that position occurs only once
        #        deletions and insertions of more than one base are not contained in these maple files.
        number = 0

        # if there's three columns
        if len(columns) == 3:
            number = int(columns[2])
        else:   # if there is no third column, or no value, then the number to increment is 1
            number = 1
            
        count_base[base_index] = int(count_base[base_index]) + number
            

    # The file has been read, print the tallies for the last chromosome (should be chrom == 7)
    if (chrom != 0):  # should be 7 for C auris - last chromosome to print before next file
        chrom += 1
        # Should be 7 chromosomes, if not.... message    
        if chrom < 7:
            fout.write(line.strip() + ' ERROR FILE DOES NOT CONTAIN 7 CHROMOSOMES, only ' + str(chrom) + '\n')
        
        fout.write(line.strip() + " chrom=" + str(chrom) + " n=" + str(count_base[0]) + " A=" + str(count_base[1]))
        fout.write(" C=" + str(count_base[2]) + " G=" + str(count_base[3]) + " T=" + str(count_base[4]))
        fout.write(" *=" + str(count_base[5]))
        if int(count_base[6]) > 0:
            fout.write(" " + str(something_else) + "=" + str(count_base[6]) + "\n")
        else:
            fout.write(" ?=" + str(count_base[6]) + "\n")                
        
    fin.close()  # close the file to tabulate

# close files            
fout.close()     # close the output file with tabulations
