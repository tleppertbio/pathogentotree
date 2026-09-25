#!/usr/bin/env python3
# Tami Leppert
# 7/9/2025
# v 1.0
# 1/28/2026 move file to vm-scripts and chmod 775
# v 2.0
# 4/22/2026 auto execute file, count available samples/size
# v 3.0
# 4/29/2026 enable command line entry interactive entry
# v 4.0
#
# Program invoke_mycosnp_script.py is called from master_vm.script
# Program invoke_mycosnp_script.py reads in input file, list of samples and sizes
# fin input file contains two columns, tab separated
# first column is size in base #s
# second column is SRR number
#
# finds corresponding vm-scripts/SRR*startup*.script file
# The script file in vm-scripts is used to load and process the SRR in a google cloud vm
# Invokes up to 400 xlow; 300 low; 200 medium; 50 large; 5 xlarge; 2 xxlarge vms during scheduling times.
# They are only queueable if they have a script file in the vm-scripts directory,
#
# An execute vm script is created in this python code.
# Once they have run successfully in the cloud, the vm-script/SRR*startup*.script file is removed,
# otherwise they are moved back to ./vm-scripts
# The execute script vm is moved to ./vm-scripts/done.
#
# This program creates the queuing scripts, then executes them, then moves these execute scripts to ./vm-scripts/done

import os
from pathlib import Path
from datetime import datetime
import subprocess
import glob
import sys

# Get the current time
now = datetime.now()
# Format the current time
format_date_time = now.strftime("%Y-%m-%d.%H.%M")

# Count how many of these sizes you have queued.
xsmall_count = 0
small_count = 0
medium_count = 0
large_count = 0
xlarge_count = 0
xxlarge_count = 0

#find the current directory path
from pathlib import Path
current_directory = Path.cwd()
vm_directory = os.path.join(current_directory, "vm-scripts")
#print(current_directory)
#current_directory = input("Enter the full path to vm-running (e.g. /Users/tleppert/Desktop/candidas/cloud3): ")


#################################################################################################
#### Twiddling about with the number of samples in each size category that have not been queued.
#### Letting the user know how many are available to queue.
#### The sra_now.list stays relatively static until the next large loop downloading another list.
#### The dynamic list of how many samples in the sra_now.list file have already been run is
#### figured here in the next section.
#################################################################################################

# Determine the number of each size file that the user wishes to queue
# Note that the suggested numbers are somewhat arbitrary, sometimes there are no vm's available
# Watch the queuing process to see that machines were available to accept the queuing.

# Get the counts of the number of sample/files available by size - from the sra_list.now (~static)
# Check which of these have been run (usually they no longer have a queue script available).
# Unless they are in the queue and then fail, then their queue script re-appears to be tried again.....
scripts = glob.glob(os.path.join(vm_directory,"*-startup.script"))        # Get all the script files in ./vm-scripts/*-startup.script
split_scripts = [os.path.basename(f) for f in scripts]                    # Strip out the path, leaving just the basename
srr_scripts = [line.split('-')[0] for line in split_scripts]              # Split to just the SRR number

cmd = """awk '$1 < 1000000000' sra_now.list"""                            # command to list the srr with size < 1B in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    xlow = len(set(srr_scripts) & set(srr_numbers))                           # Find the number of xlow scripts available!
else:
    xlow = 0    

cmd = """awk '$1 >= 1000000000 && $1 < 2000000000' sra_now.list"""        # command to list the srr with 1B <=size< 2B in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    low = len(set(srr_scripts) & set(srr_numbers))                            # Find the number of low scripts available!
else:
    low = 0

cmd = """awk '$1 >= 2000000000 && $1 < 4000000000' sra_now.list"""        # command to list the srr with 2B <=size< 4B in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    medium = len(set(srr_scripts) & set(srr_numbers))                         # Find the number of medium scripts available!
else:
    medium = 0

cmd = """awk '$1 >= 4000000000 && $1 < 10000000000' sra_now.list"""       # command to list the srr with 4B <=size<10B in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    large = len(set(srr_scripts) & set(srr_numbers))                          # Find the number of large scripts available!
else:
    large = 0

cmd = """awk '$1 >= 10000000000 && $1 < 15000000000' sra_now.list"""      # command to list the srr with 10B<=size<15B in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    xlarge = len(set(srr_scripts) & set(srr_numbers))                         # Find the number of xlarge scripts available!
else:
    xlarge = 0

cmd = """awk '$1 >= 15000000000' sra_now.list"""                          # command to list the srr with 15B<=size in srr_now.list
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
if result.stdout.strip():
    srr_numbers = [line.split('\t')[1] for line in result.stdout.strip().split('\n')]  # Save just the srr_number[1] not the size[0]
    xxlarge = len(set(srr_scripts) & set(srr_numbers))                        # Find the number of xxlarge scripts available!
else:
    xxlarge=0


print("The max number is the number of samples you can queue now.")
print("The queue order is as listed in the sra_now.list file (by size category).")
print("The number of samples available for queuing at this size range is also listed.")
print("The samples available to queue (by size) are determined by the sra_now.list file and by make_mycosnp_script.py output.")
print("If the number available to queue > the limit, you may start a new queue at a different time.")
print("e.g. suggested wait time - several hours from now for small runs, a couple of days for xlarge runs.")

if len(sys.argv) == 1:
    xlow_max = int(input("Enter the number of xlow (<1GB) sra files to queue (1000 max, " + str(xlow) + " avail): "))
    low_max = int(input("Enter the number of low (1-<2GB) sra files to queue (1000 max, " + str(low) + " avail): "))
    medium_max = int(input("Enter the number of medium (2-<4GB) sra files to queue (1000 max, " + str(medium) + " avail): "))
    large_max = int(input("Enter the number of large (>=4GB-10GB) sra files to queue (1000 max, " + str(large) + " avail): "))
    xlarge_max = int(input("Enter the number of xlarge (>=10-15GB) sra files to queue (100 max, " + str(xlarge) + " avail): "))
    xxlarge_max = int(input("Enter the number of xxlarge (>=15GB) sra files to queue (10 max, " + str(xxlarge) + " avail): "))
    project_id = input("Enter the google project id e.g. c-auris-cdc: ")
    google_region = input("Enter the google_region e.g. us-west1 : ")
    pathogen_image = input("Enter the pathogen_image e.g. ghcr.io/tleppertbio/pathogentotree:1.0.0 : ")
    service_account = input("Enter the service_account e.g. 250856040547-compute@developer.gserviceaccount.com: ")        
else:
    xlow_max = int(sys.argv[1])
    low_max = int(sys.argv[2])
    medium_max = int(sys.argv[3])
    large_max = int(sys.argv[4])
    xlarge_max = int(sys.argv[5])
    xxlarge_max = int(sys.argv[6])
    project_id = sys.argv[7]
    google_region = sys.argv[8]
    pathogen_image = sys.argv[9]
    service_account = sys.argv[10]
    
# open input file and output files
fin = open("sra_now.list", 'r')
if xlow_max > 0:
    filexlow = f"execute-vm-xlow-{format_date_time}.script"
    foutxlow = open(filexlow, 'w')
if low_max > 0:
    filelow = f"execute-vm-low-{format_date_time}.script"
    foutlow = open(filelow, 'w')
if medium_max > 0:
    filemed = f"execute-vm-med-{format_date_time}.script"
    foutmed = open(filemed, 'w')
if large_max > 0:
    filelarge = f"execute-vm-large-{format_date_time}.script"
    foutlarge = open(filelarge, 'w')
if xlarge_max > 0:
    filexlarge = f"execute-vm-xlarge-{format_date_time}.script"
    foutxlarge = open(filexlarge, 'w')
if xxlarge_max > 0:
    filexxlarge = f"execute-vm-xxlarge-{format_date_time}.script"
    foutxxlarge = open(filexxlarge, 'w')

#################################################################################################
#################################################################################################
#### Read from sra_now.list file, find if execute script exists for it, create a vm submit script
#### Processes that have run and were successful will have their execute scripts deleted.
#### vm submit scripts get created/executed in this python script then moved to ./vm-scripts/done
#################################################################################################
#################################################################################################
# for each line in input sra file list
for line in fin:

    # debug print("line: " + line.strip())
    # split the line into columns, two columns
    columns = line.strip().split('\t')

    # get the sra string of the second column put it into srr_number
    srr_number = columns[1]
    srr_size = columns[0]
    lower_srr_number = srr_number.lower()  # lower case the srr or err number
    vm1 = 0     # If run needs to be not preempted instead of preempted
#    if int(srr_size) >= 2000000000:  # Anything >= 2GB is not preemptible
#    if int(srr_size) >= 4000000000:  # Anything >= 4GB is not preemptible
#    if int(srr_size) >= 10000000000:  # Anything >= 10GB is not preemptible
    if int(srr_size) >= 90000000000:  # Anything >= 90GB is not preemptible
        vm1 = 1
        filein = f"{srr_number}-startup-vm1.script"
        filepathin = f"{current_directory}/vm-scripts/{srr_number}-startup-vm1.script"        
    if vm1 == 0:                    # else is preemptible
        filein = f"{srr_number}-startup.script"
        filepathin = f"{current_directory}/vm-scripts/{srr_number}-startup.script"

    filein_path = Path(filepathin)
    
    if filein_path.exists():
        # variable initialization
        xsmall_size = 0
        small_size = 0
        medium_size = 0
        large_size = 0
        xlarge_size = 0
        xxlarge_size = 0
        
        # file size evaluation
        if int(srr_size) < 1000000000:  # XSmall
            xsmall_size = 1
        elif int(srr_size) < 2000000000:  # Small
            small_size = 1        
        elif int(srr_size) < 4000000000:  # Medium
            medium_size = 1                
        elif int(srr_size) < 10000000000:  # Large
            large_size = 1                        
        elif int(srr_size) < 15000000000:  # XLarge
            xlarge_size = 1                        
        elif int(srr_size) >= 15000000000:  # XXLarge
            xxlarge_size = 1                        
        #debug print("3 columns, position: " + columns[1] + " number: " + columns[2])

        #
        # Write the scripts that will queue the vms
        #
        #1000 of these
        if (xsmall_size == 1) and (xsmall_count < xlow_max):
            xsmall_count += 1
            foutxlow.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=e2-highmem-4 --boot-disk-size=50 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutxlow.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutxlow.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutxlow.write("else\n")
            foutxlow.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/xlow/" + filein + "\n")
            foutxlow.write("fi\n")
        # 1000 of these
        if (small_size == 1) and (small_count < low_max):
            small_count += 1
#            foutlow.write('gcloud compute instances create-with-container --machine-type=e2-highmem-16 --boot-disk-size=100 \n')
            foutlow.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=e2-highmem-4 --boot-disk-size=50 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutlow.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutlow.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutlow.write("else\n")
            foutlow.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/low/" + filein + "\n")
            foutlow.write("fi\n")            
        # 1000 of these
        if (medium_size == 1) and (medium_count < medium_max):
            medium_count += 1
#            foutmed.write('gcloud compute instances -pathogen-vm1 --machine-type=n1-highmem-32 --boot-disk-size=300\n')
            foutmed.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=e2-highmem-4 --boot-disk-size=50 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutmed.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutmed.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutmed.write("else\n")
            foutmed.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/medium/" + filein + "\n")
            foutmed.write("fi\n")            
        # 10 of these
        if (large_size == 1) and (large_count < large_max):
            large_count += 1
#            foutlarge.write('gcloud compute instances -pathogen-vm1 --preemptible --zone=us-west1-c --machine-type=n2d-highmem-48 --boot-disk-size=500\n')
            foutlarge.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=n4-highmem-8 --boot-disk-size=200 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutlarge.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutlarge.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutlarge.write("else\n")
            foutlarge.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/large/" + filein + "\n")
            foutlarge.write("fi\n")            
        if (xlarge_size == 1) and (xlarge_count < xlarge_max):
            xlarge_count += 1
            foutxlarge.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=n4-highmem-8 --boot-disk-size=200 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutxlarge.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutxlarge.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutxlarge.write("else\n")
            foutxlarge.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/xlarge/" + filein + "\n")
            foutxlarge.write("fi\n")       
        if (xxlarge_size == 1) and (xxlarge_count < xxlarge_max):
            xxlarge_count += 1
            foutxxlarge.write('gcloud compute instances create ' + lower_srr_number + '-pathogen-vm --preemptible --zone=' + google_region + '-a --machine-type=e2-highmem-16 --boot-disk-size=500 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./vm-scripts/' + srr_number + '-startup.script --service-account=' + service_account + ' --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n')
            foutxxlarge.write("if grep -q 'ERROR' /tmp/gcloud-err.txt; then\n")
            foutxxlarge.write("  grep 'ERROR' /tmp/gcloud-err.txt\n")
            foutxxlarge.write("else\n")
            foutxxlarge.write("  mv " + str(current_directory) + "/vm-scripts/" + filein + " " + str(current_directory) + "/vm-running/xxlarge/" + filein + "\n")
            foutxxlarge.write("fi\n") 

# close files            
fin.close()

###############################################################################################################
###############################################################################################################
#### For submit script, Chmod to 775, Copy to ./vm-running/subdir, Execute file, Move file to ./vm-scripts/done
###############################################################################################################
###############################################################################################################

# if /vm-scripts/done does not exist, create it
runpath = os.path.join(current_directory, "vm-scripts/done")
path_exists=Path(runpath)
path_exists.mkdir(parents=True,exist_ok=True)

# File cleanup and chmod
if xlow_max > 0:
    foutxlow.close()
    #check if current_directory/vm-runnning/xlow exists, if not create it.
    xlowpath=os.path.join(current_directory, "vm-running/xlow")
    path_exists=Path(xlowpath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filexlow,0o775)
    if os.path.getsize(filexlow) == 0:
        os.remove(filexlow)            
if low_max > 0:
    foutlow.close()
    #check if current_directory/vm-runnning/low exists, if not create it.
    lowpath=os.path.join(current_directory, "vm-running/low")
    path_exists=Path(lowpath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filelow,0o775)
    if os.path.getsize(filelow) == 0:
        os.remove(filelow)        
if medium_max > 0:
    foutmed.close()
    #check if current_directory/vm-runnning/medium exists, if not create it.
    medpath=os.path.join(current_directory, "vm-running/medium")
    path_exists=Path(medpath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filemed,0o775)
    if os.path.getsize(filemed) == 0:
        os.remove(filemed)    
if large_max > 0:
    foutlarge.close()
    #check if current_directory/vm-runnning/large exists, if not create it.
    largepath=os.path.join(current_directory, "vm-running/large")
    path_exists=Path(largepath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filelarge,0o775)
    if os.path.getsize(filelarge) == 0:
        os.remove(filelarge)
if xlarge_max > 0:
    foutxlarge.close()
    #check if current_directory/vm-runnning/xlarge exists, if not create it.
    xlargepath=os.path.join(current_directory, "vm-running/xlarge")
    path_exists=Path(xlargepath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filexlarge,0o775)
    if os.path.getsize(filexlarge) == 0:
        os.remove(filexlarge)
if xxlarge_max > 0:
    foutxxlarge.close()    
    #check if current_directory/vm-runnning/xxlarge exists, if not create it.
    xxlargepath=os.path.join(current_directory, "vm-running/xxlarge")
    path_exists=Path(xxlargepath)
    path_exists.mkdir(parents=True,exist_ok=True)
    # chmod to 775
    os.chmod(filexxlarge,0o775)
    if os.path.getsize(filexxlarge) == 0:
        os.remove(filexxlarge)
