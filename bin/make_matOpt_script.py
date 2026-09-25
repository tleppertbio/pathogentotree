#!/usr/bin/env python3
# Tami Leppert
# 8/13/2026 - read command line bucket, region, project_id
# v 5.0
# 9/22/2026 - read more global variables, commented out cost/size trials for reference
# v 6.0 
#
# program make_matOpt_script.py writes two files matOpt.script and sling_matOpt.script
# called from sra-setup.script, after samples have been processed by mycosnp.
#
# The matOpt.script file is used to load and process the tree in a google cloud vm.
#    Pulling either an old tree to build onto, or starting with an empty tree
#    Pulling a reference.fa for positioning
#    Pulling the bundled mycosnp processed files (created by maples_parsimony_packs.script
#
#    Running usher-sampled - to build a tree (or add on to an existing tree
#    Running matOptimize   - optimize the tree that was built
#    Running matUtils - to create .nwk tree file
#
# The sling_matOpt.script file is used to create a gs vm running matOpt.script
#
import os
import argparse

# 1. Initialize the parser
parser = argparse.ArgumentParser(description="Writes matOpt.script for a tree in google cloud vm")

# 2. Define a Boolean Switch Flag (True if present, False if absent)
parser.add_argument("-v", "--verbose", action="store_true", help="Summarizes input flags")

# 3. Define a Value Flag (Expects data directly after it)
parser.add_argument("-p", "--project", type=str, help="google project id")

# 4. Define a Value Flag (Expects data directly after it)
parser.add_argument("-b", "--bucket", type=str, help="name of google bucket")

# 5. Define a Value Flag (Expects data directly after it)
parser.add_argument("-r", "--region", type=str, help="name of preferred google region")

# 6. Define a Value Flag (Expects data directly after it)
parser.add_argument("-s", "--service", type=str, help="name of preferred service account")

# 7. Parse the command line inputs
args = parser.parse_args()

# 8. Access the parsed arguments in your code
project_id=args.project
bucket_name=args.bucket
google_region=args.region
service_acc=args.service

if args.verbose:
    print("Verbose mode is ON!")

#find the current directory path
from pathlib import Path
current_directory = Path.cwd()
scriptpath=f"{current_directory}"

fileout = "./matOpt.script"
fout = open(fileout, 'w') # open script file, to be executed by vm

#usher_image="quay.io/biocontainers/usher:0.6.6--hdd55de9_4" does not work, later version, does not work.
usher_image="quay.io/biocontainers/usher:0.6.3--hb389108_1"

##############################
# Write the matOpt.script file
##############################
fout.write("#!/bin/bash\n")
fout.write("set -euxo pipefail\n")
fout.write("mkdir -p /home/usera/the_data\n")
fout.write("cd /home/usera/the_data\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp gs://"+bucket_name+"/all_nhin_old_tree.pb.gz /the_data/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp gs://"+bucket_name+"/reference.fa /the_data/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp gs://"+bucket_name+"/combo_all.*.maple /the_data/\n")
fout.write("touch /home/usera/files.downloaded\n")
fout.write("echo '()' > /home/usera/the_data/emptyTree.nwk\n")
#
# Determine if using previous tree or empty tree
previous_tree="/the_data/all_nhin_old_tree.pb.gz"
if os.path.getsize("./all_nhin_old_tree.pb.gz") == 0:
    previous_tree="/the_data/emptyTree.nwk"
#
# Figure out how many combo files exist
file_count = len([f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.maple')])
file_count_minus_one = file_count - 1
next_tree="all.1_tree.pb.gz"
count_index=1
#
# Start with the first combo file
if previous_tree == "/the_data/emptyTree.nwk":
    outstring="docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/usher-sampled --batch_size_per_process 50 -t /the_data/empty_tree.nwk --diff /the_data/combo_all."+str(count_index)+".maple --ref /the_data/reference.fa --optimization_radius 0 -o /the_data/"+next_tree+" -d /the_data 2>&1 | tee /home/usera/the_data/usher-sampled.log\n"
    fout.write(outstring)
else:
    outstring="docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/usher-sampled --batch_size_per_process 50 -i /the_data/all_nhin_old_tree.pb.gz --diff /the_data/combo_all."+str(count_index)+".maple --ref /the_data/reference.fa --optimization_radius 0 -o /the_data/"+next_tree+" -d /the_data 2>&1 | tee /home/usera/the_data/usher-sampled.log\n"
    fout.write(outstring)
#
# Continue with the rest of the combo files
while count_index < file_count_minus_one:
    combo_file="combo_all."+str(count_index-1)+".maple"
    previous_tree=next_tree
    count_index += 1
    next_tree="all."+str(count_index)+"_tree.pb.gz"
    outstring="docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/usher-sampled --batch_size_per_process 50 -i /the_data/"+previous_tree+" --diff /the_data/combo_all."+str(count_index)+".maple --ref /the_data/reference.fa --optimization_radius 0 -o /the_data/"+next_tree+" -d /the_data 2>&1 | tee /home/usera/the_data/usher-sampled.log\n"
    fout.write(outstring)
#
# Finish with the last combo file (if more than just the first one)
previous_tree=next_tree
count_index += 1
next_tree="all."+str(count_index)+"_tree.pb.gz"
if file_count_minus_one > 0:
    outstring="docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/usher-sampled --batch_size_per_process 50 -i /the_data/"+previous_tree+" --diff /the_data/combo_all."+str(count_index)+".maple --ref /the_data/reference.fa --optimization_radius 0 -o /the_data/all_nhin_tree.pb.gz -d /the_data 2>&1 | tee /home/usera/the_data/usher-sampled.log\n"
    fout.write(outstring)
else:
    fout.write("touch /home/usera/tree.built\n")    
    outstring="mv /home/usera/the_data/"+previous_tree+" /home/usera/the_data/all_nhin_tree.pb.gz\n"
    fout.write(outstring)
    fout.write("touch /home/usera/tree.copied\n")
#
# Copy any intermediate files to the bucket
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/all_nhin_tree.pb.gz gs://"+bucket_name+"/\n")
#fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/current-tree.nh gs://"+bucket_name+"/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/final-tree.nh gs://"+bucket_name+"/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/mutation-paths.txt gs://"+bucket_name+"/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/placement_stats.tsv gs://"+bucket_name+"/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/usher-sampled.log gs://"+bucket_name+"/\n")
fout.write("touch /home/usera/build.finished\n")
#
# Run matOptimize
fout.write("docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/matOptimize -i /the_data/all_nhin_tree.pb.gz -m 0.00000001 -o /the_data/all_nhin_opt_tree.pb.gz -M 2 2>&1 | tee /home/usera/the_data/matOptimize.log\n")
fout.write("rc=${PIPESTATUS[0]}\n")
fout.write('echo "matOptimize exit code: $rc" | tee -a /home/usera/the_data/matOptimize.log\n')
fout.write("sudo dmesg -T | tail -300 > /home/usera/the_data/dmesg_snapshot.txt\n")
fout.write("touch /home/usera/opt.finished\n")
#
# Save intermediate files to the bucket
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/all_nhin_opt_tree.pb.gz gs://"+bucket_name+"/\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/matOptimize.log gs://"+bucket_name+"/\n")
#
# Run matUtils to create .nwk file
fout.write("docker run --rm -v /home/usera/the_data:/the_data "+usher_image+" /usr/local/bin/matUtils extract -i /the_data/all_nhin_opt_tree.pb.gz -t /the_data/all_nhin_opt_tree.nwk\n")
#
# Save last files to bucket
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/all_nhin_opt_tree.nwk gs://"+bucket_name+"/\n")
fout.write("touch /home/usera/the_data/optimize.done\n")
fout.write("docker run --rm -v /home/usera/the_data:/the_data google/cloud-sdk:slim gsutil cp /the_data/optimize.done gs://"+bucket_name+"/\n")
fout.write("sudo shutdown now\n")
#fout.write("gcloud compute instances delete matopt-vm --zone="+google_region+"\n")
fout.close()
#####################################
# End of Write the matOpt.script file
#####################################
####################################
# Write the sling_matOpt.script file
####################################

filesout = "./sling_matOpt.script"
fsout = open(filesout, 'w') # open script file, to be executed by vm

#
# Left in pricing a memory configurations, used to determine which works best for 30,000 samples
#
#$0.44/hour 8GB memory per cpu
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=c2d-highmem-56 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$0.18/hour 32GB memory
#fsout.write("gcloud compute instances create matopt-vm --preemptible --zone="+google_region+"-a --machine-type=e2-highmem-4 --boot-disk-size=50 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$0.72/hour 128GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=e2-highmem-16 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$1.42/hour 248GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=m4-hypermem-16 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$9.38/hour 1116GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=c4-highmem-144 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$6.63/hour 756GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=c4d-highmem-96-Issd --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$5.82/hour 704GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=c3-highmem-88 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$5.51/hour 720GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=c3d-highmem-900 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$5.33/hour 768GB memory
#
# Used this configurations, determined which works best for 30,000 samples
#
fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=n4d-highmem-96 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#
# More pricing a memory configurations, used to determine which works best for 30,000 samples
#
#$6.28/hour 768GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=n2-highmem-96 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$5.47/hour 768GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=n2d-highmem-96 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$7.82/hour 1488GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=m4-ultramem-56 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
#$8.84/hour 1488GB memory
#fsout.write("gcloud compute instances create matopt-vm --zone="+google_region+"-a --machine-type=m4-megamem-112 --image-family=cos-stable --image-project=cos-cloud --metadata-from-file startup-script=./matOpt.script --service-account="+service_acc+" --scopes=https://www.googleapis.com/auth/devstorage.read_write 2>&1 | tee /tmp/gcloud-err.txt\n")
fsout.close()
###########################################
# End of Write the sling_matOpt.script file
###########################################
