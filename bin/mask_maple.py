#!/usr/bin/env python3
# Program mask_maple.py
# Tami Leppert
# 1/13/2026
# v 3.0
# 6/16/26
# v 4.0 added new mask test regions
#
# maple file format:
# fin contains three columns
# 1st column is either '-' or 'n' or 'A', 'G', 'C' or 'T'
# second column is position
# third column is number of consecutive positions (only if first column is 'n')
#
# bed file format:
# First three columns
# 1st column chromosome number (we will run by chromosome) - so not checked
# 2nd column start position
# 3rd column end position
#
# Any edits found in the maple files between any of the start to end positions
# are not printed in the output maple file.
# Any n regions found in the maple files overlapping any start or end positions,
# any - deletion regions found in the maple files overlapping any start or end positions
# are adjusted to show only those regions outside of the masking region
#
# program make_maple.py reads two input files
# the first file is a list of maple files
# the second file is a bed file - edited for the chromosome corresponding to the directory of maple files
# and writes a new .maple file with edits to mask removed.
#
# S = start_pos of masking region
# E = end_pos of masking region
# * = location
# + = represents the length of the extension (for n base or '-' deletion regions only)
#
#while (end_pos < location)
#    S----------E    if location is after masking region - then read the next masking region
#                    *
#if (extension != 0)  
#  if (start_pos <= location) and (end_pos < location+extension) and (end_pos >= location): 
#    S----------E    'n's or '-'s after masking region
#             *++++      store S&E until E is beyond the end of +'s
#    S----------E S---E  store S&E because possibly multiple regions are involved
#             *++++++    store S&E until E is beyond the end of +'s, region between E and next S is not masked
#
#  elif (start_pos >= location+extension):
#        S----------E   'n's or '-'s prior to masking region are not masked, unless they span a previous region
# *++++                 process previous S&E's
#
#  elif (start_pos > location) and (start_pos < location+extension) and (end_pos > location+extension): 
#    S----------E    'n's or '-'s prior to masking region are not masked, unless they span a previous region
# *++++                 process previous S&E's
#
#  elif (start_pos > location) and (start_pos < location+extension) and (end_pos < location+extension): 
#    S----------E    'n's or '-'s prior to and after masking region are not masked, unless they span another region
#  *+++++++++++++++     store S&E until E is beyond the end of +'s
#    S--E  S--E  S---E  possible masked regions between
#  *++++++++++++++++   
#    S----------E   S---E  'n's or '-'s prior to and after masking region are not masked 
#  *+++++++++++++++     store S&E until E is beyond the end of +'s, region between E and next S is not masked
#
#  else implied default 
#    S----------E    Do not print, mask this position
#        *++++
#
# if (extension == 0)
#    S----------E    Do not print, mask this position
#        *
#  if (end_pos < location)
#    S----------E    Save S&E, read next region (this condition should have been skipped at the beginning)
#                    * 
#  elif (start_pos > location) 
#    S----------E    Do not mask this position, process previous S&Es
#  *
#  else impled default
#    S----------E    Do not print, mask this position
#        *

import sys
import os
import argparse
from pathlib import Path

start_pos = []
end_pos = []
pos_index = -1

def process_arguments_mask():

    #  Checks to see that 3 arguments are entered on the command line
    #
    #  Arguments:
    #      1) maple_file_list (str): file of list of maple files to mask.
    #      2) .bed file (str): .bed file containing masking regions
    #      3) directory to use to store all processed masked .maple files
    #
    #  No return unless 3 valid arguments have been entered.
    #
    parser = argparse.ArgumentParser(description='''A script that takes three command-line arguments.
     Reads:
      a file containing a list of maple files to mask
      a file containing masking regions
      a directory to contain the masked maple files
     Returns:
      a maple format file - processed as follows, maple regions within the masking region are omitted.
        if an 'n' or '-' region spans the masking region, then only those sequences outside of the masking
        region are written to the output maple file.'''
    ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-l','--list_maple_files',help='The name of the input ile containing the maple files to mask.',required=True)
    parser.add_argument('-m','--mask_file', help='The name of the input .bed file containing the masking regions.',required=True)
    parser.add_argument('-d','--output_directory', help='The name of the output directory containing the masked maple files.',required=True)    
    parser.add_argument('-v','--verbose',action='store_true',help='Enable verbose output')
    args = parser.parse_args()

    global list_maple_files   # The first argument
    global mask_file          # The second argument
    global output_dir         # The third argument
    global list_maple_text    # The text of the list filename
    global mask_file_text     # The text of the mask file
    global output_dir_text    # The text of the output directory
    list_maple_files = ""     # Initialize list filename
    mask_file = ""            # Initialize mask filename
    output_dir = ""           # Initialize output directory

    list_maple_files = args.list_maple_files
    list_maple_text = list_maple_files
    mask_file = args.mask_file
    mask_file_text = mask_file
    output_dir = args.output_directory
    output_dir_text = output_dir
    
#            
#END of def process_arguments_mask():
#

def save_last_SE_as_current():
    #
    # Save the last S&E coordinates as the current coordinates.
    #

    global start_pos
    global end_pos
    global pos_index
    
    save_start=start_pos[pos_index]         # start_position of mask region (zero-based, half-open coordinates)
    save_end=end_pos[pos_index]             # end_position of mask region   (no need to modify the index)
    start_pos.clear()  # initialize start_position list
    end_pos.clear()    # initialize end_position list
    pos_index = -1     # initialize position_index

    start_pos.append(save_start)         # save last start position
    end_pos.append(save_end)             # save last end position
    pos_index += 1      # increment position_index (after increment is now index 0)                                
    
#    
#END of def save_last_SE_as_current():
#    
    
def process_past_regions():

    #  Process saved past mask regions - count is indicated by pos_index
    #
    #  A current string of 'n's or '-'s may span several mask regions.
    #  Masked regions are not printed,
    #  but regions between masked regions need to be printed
    #
    #           S------E     no regions masked
    #   *++++++
    #        S------E        mask regions found between S&E
    #   *++++++        
    #    S----------E S---E  mask regions found between S&E, regions between E and next S are not masked
    #             *++++++    
    #    S--E  S--E  S--E  S--E   review all saved masked regions, the last region may not be relevant
    #  *++++++++++++++++++
    #    S----------E   S---E     all masked regions in list are cleared after this routine, including the last one.
    #  *+++++++++++++++     
    #  if (start_pos > location) and (extension == 0)  
    #    S----------E             there may be only a location and no extension
    #  *
    
    global start_pos
    global end_pos
    global pos_index

    for current_index in range(0,pos_index+1):
        #start_pos[current_index]         # start_position of mask region (zero-based, half-open coordinates)
        #end_pos[current_index]           # end_position of mask region   (no need to modify the index)

        if (extension > 0):  # if the extension > 0        
#        if (extension > 0) and region and aline:  # if the extension > 0
            #1)        S---E          no masking from location (or previous E) to location+extension
            #    *+++
            #2)        S---E          no masking from location (or previous E) to S, masking from S to location+extension
            #       *+++
            #3)        S---E          no masking from location (or previous E) to S, masking from S-E
            #       *++++++++


            #1)        S---E          no masking from location (or previous E) to location+extension
            #    *+++
            if (location+extension-1 < start_pos[current_index]):
                # if there is a previous mask region
                if current_index > 0:
                    # use the last end_pos as the beginning of the unmasked region
                    # S---E       S---E          no masking from previous E to location+extension
                    #    *+++++                                        
                    if (location <= end_pos[current_index-1]):
                        if (extension+location-end_pos[current_index-1]-1) > 0:
                            fout.write('n\t' + str(end_pos[current_index-1]+1) + '\t' + str(extension+location-end_pos[current_index-1]-1) + '\n')

                #       S---E          no previous masking region, no masking from location to location+extension
                #  *+++                                            
                else:
                    fout.write('n\t' + str(location) + '\t' + str(extension) + '\n')                
            #end if (location+extension >= start_pos[current_index]):                    

            #2)        S---E          no masking from location (or previous E) to S, masking from S to location+extension
            #        *+++
            if (location+extension-1 >= start_pos[current_index]) and (location+extension-1 <= end_pos[current_index]):
                # if there is a previous mask region
                if current_index > 0:
                    # use the last end_pos as the beginning of the unmasked region
                    # S---E  S---E          no masking from previous E to S
                    #    *+++++                                        
                    if (location <= end_pos[current_index-1]):
                        if (start_pos[current_index]-end_pos[current_index-1]-1) > 0:
                            fout.write('n\t' + str(end_pos[current_index-1]+1) + '\t' + str(start_pos[current_index]-end_pos[current_index-1]-1) + '\n')

                #     S---E        no previous masking region, no masking from location to S
                #   *+++                    
                else:
                    if (start_pos[current_index]-location) > 0:
                        fout.write('n\t' + str(location) + '\t' + str(start_pos[current_index]-location) + '\n')
                    
            #end if (location+extension >= start_pos[current_index]) and (location+extension <= end_pos[current_index]):

            #3)        S---E          no masking from location (or previous E) to S, no masking from E to location+extension (or next S), masking from S-E
            #       *++++++++
            if (location < start_pos[current_index]) and (location+extension-1 > end_pos[current_index]):
                # if there is a previous mask region
                if current_index > 0:
                    # use the last end_pos as the beginning of the unmasked region
                    # S---E  S---E          no masking from previous E to S
                    #    *++++++++++                                 
                    if (location <= end_pos[current_index-1]):
                        if (start_pos[current_index]-end_pos[current_index-1]-1) > 0:
                            fout.write('n\t' + str(end_pos[current_index-1]+1) + '\t' + str(start_pos[current_index]-end_pos[current_index-1]-1) + '\n')
                #    S---E        no masking from location to S
                #  *++++++++
                else:
                    if (start_pos[current_index]-location) > 0:
                        fout.write('n\t' + str(location) + '\t' + str(start_pos[current_index]-location) + '\n')
                #end if there is a next mask region
            #end if (location <= start_pos[current_index]) and (location+extension >= end_pos[current_index]):
            
        #end if (extension > 0) and region and aline:  # if the extension > 0

        if (extension == 0) and region and aline:  # if the extension == 0
            #    S----------E    Do not mask this position, process previous S&Es
            #  *
            if (start_pos[-1] > location) and (end_pos[-1] > location):
                fout.write(aline)
    #end for current_index in range(0,pos_index+1):        

    # Save the last coordinates of start and end position as new current coordinates
    save_last_SE_as_current()
    
#
#END of def process_past_regions():
#

# Check the command line arguments
process_arguments_mask()
    
# open input files
try:  # open list of maple files
    with open(list_maple_text, 'r') as flistin:  # open list of maple files to read    

        try:  # open bed file with masking regions
            with open(mask_file_text, 'r') as fbedin:     # open bed file which contains masking regions            

                # for each line in current maple file file
                for line in flistin:
                    if not line:
                        raise ValueError("The list file " + list_maple_text.strip() + " is empty.")
                    
                    try:  # open next maple file in list of maple files
                        # debug print("line: " + line.strip())
                        path_line = Path(line.strip())
                        if not path_line.exists():
                            raise ValueError("The file " + line.strip() + " does not exist.")
                            
                        with open(line.strip(), 'r') as fin:  # Open the maple file for reading
                            dirs = line.split('/')            # split line by '/'
                            dir_len = len(dirs)               # get number of '/'s
                            if dir_len >= 1:
                                SRR_file = dirs[dir_len-1]        # get filename (last of '/') if any
                            else:
                                print(f"Error in format of contents of list of maples - {e}")
                                print(f"Can be list of files separated by newline.")
                                print(f"Can be list of files in another directory e.g. ../this.maple")
    
                            try:   # open file for writing masked maples in new directory 
                                with open(output_dir_text + "/" + SRR_file.strip(),'w') as fout:   # open file for writing masked maples in new directory
                                    

                                    # Reset the bed file after every maple file search
                                    fbedin.seek(0)
                                    start_pos.clear()  # initialize start_position list
                                    end_pos.clear()    # initialize end_position list
                                    pos_index = -1     # initialize position_index
    
                                    # for each mask region in bed file
                                    for region in fbedin:

                                        if not region:
                                            raise ValueError("The bed file " + mask_file_text + " is empty.")
                                        
                                        positions = region.strip().split('\t')  # split the line into columns
                                        if len(positions) >= 2:
                                            start_pos.append(int(positions[1])+1)         # start_position of mask region (zero-based, half-open coordinates)
                                            end_pos.append(int(positions[2]))             # end_position of mask region   (no need to modify the index)
                                            pos_index += 1      # increment position_index                                            
                                        else:
                                            print(f"Error in format of contents of mask file, no tabs? - {e}")

                                        for aline in fin:  # For each line in the maple file

                                            # if at the header line, write to output masked file and skip to the next line
                                            if '>' in aline:
                                                fout.write(aline)
                                                aline = fin.readline()

                                            if aline:
                                                columns = aline.strip().split('\t') # split the line into columns, may be two or three columns
                                            else:
                                                columns = ''
                                                location = end_pos[-1]
                                                extension = 0
                                                
                                            if len(columns) >= 2:
                                                location = int(columns[1])          # location is the sequence position of the edit
                                                if_n = columns[0]                   # if_n is type of base '-','n','A','C','G' or 'T'
                                                extension = 0                       # extension is > 0 only if base is 'n' or '-' then 'n' or '-' can span 
                                                if (if_n == 'n') or (if_n == '-'):          # more than one position '-', 'n' spans can span a masking region
                                                    extension = int(columns[2])     # we will check if the location+extension region spans any masking region
                                            elif columns:
                                                print(f"Error in format of contents of maple file, no tabs? - {e}")
                                            #end if len(columns) >= 2:                                                

                                            # if location in the maple file is > the end_position of the current region, then read next masking region
                                            #    S-------E      'n's or '-'s after masking region, read next masking region
                                            #              *++++                                                        
                                            while (location > end_pos[-1]) and region:
                                                region = fbedin.readline()

                                                if region:
                                                    start_pos.clear()  # initialize start_position list
                                                    end_pos.clear()    # initialize end_position list
                                                    pos_index = -1     # initialize position_index
                                                    
                                                    positions = region.strip().split('\t') # split the line into columns
                                                    if len(positions) >= 2:
                                                        start_pos.append(int(positions[1])+1)  # start_position of the mask region (zero-based, half-open coords)
                                                        end_pos.append(int(positions[2]))      # end_position of the mask region   (no need to modify the index)
                                                        pos_index += 1                          # increment position_index
                                                    else:
                                                        print(f"Error in format of contents of mask file, no tabs? - {e}")

                                            #end while (location > end_pos) and region:

                                            if region == '' and aline:
                                                fout.write(aline)
                                                
                                            #        S------E    'n's or '-'s before current masking region, print n's or -'s
                                            # *++++
                                            #        S------E    edits before current masking region, print edits
                                            # *
                                            elif (location+extension < start_pos[-1]):
                                                process_past_regions()
                                                
                                            # if location in the maple file is > the end_position of the current region, then read next masking region
                                            else:
                                                #    S----------E    'n's or '-'s after current masking region, read next masking region
                                                #           *+++++++
                                                while (location+extension > end_pos[-1]) and region:
                                                
                                                    if (extension > 0) and region and aline:
                                                        
                                                        #  if (start_pos <= location) and (end_pos < location+extension) and (end_pos >= location):
                                                        #    S----------E    'n's or '-'s after of masking region are not masked, store S&E
                                                        #             *++++
                                                        #    S----------E S---E  store S&E because possibly multiple regions are involved
                                                        #             *++++++    store S&E until E is beyond the end of +'s, region between E and next S is not masked
                                                        if (start_pos[-1] <= location) and (end_pos[-1] < location+extension) and (end_pos[-1] >= location):
                                                            #start_pos and end_pos have been stored as read
                                                            pass

                                                        #  if (start_pos >= location+extension):
                                                        #        S----------E   'n's or '-'s prior to masking region are not masked, unless they span a previous region
                                                        # *++++
                                                        elif (start_pos[-1] >= location+extension):
                                                            # Process saved past mask regions - against current interval of 'n's or '-'s
                                                            # A current string of 'n's or '-'s may span several Mask regions.
                                                            # Masked regions are not printed, but regions between masked regions need to be printed.

                                                            process_past_regions()
                    

                                                        #    S----------E    'n's or '-'s prior to masking region are not masked, unless they span a previous region
                                                        # *++++                                                                                               

                                                        elif (start_pos[-1] > location) and (start_pos[-1] < location+extension) and (end_pos[-1] >= location+extension):
                                                            # Process saved past mask regions - against current interval of 'n's or '-'s
                                                            # A current string of 'n's or '-'s may span several Mask regions.
                                                            # Masked regions are not printed, but regions between masked regions need to be printed.
                                                        
                                                            process_past_regions()

                    
                                                        #    S----------E   'n's or '-'s prior to and after masking region are not masked, unless they span another region
                                                        #  *+++++++++++++++
                                                        #    S--E  S--E  S--E  Mask regions in-between
                                                        #  *++++++++++++++++++
                                                        #    S----------E   S---E  'n's or '-'s prior to and after masking region are not masked 
                                                        #  *+++++++++++++++     store S&E until E is beyond the end of +'s, region between E and next S is not masked
                                                        elif (start_pos[-1] > location) and (start_pos[-1] < location+extension) and (end_pos[-1] < location+extension): 
                                                            #start_pos and end_pos have been stored - continue to next mask region
                                                            pass

                                                        #  else impled default
                                                        #    S----------E    'n's or '-'s inside masking region, mask - i.e. do not print
                                                        #        *++++
                                                        elif (start_pos[-1] > location) and (start_pos[-1] < location+extension) and (end_pos[-1] > location+extension):
                                                            # Save the last coordinates of start and end position as new current coordinates
                                                            save_last_SE_as_current()                                                        
                                                    
                                                    elif (extension == 0) and region and aline:  # if the extension ==  0

                                                        # This case should not occur, but for completion of list it is here
                                                        if (start_pos[-1] < location) and (end_pos[-1] < location):   
                                                            #  if (end_pos < location)
                                                            #    S----------E    read next region
                                                            #                    *
                                                            start_pos.clear()  # initialize start_position list
                                                            end_pos.clear()    # initialize end_position list
                                                            pos_index = -1     # initialize position_index                                                    
                                                    
                                                        if (start_pos[-1] > location) and (end_pos[-1] > location):
                                                            #    S----------E    Do not mask this position, process previous S&Es
                                                            #  *
                                                            # Process saved past mask regions - against current interval of 'n's or '-'s
                                                            # A current string of 'n's or '-'s may span several Mask regions.
                                                            # Masked regions are not printed, but regions between masked regions need to be printed.
                                                            
                                                            process_past_regions()

                                                        #  else impled default
                                                        #    S----------E    Do not print, mask this position, do not print
                                                        #        *
                                                        if (start_pos[-1] < location) and (end_pos[-1] > location):
                                                            # Save the last coordinates of start and end position as new current coordinates
                                                            save_last_SE_as_current()
                                                
                                                    #end elif (extension == 0) and region and aline:  # if the extension ==  0
                                                    #end if (extension > 0) and region and aline: elif (extension == 0) and region and aline: else

                                                    # if read another region
                                                    if (location+extension > end_pos[-1]) and region:
                                                        region = fbedin.readline()                                                
                                                        if region:
                                                            positions = region.strip().split('\t') # split the line into columns
                                                            if len(positions) >= 2:
                                                                start_pos.append(int(positions[1])+1)  # start_position of the mask region (zero-based, half-open coords)
                                                                end_pos.append(int(positions[2]))      # end_position of the mask region   (no need to modify the index)
                                                                pos_index += 1                          # increment position_index
                                                            else:
                                                                print(f"Error in format of contents of mask file, no tabs? - {e}")
                                                        #end if region: - hit the end of the masking file
                                                        else:
                                                            # Take care of previous masking regions
                                                            if (pos_index > 0):
                                                                process_past_regions()                                                            
                                                            #    S---E        no masking from location to S
                                                            #  *++++++++                                                            
                                                            elif (start_pos[-1]-location) > 0:
                                                                fout.write('n\t' + str(location) + '\t' + str(start_pos[-1]-location) + '\n')
                                                                # use the last end_pos as the beginning of the unmasked region
                                                                #   S---E          no masking from E to location+extension
                                                                # *++++++++++
                                                            
                                                            if (location+extension > end_pos[-1]):
                                                                if (extension+location-end_pos[-1]-1) > 0:
                                                                    fout.write('n\t' + str(end_pos[-1]+1) + '\t' + str(extension+location-end_pos[-1]-1) + '\n')
                                                            #end else if (pos_index > 0):
                                                        #end else:  if region: hit the end of the masking file
                                                            
                                                #end while (location+extension > end_pos) and region:  while the extension goes beyond the region, get next region
                                                
                                                if (location+extension <= end_pos[-1]) and region and aline:
                                                    process_past_regions()
                                                    
                                            #else: if (location+extension >= start_pos[-1]):
                                        #end for aline in fin:  # For each line in the maple file
                                    #end for region in fbedin:  # file containing masked regions
                                #end with open("mask_chrom1/" + SRR_file.strip(),'w') as fout:   # open file for writing masked maples in new directory

                            except FileNotFoundError as e:  # for output masked maple file written in new directory
                                print(f"Error: The file was not found - {e}")
                            except IOError as e:
                                print(f"Error reading the file - {e}")

                        #end with open(line.strip(), 'r') as fin:  # Open the maple file for reading
                        
                    except FileNotFoundError as e:  # for next maple file in list of maple files, fin
                        print(f"Error: The file was not found - {e}")
                    except IOError as e:
                        print(f"Error reading the file - {e}")
                        
                #end for line in flistin:
            #end with open("fasTAN.bed", 'r') as fbedin:     # open bed file which contains masking regions
            
        except FileNotFoundError as e:   # for bed file with masking regions, fbedin
            print(f"Error: The file was not found - {e}")
        except IOError as e:
            print(f"Error reading the file - {e}")
            
    #end with open("chrom_nhin.list", 'r') as flistin:  # open list of maple files to read
    
except FileNotFoundError as e:    # for list of maple files, flistin
    print(f"Error: The file was not found - {e}")
except IOError as e:
    print(f"Error reading the file - {e}")
