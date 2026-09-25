#!/usr/bin/env python3
# Program gvcf_to_maple_haploid.py
# Tami Leppert
# 9/2/2025
# v 1.0
#

import sys
import os
import gzip
import argparse

def read_vcf(vcf_file_path):

    #  Reads a VCF.gzipd file and returns its content as a list of lines, 
    #  skipping comment lines.
    #
    #  Arguments:
    #      vcf_file_path (str): Path to the VCF file (gzipped).
    #
    #  Returns:
    #     list: A list of strings, where each string is a line from the VCF file.


    # lines to return
    lines = []
    global maple_fileout
    global maple_root
    # Initialize the output maplefile name
    maple_fileout="initialize"
    
    # read gzip *.g.vcf.gz file
    try:
        # open the gzip file in text mode for automatic decompression
        with gzip.open(vcf_file_path, 'rt') as file:

            # replace string "g.vcf.gz" with "maple" for output file
            maple_fileout = vcf_file_text.replace("g.vcf.gz","maple")
            maple_root = vcf_file_text.replace(".g.vcf.gz","")            

            for line in file:                       # Read each line
                if not line.startswith('#'):        # If the line does not begin with a comment '#'
                    lines.append(line.strip())      # Save the lines in the array lines.
                    
    except FileNotFoundError:
         print(f"Error: The file '{vcf_file_path}' was not found.")
         
    except gzip.BadGzipFile:
        try:
            # for non gzip file
            with open(vcf_file_path, 'r') as file:

                # replace string "g.vcf" with "maple" for output file                
                maple_fileout = vcf_file_text.replace("g.vcf","maple")
                if ".g.vcf.gz" in vcf_file_text:
                    maple_root = vcf_file_text.replace(".g.vcf.gz","")                            
                elif ".g.vcf" in vcf_file_text:
                    maple_root = vcf_file_text.replace(".g.vcf","")                            

                for line in file:
                    if not line.startswith('#'):
                        lines.append(line.strip())
                        
        except Exception as e:
             print(f"Error reading file non-gzip: {e}")
             return None
         
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return lines

#            
#END of def read_vcf(vcf_file_path):
#


def process_arguments_vcf():

    #  Checks to see that 4 arguments are entered on the command line
    #
    #  Arguments:
    #      1) vcf_file_path (str): Path to the VCF file (gzipped).
    #      2) DP_min_val as a command line argument
    #      3) GQ_min_val as a command line argument
    #      4) "AND" or "OR" as a command line argument to select choice A or choice B
    #
    #  No return unless 4 valid arguments have been entered.
    #
    parser = argparse.ArgumentParser(description='''A script that takes four command-line arguments.
     Reads:
      a .g.vcf.gz or .g.vcf file, a minimum read depth value, a minimum genotype quality value, an operation text
     Returns:
      a maple format file - processed with the following filters, reference or alternate alleles printed if;
        the DP (read depth of the segment) is >= DP_min_val
        the GQ (genome quality confidence value) is >= GQ_min_val
        -e OR used as  (DP >= DP_min_val) OR (GQ >= GQ_min_val)
        -e AND used as (DP >= DP_min_val) AND (GQ >= GQ_min_val)'''
    ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i','--input_file',help='The name of the input g.vcf.gz file.',required=True)
    parser.add_argument('-DP','--DP_MIN', help='The value (integer) of the minimum read depth; recommend using 20.',type=int,default=20)
    parser.add_argument('-GQ','--GQ_MIN', help='The value (integer) of the minimum genotype quality; recommend using 99.',type=int,default=99)
    parser.add_argument('-o','--operation', help='The text AND or the text OR. Usage example: min_read_depth AND min_conf ; recommend using AND.',choices=['AND','OR'],default='AND')
    parser.add_argument('-v','--verbose',action='store_true',help='Enable verbose output')
    args = parser.parse_args()

    global vcf_filename    # The first argument
    global DP_min_val      # The second argument
    global DP_min_val_int  # The second argument cast to integer
    global GQ_min_val      # The third argument
    global GQ_min_val_int  # The third argument cast to integer
    global choice          # The fourth argument
    global vcf_file_text   # The text of filename
    vcf_filename = ""      # Initialize filename
    
    vcf_filename = args.input_file
    DP_min_val = args.DP_MIN
    GQ_min_val = args.GQ_MIN
    choice = args.operation
    vcf_file_text = vcf_filename
    DP_min_val_int = int(DP_min_val)
    GQ_min_val_int = int(GQ_min_val)        
        
#            
#END of def process_arguments_vcf():
#



########################################
########################################
# Main
########################################

# Read a VCF.gzipd file, processes its contents and outputs a maple file
#
# Arguments:
#      inputfile.g.vcf.gz as a command line argument
#      DP_min_val as a command line argument
#      GQ_min_val as a command line argument
#      "AND" or "OR" as a command line argument to select choice A or choice B
#
# Returns:
#      a maple file - processed with the following filters;
#         if the DP (read depth of the segment) is >= DP_min_val
#         if the GQ (genome quality confidence value) is >= GQ_min_val
#         choice A) (DP >= DP_min_val) OR (GQ >= GQ_min_val)
#         choice B) (DP >= DP_min_val) AND (GQ >= GQ_min_val)
#
#         recommended values DP_min_val = 20, GQ_min_val = 99, choice B (AND)
#
#
# Each line consists of 10 columns:
# 1      2        3   4        5        6             7               8               9                10
# CHROM  POS      ID  REF      ALT      QUAL          FILTER          INFO            FORMAT           SRR25455197
# string position '.' ref_base alt_base quality_score filter_value(.) info(key+value) format(key only) sample_data
#
# ALL possibilities for column 4 and 5
# T <NON_REF>              # Reference and no alternate        
# T A,<NON_REF>            # Reference and alternate
# A AAGGCT,<NON_REF>       # insertion of AGGCT
# TAAAACTATGC T,<NON_REF>  # deletion of AAAACTATGC
# A *,T,<NON_REF>          # ‘*’ indicates that the allele is missing due to a upstream deletion, can pass DP and GQ tests
# N <NON_REF>              # Reference and no alternate - usually does not pass DP and GQ tests
#
# ALL possibilities for column 8
# see.. https://gatk.broadinstitute.org/hc/en-us/articles/360035531692-VCF-Variant-Call-Format
# DP:integer:="Approximate read depth (reads with MQ=255 or with bad mates are filtered)"
# MLEAC:integer,:A:="Maximum likelihood expectation (MLE) for the allele counts (not necessarily the same as the AC), for each ALT allele, in the same order as listed"
# MLEAF:float,:A:x.xx:="Maximum likelihood expectation (MLE) for the allele frequency (not necessarily the same as the AF), for each ALT allele, in the same order as listed"
# MQRankSum="Z-score:float:x.xxx: From Wilcoxon rank sum test of Alt vs. Ref read mapping qualities"
# RAW_MQandDP:integer:2:xxxxxx,xxx:="Raw data (sum of squared MQ and total depth) for improved RMS Mapping Quality calculation. Incompatible with deprecated RAW_MQ formulation."
# ReadPosRankSum:float:(-)x.xxx:="Z-score from Wilcoxon rank sum test of Alt vs. Ref read position bias"
# BaseQRankSum:float:(-_x.xxx:="Z-score from Wilcoxon rank sum test of Alt Vs. Ref base qualities"
#                              This score only shows when the reference has a read depth > 0
# END:integer:="Stop position of the interval" (always by itself)
#
# ALL possibilities for column 10 (label/format is found in column 9)
# see.. https://gatk.broadinstitute.org/hc/en-us/articles/360035531692-VCF-Variant-Call-Format        
# GT:integer:0,1,.,x="Genotype" (. = n) (0 = reference) (x = which non reference base/sequence)
 ##The genotype of this sample at this site. For a diploid organism, the GT field indicates the two alleles
 ##carried by the sample, encoded by a 0 for the REF allele, 1 for the first ALT allele, 2 for the second ALT
 ##allele, etc. When there is a single ALT allele (by far the more common case), GT will be either:
 ##Tami- in spite of c. auris not being diploid, I believe the 0= reference allele was used.
# DP:integer:"Approximate read depth; some reads may have been filtered"
# GQ:integer:"Genotype Quality"
# MIN_DP:integer:"Minimum DP observed within the GVCF block"
# PL:integer:"Normalized, Phred-scaled likelihoods for genotypes as defined in the VCF specification"
# MIN_PL:integer:"Minimum PL observed within the GVCF block"
# AD:integer:Allelic depths for the ref and alt alleles in the order listed"
# SB:integer:"Per-sample component statistics which comprise the Fisher's Exact Test to detect strand bias."
#
# EXAMPLE:
# 0             1  2  3     4                       5    6      7      8                9
# CHROM       POS ID REF   ALT                     QUAL FILTER INFO    FORMAT           SRR25455197
#CP043531.1      1 .  A   <NON_REF>                   .   .     END=372 GT:DP:GQ:MIN_DP:PL 0:0:0:0:0,0
#CP043531.1    373 .  C   <NON_REF>                   .   .     END=487 GT:DP:GQ:MIN_DP:PL 0:97:99:54:0,1730
#CP043531.1    488 .  T   C,<NON_REF>             4572.04 .     DP=102;MLEAC=1,0;MLEAF=1.00,0.00;RAW_MQandDP=367200,102 GT:AD:DP:GQ:PL:SB 1:0,102,0:102:99:4582,0,4582:0,0,67,35
#CP043531.1    524 . TC   T,<NON_REF>             5345.01 .     DP=119;MLEAC=1,0;MLEAF=1.00,0.00;RAW_MQandDP=428400,119 GT:AD:DP:GQ:PL:SB 1:0,119,0:119:99:5355,0,5355:0,0,82,37    ##deletion event
#CP043531.1    544 .  A   C,AGCAC,AGCCC,<NON_REF> 5056.04 .     DP=113;MLEAC=1,0,0,0;MLEAF=1.00,0.00,0.00,0.00;RAW_MQandDP=406800,113 GT:AD:DP:GQ:PL:SB 1:0,109,1,0,0:110:99:5066,0,4891,4794,4910:0,0,73,37
#CP043531.1   1202 .  G   T,<NON_REF>             4209.04 .     BaseQRankSum=2.013;DP=139;MLEAC=1,0;MLEAF=1.00,0.00;MQRankSum=0.000;RAW_MQandDP=500400,139;ReadPosRankSum=-1.304 GT:AD:DP:GQ:PL:SB 1:2,135,0:137:99:4219,0,4238:0,2,71,64
#CP043531.1  25273 .  T   TAC,TCCC,TCCCC,TACCCC,TCCCCC,<NON_REF>  4047.01 . DP=97;MLEAC=0,0,1,0,0,0;MLEAF=0.00,0.00,1.00,0.00,0.00,0.00;RAW_MQandDP=349200,97 GT:AD:DP:GQ:PL:SB 3:0,0,0,90,0,0,0:90:99:4057,4139,3457,0,3597,3998,4025:0,0,38,52 ## insertion event
#CP043531.1 901271 .  A   AT,<NON_REF>                0   .     MLEAC=0,0;MLEAF=NaN,NaN GT:GQ:PL  .:0:0,0,0 ## no criteria available- ignore
#CP043531.1   6213 .  T   C,<NON_REF>	             0.01 .	MLEAC=0,0;MLEAF=NaN,NaN	GT:PL	.:0,0,0     ## no criteria available- ignore
#
#


# Check the command line arguments
process_arguments_vcf()


# Read the contents of the gvcf file into vcf_data - an array of strings
if vcf_filename != "":
    vcf_data = read_vcf(vcf_filename)
else:
    sys.exit(1)

# Initialize g.vcf.gz chromosome string
chromosome="initialize"
chromosome_number = 0

# If input file was read into vcf_data
if vcf_data:

    # Check the output maplefile name
    if ".maple" in maple_fileout:
        try:
            # open maplefile for writing
            with open(maple_fileout, 'w') as outfile:

                # process lines in input file
                for line in vcf_data:

                    # split line into array aline by tab separator
                    aline = line.split('\t')
                    
                    # only used in if statements if GT == '.', otherwise used as a catch for omitting a line.
                    no_call = 0                        

                    # Check to see if this is a new chromosome; using filename as chromosome number:
                    if aline[0] != chromosome:
                        chromosome_number += 1
                        chromosome_text = maple_root + "_" + str(chromosome_number)
                        chromosome = aline[0]                       #save the g.vcf.gz new chromosome string
                        output_string=f">{chromosome_text}\n"       #make header for maple file data for next chromosome

                        outfile.write(output_string)   #print the header to the maple file

                    # Check to see if the reference allele more than one base, if more than one base then skip output
                    # This indicates a deletion - note there could possibly be an exception which is not addressed here.
                    # If the reference allele is n bases long and the best alternate allele is the same length, then this 
                    # would not be an insertion event, but the maple cannot have a multi base string (? is this true?)
                    if len(aline[3]) > 1:
                        no_call = 1

                    # Check to see if this is a reference segment.  Note col 8 always starts with 'GT:'
                    # When col 4 is only "<NON_REF>" aline[9] always starts with 0: aline[8] is always 'GT:DP:GQ'
                    # When col 4 is only "<NON_REF>" there are no multiple choice alternate alleles
                    # Check the DP and GQ pass the user criteria        
                    elif (aline[4] == "<NON_REF>") and (aline[8].startswith("GT:DP:GQ")) and (aline[9].startswith("0:")):
                        missing_call = 0
                        # split aline[9] by ':' into values for 'GT:DP:GQ:'
                        stats = aline[9].split(':')

                        # check if critera is not met for validated reference sequence
                        if (choice == 'AND'):
                            if (int(stats[1]) < DP_min_val_int) or (int(stats[2]) < GQ_min_val_int):
                                missing_call = 1
                        elif (choice == 'OR'):
                            if ((int(stats[1]) < DP_min_val_int) and (int(stats[2]) < GQ_min_val_int)):
                                missing_call = 1

                        # if critera is not met for validated reference sequence, print sequence as 'missing' or 'n'
                        if missing_call:
                            end_of_sequence = aline[7].split('=')

                            output_string = f"n\t{aline[1]}\t{str(int(end_of_sequence[1])-int(aline[1])+1)}\n"
                            outfile.write(output_string)

                
                    # Check to see if this is a alternate segment.  Note col 8 always starts with 'GT:'
                    # When col 4 has more than one option (has ',') as in ",<NON_REF>" aline[8] is always 'GT:AD:DP:GQ'
                    # When col 4 ",<NON_REF>" there can be multiple alternate alleles, the best alternate is the value of GT
                    # Check the value of GT, ##DISCARD THIS -> check the AD is > DP_min_val, use DP instead of individual AD
                    # Check the DP and GQ pass the user criteria
                    # Check the alternate allele is only one base (no inserts allowed!)
                    elif (",<NON_REF>" in aline[4]) and (aline[8].startswith("GT:AD:DP:GQ")):
                        missing_call = 0
                        # split aline[9] by ':' into values for 'GT:DP:GQ:'
                        stats = aline[9].split(':')

                        if stats[0] == '.':
                            allele = 0                       # index for '.' set to reference, avoid invalid indexing
                            no_call = 1                      # avoid checking stats, no DP or GQ for '.'
                        else:
                            allele = int(stats[0])           # index of GT 
                        AD_values = stats[1].split(',')      # split the stats for the AD values
                        allele_AD = int(AD_values[allele])   # find the AD for the GT - will not use

                        # We use the DP value rather than the individual AD
                        # check if critera is not met for validated alternate sequence
                        # if the genotype index is '.', there are not complete stats, make missing_call = 1
                        if (choice == 'AND') and (no_call == 0):
                            if (int(stats[2]) < DP_min_val_int) or (int(stats[3]) < GQ_min_val_int):
                                missing_call = 1
                        elif (choice == 'OR') and (no_call == 0):
                            if ((int(stats[2]) < DP_min_val_int) and (int(stats[3]) < GQ_min_val_int)):
                                missing_call = 1

                        # check if alternate allele more than one base
                        # regardless of DP or GQ values - both an insertion and criteria not met are flagged as 'n'
                        alleles = aline[4].split(',')      # split the alternate alleles by separator ','
                        if (allele < 1):                   # if the best allele is the reference stops further elif eval
                            if (len(aline[3]) == 1) and missing_call:    # if ref allele is one base, and fails criteria
                                output_string = f"n\t{aline[1]}\t1\n"
                                outfile.write(output_string)
                                                                         # the unstated else here is do nothing if '.'
                        elif len(alleles[allele-1]) != 1:  # if allele length > 1 base, then it isn't valid, skip output
                            no_call = 1

                        elif alleles[allele-1] == '*':   # if allele is '*', then it is part of a deletion, skip output
                            no_call = 1

                        # if critera is not met for validated alternate sequence, print sequence as 'missing' or 'n' length 1
                        elif missing_call:
                            output_string = f"n\t{aline[1]}\t1\n"
                            outfile.write(output_string)

                        # else print the alternate genotype and its position
                        else:
                            output_string = f"{alleles[allele-1]}\t{aline[1]}\n"   # print the correct alternate, indexed by allele-1
                            outfile.write(output_string)
                
                    # Check to see if this is a bad call
                    # When aline[8] is 'GT:GQ:PL' - there is no read depth
                    # can't be sure if it's an indel - skip output
                    elif (aline[8].startswith("GT:GQ:PL")) or (aline[8] == "GT:PL"):
                        no_call = 1

                    # Unknown condition catch - will be skipped in output maple file
                    else:
                        print(f"*** Unexpected line type in {vcf_filename}:\n{line}", file=sys.stderr)

        except IOError as e:   ## closes try: with open(maple_fileout, 'w') as outfile:
            print(f"An error occurred, writing to output file. {e}")
            sys.exit(1)
            
    else:  # if '.maple' is not in output filename
        print(f"An error occurred, cannot use output file, input filename not .g.vcf.gz or .g.vcf and no .maple in output filename")
        sys.exit(1)
