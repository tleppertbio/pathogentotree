#!/usr/bin/env python3
# Tami Leppert
# 3/5/26
# v 1.0
# 6/15/26
# v 2.0 Add reading file list from folder, instead of from file
#
# Script is called from master_vm.script  Pastes the maple files together after they've been masked.
# There is a two step masking process, one with .bed file created from large repeat regions in the sequence.
# The second mask process is masking based on parsimony scores.  Masking areas with parsimony scores > 1000.
# The paste_maples.py happens after the first masking process.  It pulls the chromosomes together into a
# single file.  The list of files to pull together are in a folder ./mask_chrom, the merged files are
# put into the folder ./allchrom. The lengths of each chromosome are from the reference file
# ../reference/reference.fa.fai.
#
# program paste_maples.py reads in list of chromosome lengths and list of maple files
# copies maple file to full_maple pulling all of the chromosomes (listed in fchromin) together
# and prints them out to one file - the position of the edits being adjusted (made relative)
# by the chromosome number.
#
# output file contains all chromosome maple files for one sample pasted together with new relative positions.
#

import os
from pathlib import Path
import subprocess
import glob
import sys

# open input and output files
#flistin = open("maple_file_wn.list", 'r')
#flistin = open("maple_file.list", 'r')
current_directory = Path.cwd()
parent_directory= Path.cwd().parent
# reference.fa.fai contains the lengths of all of the chromosomes, used for aligning merged chromosomes.
reference_directory=parent_directory / 'reference' / 'reference.fa.fai'
maple_directory = os.path.join(current_directory,"mask_chrom")
flistin = glob.glob(os.path.join(maple_directory,"*.1.maple"))
#fchromin = open("{parent_directory}/reference/reference.fa.fai", 'r')
fchromin = open(reference_directory, 'r')
#
#
chromosome=0
chromlen=[]
for line in fchromin:
    # split the line into columns, 4 columns
    chromosome += 1
    columns = line.strip().split('\t')
    chromlen.append(columns[1])
fchromin.close()     # close the input length file
n_chromosomes= chromosome + 1

# Find the output directory, if it exists, otherwise create it.
directory_path = os.path.join(current_directory,"allchrom")
os.makedirs(directory_path, exist_ok=True)

# For each sample in the maple file list
for sample in flistin:
    sampleroot = sample.strip().split('/')[-1].split('.')[0]
    #print("samplefile: " + str(samplefile))
    full_out_samplefile  = directory_path + "/" + sampleroot + ".all.maple"
    fsampleout = open(full_out_samplefile,'w')
        
    offset = 0  # offset for the current chromosome
    next_offset = 0  # offset for the next chromosome
    
    for chromosome in range(1,n_chromosomes):

        offset = next_offset + offset
        next_offset = int(chromlen[chromosome-1])
        full_samplefile_name  = maple_directory + "/" + sampleroot + "." + str(chromosome) + ".maple"
        #print("full_samplefile: " + full_samplefile_name)
        fsamplein = open(full_samplefile_name,'r')

        # Read the sample file
        for mapleline in fsamplein:
            if (">" in mapleline):
                if (chromosome == 1):  # For the first chromosome, print the header
                    fsampleout.write(mapleline)
            else:
                if (chromosome == 1):  # For the first chromosome, don't adjust the position
                    fsampleout.write(mapleline)
                else:
                    # Save contents of line into mapleedit and mapleposition
                    maplearray = mapleline.split('\t')
                    #print("maple line: " + str(maplearray))
                    mapleedit = maplearray[0]            
                    mapleposition = int(maplearray[1]) + offset
                    #print("maple edit: " + str(mapleedit) + "\t" + str(mapleposition))

                    # if mapleedit is an 'n' then determine maplenlen length of n string, not used currently
                    if (mapleedit == 'n'):
                        maplenlen = maplearray[2]
                        fsampleout.write(mapleedit + "\t" + str(mapleposition) + "\t" + maplenlen)
                    else:
                        fsampleout.write(mapleedit + "\t" + str(mapleposition) + "\n")
                #end if (chromosome == 1):  # For the first chromosome, don't adjust the position
            #end if (">" in maplearray):                        
        #end for mapleline in fsamplein:

        # close the input sample file for this chromosome
        fsamplein.close()
        
    #end for chromosome in range(1,n_chromosomes):

    # close the output sample file
    fsampleout.close()

#end for sample in flistin:    
