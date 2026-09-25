#!/usr/bin/env python3
# Tami Leppert
# 4/16/26
# v 1.0
#
# Program parse_entrez.py is called from sra-setup.script
# It looks at these 3(8) files 
#./metadata/Entrez.csv  How many new samples (should possibly use sra-now.list)
#./metadata/Not_run.info  Write how many of these new samples have not been previously run (if previous run)
#./metadata/Not_qualified.info  Write the new samples that are not WGS, PAIRED, 498019 and 'Candidozyma auris'
# If a previous directory exists
#../previous_directory/current_chrom_nhin.list how many samples were run last time
#../previous_directory/previous_chrom_nhin.list how many samples were run (the time previous to) last time
#../previous_directory/disqualified_n.list how many samples were disqualified last time
#../previous_directory/previous_disqualified.list how many samples were disqualified (the time before) last time
#../previous_directory/do_not_run.list how many samples have been put by previous users into the do not run list
#
# Determines if the sample as already been processed.
# Determines if the sample qualifies for processing.
#

import os
import csv
import argparse
from pathlib import Path

def process_arguments_mask():

    #  Checks to see that at least two arguments are entered on the command line
    #
    #  Arguments:
    #      1) directory name of the current folder - manditory
    #      2) directory name of the previous folder - optional
    #      3) -n means there is no previous folder - optional
    #
    #  No return unless a valid argument has been entered.
    #
    parser = argparse.ArgumentParser(description='''A script that takes a two command-line argument.
     Reads:
      a current processing directory -c, in the format YYYY-MM_C.auris - manditory
      a previous processing directory -p, in the format YYYY-MM_C.auris - optional
      a flag if no processing directory -n                              - optional
     Returns:
      a list of samples to process.'''
    ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c','--current_directory',help='The name of the current run directory.',required=True)    
    parser.add_argument('-p','--previous_directory',help='The name of the previous run directory.')
    parser.add_argument('-n','--no_previous_directory',action='store_true',help='There is no previous run directory.')    
    parser.add_argument('-v','--verbose',action='store_true',help='Enable verbose output')
    args = parser.parse_args()

    global current_directory        # The first argument
    global current_directory_text   # The text of the current directory    
    global previous_directory       # The second argument
    global previous_directory_text  # The text of the previous directory
    global no_previous_directory    # The third argument
    current_directory = ""    # Initialize current_directory    
    previous_directory = ""   # Initialize previous_directory
    no_previous_directory = 0 # Initialize no_previous_directory    

    current_directory = args.current_directory
    current_directory_text = current_directory
    previous_directory = args.previous_directory
    previous_directory_text = previous_directory
    #no_previous_directory stores true if present
    no_previous_directory = args.no_previous_directory    
    
#            
#END of def process_arguments_mask():
#

process_arguments_mask()

# open input and output files

try:   # open file for reading Entrez csv
    entrez_file = current_directory_text + "/metadata/Entrez.csv"
    flistin = open(entrez_file, 'r')    
except FileNotFoundError as e:  # for input Entrez.csv file
    print(f"Error: The file was not found - {e}")
    sys.exit(1)
except IOError as e:
    print(f"Error reading the file - {e}")
    sys.exit(1)    
    
not_run_file = current_directory_text + "/metadata/Not_run.info"
flistout = open(not_run_file, 'w')
not_qual_file = current_directory_text + "/metadata/Not_qualified.info"
fdnqout = open(not_qual_file, 'w')

# Find the output directory, if it exists, otherwise create it.
prev_current = 0
prev_previous = 0
prev_curr_disqualify = 0
prev_prev_disqualify = 0
prev_do_not_run = 0
print("Previous directory ", previous_directory_text)
if previous_directory_text:
    if Path(previous_directory_text).is_dir():
        prev_dir_current = previous_directory_text + "/current_chrom_nhin.list"
        print("Previous directory current ", prev_dir_current)        
        if Path(prev_dir_current).is_file():
            fprevcurrentin = open(prev_dir_current, 'r')
            prev_current = 1
        prev_dir_previous = previous_directory_text + "/previous_chrom_nhin.list"
        print("Previous directory previous ", prev_dir_previous)        
        if Path(prev_dir_previous).is_file():        
            fprevprevin = open(prev_dir_previous, 'r')            
            prev_previous = 1
        prev_dir_current_disqualify = previous_directory_text + "/disqualified_n.list"
        print("Previous directory disqualify ", prev_dir_current_disqualify)                
        if Path(prev_dir_current_disqualify).is_file():        
            fprevcurrdisqualin = open(prev_dir_current_disqualify, 'r')            
            prev_curr_disqualify = 1
        prev_dir_prev_disqualify = previous_directory_text + "/previous_disqualified.list"
        print("Previous directory disqualify ", prev_dir_prev_disqualify)                
        if Path(prev_dir_prev_disqualify).is_file():        
            fprevprevdisqualin = open(prev_dir_prev_disqualify, 'r')            
            prev_prev_disqualify = 1
        prev_dir_do_not_run = previous_directory_text + "/do_not_run.list"
        print("Previous directory do_not_run.list ", prev_dir_do_not_run)                
        if Path(prev_dir_do_not_run).is_file():        
            fprevdonotrunin = open(prev_dir_do_not_run, 'r')            
            prev_do_not_run = 1

#1,5,13,16,28,29 columns from Entrez.csv
flistout.write('Run,bases,LibraryStrategy,LibraryLayout,TaxID,ScientificName\n')
#fdnqout.write('Run,bases,LibraryStrategy,LibraryLayout,TaxID,ScientificName\n')

# For each sample in the maple file list
csv_reader = csv.reader(flistin)
# Read past header
header = next(csv_reader)
library_strategy = 0
library_layout = 0
tax_id = 0
scientific_name = 0
bases = 0
run = 0                        
for i in range(len(header)): 
    if header[i] == "LibraryStrategy":
        library_strategy = i
    if header[i] == "LibraryLayout":
        library_layout = i
    if header[i] == "TaxID":
        tax_id = i
    if header[i] == "ScientificName":
        scientific_name = i                
    if header[i] == "bases":
        bases = i
    if header[i] == "Run":
        run = i                        
        
for sample in csv_reader:

    filelookfordot = sample[0] + "."
    filelookfornewline = sample[0] + "\n"
        
    # look for previously processed sample
    file_found = 0
    if prev_current:
        if filelookfordot in fprevcurrentin.read():
            file_found = 1
        fprevcurrentin.seek(0)
    if prev_previous:
        if filelookfordot in fprevprevin.read():
            file_found = 1
        fprevprevin.seek(0)                
    if prev_curr_disqualify:
        if filelookfordot in fprevcurrdisqualin.read():
            file_found = 1
        fprevcurrdisqualin.seek(0)                                
    if prev_prev_disqualify:
        if filelookfornewline in fprevprevdisqualin.read():
            file_found = 1
        fprevprevdisqualin.seek(0)                                
    if prev_do_not_run:
        if filelookfornewline in fprevdonotrunin.read():
            file_found = 1
        fprevdonotrunin.seek(0)                                

    # if sample was not previously processed
    if not file_found:
            
        # if WGS, PAIRED, 498019 and 'Candidozyma auris'
        if str(sample[library_strategy]) == "WGS" and str(sample[library_layout]) == "PAIRED" and str(sample[tax_id]) == "498019" and str(sample[scientific_name]) == "Candidozyma auris":

            #1,5,13,16,28,29 columns from Entrez.csv
            flistout.write(str(sample[run]) + "," + str(sample[bases]) + "," + str(sample[library_strategy]) + "," + str(sample[library_layout]) + "," + str(sample[tax_id]) + "," + str(sample[scientific_name]) + "\n")

            #end if str(samplename[12]) == "WGS" and str(samplename[15]) == "PAIRED" and str(samplename[27]) == "498019" and str(samplename[28]) == "Candidozyma auris":
        else:
            #fdnqout.write(str(samplename[0]) + "," + str(samplename[4]) + "," + str(samplename[12]) + "," + str(samplename[15]) + "," + str(samplename[27]) + "," + str(samplename[28]) + "\n")
            fdnqout.write(str(sample[run]) + "\n")                
    #end if not file_found

#end for sample in flistin:    

# close files            
flistin.close()
flistout.close()
fdnqout.close()
fprevdonotrunin.close()
fprevprevdisqualin.close()
fprevcurrdisqualin.close()
fprevprevin.close()
fprevcurrentin.close()
