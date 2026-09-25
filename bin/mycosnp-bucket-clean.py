#!/usr/bin/env python3
# Tami Leppert
# 5/5/2025
# v 1.0
# 1/24/2026 more robust
# v 2.0
# 5/13/2026 add notpaired
#
# Program mycosnp-bucket-clean.py is called from master_vm.script
# It queries the bucket for a list of files and stores them locally in a file bucket.list.
# fin (bucket.list) contains one filename per line from bucket
#
# Program mycosnp-bucket-clean.py reads in input file (bucket.list)
# Checks to see which .extension exists for each SRR, here's a key
# A) .trimmed, .fastp, vm terminated = restart trimmed-pickup-startup.script
# B) .trimmed, .fastp, .early_bam, vm terminated = restart earlybam-pickup-startup.script
# C) .trimmed, .fastp, (early_bam), .bai*, .bam*, vm terminated = restart finalbam-pickup-startup.script
# D) .trimmed, .fastp, (early_bam), .bai*, .bam*, .vm1_done*, vm terminated = vm2 if size is large
# E) .trimmed, .fastp, .bai, .bam, .vcf, .maple, .done, .finished, vm terminated = finished - completed
# F) .bai, .bam, .vcf, .maple, .done, (vm1_done), .finished, vm terminated = finished - completed
#
# Checks to see what files each SRR has in the bucket.
# if all files are present, then a script is written to clean them up in the clean-bucket-rm-vm.script
#

import subprocess
import shlex
import sys
from datetime import datetime
import os
from pathlib import Path

if len(sys.argv) == 1: 
    PROJECT_ID = input("Enter the google project id e.g. c-auris-cdc: ")
    BUCKET_NAME = input("Enter the google bucket name e.g. test-154312-data-bucket: ")     
    GOOGLE_REGION = input("Enter the google_region e.g. us-west1 : ")
    SERVICE_ACCOUNT = input("Enter the google service_account e.g. 250856040547-compute@developer.gserviceaccount.com : ")
    BIN_DIR = input("Enter the bin dir e.g. /User/name/pathogentotree/bin : ")
    PATHOGEN_IMAGE=input("Enter the pathogen image e.g. ghcr.io/tleppertbio/pathogentotree:1.0.0 : ")
else:
    PROJECT_ID = sys.argv[1]
    print(f"PROJECT_ID '{PROJECT_ID}'")    
    BUCKET_NAME = sys.argv[2]
    print(f"BUCKET_NAME '{BUCKET_NAME}'")        
    GOOGLE_REGION = sys.argv[3]
    print(f"GOOGLE_REGION '{GOOGLE_REGION}'")            
    SERVICE_ACCOUNT = sys.argv[4]
    print(f"SERVICE_ACCOUNT '{SERVICE_ACCOUNT}'")
    BIN_DIR = sys.argv[5]
    print(f"BIN_DIR '{BIN_DIR}'")
    PATHOGEN_IMAGE = sys.argv[6]
    print(f"PATHOGEN_IMAGE '{PATHOGEN_IMAGE}'")                    


############### begin subprocess to write bucket files to output file bucket.list ###################

bucket_filename = "bucket.list"

# gsutil ls command and the bucket path
bucket_path = f"gs://{BUCKET_NAME}/"
command_str = f"gsutil ls {bucket_path}"

# For commands with arguments, it is generally safer to pass them as a list of strings
# using shlex.split() to correctly handle spaces and quotes.
command_list = shlex.split(command_str)

try:
    # Use subprocess.run for simple command execution
    # capture_output=True captures stdout and stderr
    # text=True ensures output is returned as a string rather than bytes (Python 3.7+)
    result = subprocess.run(
        command_list,
        capture_output=True,
        text=True,
        check=True # check=True raises an exception if the command fails
    )

    #print("Command executed successfully. Output:")
    # The standard output (list of files/buckets) is stored in result.stdout
    #print(result.stdout)
    output = result.stdout
    # Write the captured output to a file
    with open(bucket_filename, "w") as f:
        f.write(output)
        print(f"Successfully wrote output to '{bucket_filename}'")

except subprocess.CalledProcessError as e:
    print(f"Command failed with exit code {e.returncode}")
    print(f"Error output (stderr): {e.stderr}")
except FileNotFoundError:
    print("Error: gsutil command not found.")
    print("Please ensure Google Cloud SDK is installed and configured in your system's PATH.")

# Using shell=True (less secure, but powerful)
cmd = f"gsutil ls gs://{BUCKET_NAME}/ > bucket.list"
subprocess.run(cmd, shell=True)

############### end subprocess to write bucket files to output file bucket.list ###################

############### begin subprocess to cp bucket files to local directory  ###################

def gs_cp_command(file_from, file_to):
    """
    Copies files from/to Google Cloud Storage using gsutil cp.
    Args:
    source (str): Source file or gs:// path.
    destination (str): Destination file or gs:// path.
    """
    #cmd = ["gsutil"]
    #cmd.append("cp")
    #cmd.extend([file_from, file_to])
    cmd = f"gsutil cp {file_from} {file_to}"

    try:
        #print(f"Executing: {' '.join(cmd)}")
        # Run command
        result=subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"Copy {file_from} successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error copying file {file_from}: {e.stderr}", file=sys.stderr)
        #raise
        return False

############### end subprocess to cp bucket files to local directory  ###################    

############### begin subprocess to rm bucket files  ###################

def gs_rm_command(file_to_remove):
    """
    rm file from Google Cloud Storage using gsutil rm.
    Args:
    source (str): gs:// path.
    """
    #cmd = ["gsutil","rm"]
    #cmd.append([file_to_remove])
    cmd = f"gsutil rm {file_to_remove}"    

    try:
        # Run command
        result=subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"Successfully deleted: {file_to_remove}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error deleting {file_to_remove}: {e.stderr}", file=sys.stderr)
        return False

############### end subprocess to rm bucket file  ###################

############### begin subprocess to clean bucket files  ###################

def clean_bucket_files():
    # order: trimmed, fastp, (early_bam)>4GB, bai, bam, vcf, maple, done, (vm1_done), finished, terminated
    # A) trimmed, fastp, terminated = restart trimmed
    # B) trimmed, fastp, early_bam, terminated = restart earlybam
    # C) trimmed, fastp, (early_bam), bai*, bam*, terminated = restart finalbam
    # D) trimmed, fastp, (early_bam), bai*, bam*, vm1_done*, terminated = vm2
    # E) trimmed, fastp, bai, bam, vcf, maple, done, finished, terminated = finished
    # F) bai, bam, vcf, maple, done, (vm1_done), finished, terminated = finished
    
    # Did you finished processing sample to end?
    # E) (trimmed, fastp, bai, bam, vcf, (vm1_done), maple, done, finished, terminated)
    if ( done and maple and vcf and finished and terminated):
        #clean up .done and vm instances
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -i {PATHOGEN_IMAGE} -t done -s {last_SRR}\n")
        flog.write(f"{last_SRR} finished\n")            
        #rm .done
        rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
        if gs_rm_command(rmfile):
            flog.write(f"removed {last_SRR}.done from bucket\n")

        #check if current_directory/maple folder exists, if not create it.
        filepath=f"{current_directory}/maple"
        maple_exists=Path(filepath)
        maple_exists.mkdir(parents=True,exist_ok=True)

        #copy maple file from bucket to folder in current directory
        fromfile=f"gs://{BUCKET_NAME}/{last_SRR}.maple"
        tofile=f"{current_directory}/maple/{last_SRR}.maple"
        if gs_cp_command(fromfile,tofile):
            gs_rm_command(fromfile)
            flog.write(f"moved {last_SRR}.maple from bucket to /maple\n")

        #copy .g.vcf.gz file from bucket to folder in current directory                
        fromfile=f"gs://{BUCKET_NAME}/{last_SRR}.g.vcf.gz"
        tofile=f"{current_directory}/maple/{last_SRR}.g.vcf.gz"
        if gs_cp_command(fromfile,tofile):
            gs_rm_command(fromfile)
            flog.write(f"moved {last_SRR}.g.vcf.gz from bucket to /maple\n")

        #Clean up rest of files from bucket for this sample
        if bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.bam from bucket\n")
        if bai == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.bai"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.bai from bucket\n")
        if early_bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.early.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.early.bam from bucket\n")                    
        if vm1_done == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.vm1.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.vm1.done from bucket\n")
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
                    
    # D) trimmed, fastp, (early_bam), bai*, bam*, vm1_done*, terminated = vm2
    # Else if the current sample finished the first half of the process, vm1, then start the next half
    elif ( bam and bai and vm1_done and finished and terminated):
        # fout.write(current_directory + "/queue-vm2.script " + last_SRR + "\n")
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t vm2 -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run vm2\n")                        
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if early_bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.early.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.early.bam from bucket\n")
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")
            
    # C) trimmed, fastp, (early_bam), bai*, bam*, terminated = restart finalbam
    # .bai and .bam only done, can startup vm using these files, no need to recalculate them
    elif ( not maple and not vcf and bam and bai and not vm1_done and terminated):
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t finalbam -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run finalbam\n")                                    
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if early_bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.early.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.early.bam from bucket\n")                    
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")


    # B) trimmed, fastp, early_bam, terminated = restart earlybam
    # .early.bam only done, can startup vm using this file, no need to recalculate it
    elif ( not maple and not vcf and not bam and not bai and not vm1_done and early_bam and terminated):
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t earlybam -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run earlybam\n")                                                
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")
            
    # A) trimmed, fastp, terminated = restart trimmed
    # trimmed only done, can startup vm using these files, no need to recalculate them
    elif ( not maple and not vcf and not bam and not bai and not early_bam and (trimmed == 2) and terminated):
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t trimmed -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run trimmed\n")                                                            
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")

    # If notpaired flag
    elif ( notpaired and finished ):
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t notpaired -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run notpaired\n")                                    
        
    # ODD edge case where 'finished' or 'done' didn't get triggered.  Should re-run and not delete setup files
    elif ( maple and vcf and bam and bai ):
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t finalbam -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        flog.write(f"{last_SRR} run edgecase finalbam\n")                                    
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if early_bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.early.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.early.bam from bucket\n")                    
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")
        
    # only finished nothing else - failed miserably - need to rerun
    else:
        flog.write(f"{last_SRR} not finished.\n")     
        fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t failed -s {last_SRR} -i {PATHOGEN_IMAGE}\n")
        if fastp == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.fastp.log"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.fastp.log from bucket\n")
        if trimmed > 0:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.1.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.1.trimmed.fastq from bucket\n")
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.2.trimmed.fastq"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.2.trimmed.fastq from bucket\n")
        if early_bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.early.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.early.bam from bucket\n")                    
        if bam == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.bam"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.bam from bucket\n")
        if bai == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.bai"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.bai from bucket\n")
        if vm1_done == 1:
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.vm1.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.vm1.done from bucket\n")
        if done == 1:                    
            rmfile=f"gs://{BUCKET_NAME}/{last_SRR}.done"
            if gs_rm_command(rmfile):
                flog.write(f"removed {last_SRR}.done from bucket\n")
    #end if ( done and maple and vcf and finished and terminated):

############### end subprocess to clean bucket files  ###################

##########################################
############### BEGIN MAIN ###############
##########################################

# Find current path
from pathlib import Path
current_directory = Path.cwd()
bin_directory = BIN_DIR
print(current_directory)

################ open input and output files  #######################
# Bucket input file, lists files in the bucket
fin = open(bucket_filename, 'r')

#Get list of vms from the cloud
computefile="compute_instances.list"
cmd = f"gcloud compute instances list > {computefile}"    # Command to list the compute instances into a file
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command

# Read the compute list of vms file
fcomp = open(computefile, 'r')

# Cleanup samples that have run
fileout = "cleanup-mycosnp-vm.script"
fout = open(fileout, 'w+')

# Use timestamp to log when files were cleaned up
logpath = os.path.join(current_directory, "log")   # directory to store logs
log_exists=Path(logpath)                           # Make sure log subdir exists
log_exists.mkdir(parents=True,exist_ok=True)       # Create it if not
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#filelog = logpath / "cleanup-bucket_{timestamp}.log"   # Put log files there
filelog = os.path.join(logpath, "cleanup-bucket_" + str(timestamp) + ".log" )
file_content=f"This file was created at {timestamp}."
flog = open(filelog,'w')
flog.write(f"{file_content}\n")

############# end of open input and output files  ###################


trimmed = 0    # first if not-preemptible or vm1, prev exists if vm2
fastp = 0      # first if not-preemptible or vm1, prev exists if vm2
early_bam = 0  # second if not-preemptible or vm1, prev exists if vm2
bam = 0        # third if not-preemptible or vm1, prev exists if vm2
bai = 0        # third if not-preemptible or vm1, prev exists if vm2
done = 0       # fourth if not-preemptible or vm1 flags .vm1.done, first if vm2
vcf = 0        # fourth if not-preemptible or vm1, first if vm2
maple = 0      # fourth if not-preemptible or vm1, first if vm2
vm1_done = 0   # fourth if vm1
finished = 0   # fifth if not-preemptible or vm1, second if vm2
notpaired = 0  # if notpaired end read format

last_SRR = ""  # Track the last_SRR number to know when you move to a new sample

############# Looking for samples that have completed or partially completed  ###################

# for each line in the bucket file read list of files in the bucket
for line in fin:

    # debug print("line: " + line.strip())
    # find the SRR number
    columns = line.strip().split('/')

    # get the sra string put it into srr_number
    SRR_number = columns[3].split('.')

    #debug print("SRR_number : " + SRR_number[0] )
    #debug print("last_SRR : " + last_SRR )    
    if ( last_SRR == "" ):  # for initial setup.
        last_SRR = SRR_number[0]

    # If you are at a new sample, then process what you've found about the old sample
    if ( last_SRR != SRR_number[0] ):

        ## Look to see if this sample has a terminated vm
        fcomp.seek(0)
        terminated = 0
        for line in fcomp:
            if 'NAME' not in line:  # If not header
                status = line.strip()
                srrlow = status.split('-')[0]    # Get just the srr number but it's lowercase
                cmd = f"""echo {srrlow} | tr '[:lower:]' '[:upper:]'"""   # Uppercase it
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True) # Run the command
                srrhigh = result.stdout.strip()
                if srrhigh == last_SRR:        # Check that the current srr has a vm (and was TERMINATED)
                    if 'TERMINATED' in status:   # If a TERMINATED process
                        terminated = 1

        if terminated:
            clean_bucket_files()  # check all of the bucket files for this SRR remove and write to log and script
    
        # Reset what you've learned about the last sample, ready for next sample
        done = 0
        finished = 0
        maple = 0
        fastp = 0
        vcf = 0
        bam = 0
        bai = 0
        early_bam = 0
        vm1_done = 0
        trimmed = 0
        last_SRR = SRR_number[0]
        terminated = 0
        notpaired = 0        
        
    #end of if ( last_SRR != SRR_number[0] ):        

    # Set file flags for the new sample
    if ( ".trimmed" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        if (trimmed == 1):
            trimmed = 2  # second one was found
        else:
            trimmed = 1
        #debug print("trimmed : " + columns[3] )                        
    elif ( ".early.bam" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        early_bam = 1
    elif ( ".bam" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        bam = 1
    elif ( ".bai" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        bai = 1
    elif ( ".vm1.done" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        vm1_done = 1
    elif ( ".done" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        done = 1
    elif ( ".maple" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        maple = 1
    elif ( ".vcf" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        vcf = 1
    elif ( ".fastp" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        fastp = 1        
    elif ( ".finished" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        finished = 1
    elif ( ".notpaired" in columns[3] ) and ( SRR_number[0] in columns[3] ):
        notpaired = 1        
#end of for line in fin: read next file from bucket

# At the end of the bucket file, proccess the last last_SRR (if not reference)
if ("reference" not in last_SRR) and terminated:
    clean_bucket_files()  # check all of the bucket files for this SRR remove and write to log and script

#end of ifs (for last last_SRR)

############# End of Looking for samples that have completed or partially completed  ###################


############# The compute instances vm's may have died and not generated any output, capture these ###########

# reset compute_instances.list
fcomp.seek(0)

# Read the compute list of vms file
for line in fcomp:
    if 'NAME' not in line:  # If not header
        status = line.strip()
        if 'TERMINATED' in status:  # If a TERMINATED process
            srrlow = status.split('-')[0]    # Get just the srr number but it's lowercase
            cmd = f"""echo {srrlow} | tr '[:lower:]' '[:upper:]'"""   # Uppercase it
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True) # Run the command
            srrhigh = result.stdout.strip()
            fin.seek(0)                     # Reset bucket to check if srrhigh in bucket file
            if srrhigh not in fin.read():   # Check that this srr never created a file (and was TERMINATED)
                fout.write(f"{bin_directory}/reset.script -p {PROJECT_ID} -b {BUCKET_NAME} -r {GOOGLE_REGION} -a {SERVICE_ACCOUNT} -t failed -s {srrhigh} -i {PATHOGEN_IMAGE}\n")
                flog.write(f"echo '{srrhigh}' failed.\n")                     

# chmod 755 fileout
os.chmod(fileout,0o775)

############# End of the compute instances vm's may have died and not generated any output, capture these ###########

# close files
fin.close()
fout.close()
flog.close()
