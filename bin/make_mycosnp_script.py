#!/usr/bin/env python3
# Tami Leppert
# 4/20/2025
# v 1.0
# 7/10/2025
# v 2.0
# 10/13/2025 - on the fly copying reference, new gvcf_to_maple_haploid.py
# v 3.0
# 1/28/2026 - copy file to vm-scripts, chmod 775, curent_directory, and create vm-scripts if not exists
# v 4.0
# 8/13/2026 - read command line bucket, region, project_id
# v 5.0
#
# Program make_mycosnp_script.py is called from sra-setup.script
# This program reads in the sra_now.list, a list of samples to process through the mycosnp algorithm.
# fin sra_now.list contains two columns
# first column is size in bases - anything >=90GB is queued into a non-preemptible vm
# second column is SRR number
#
# For each sample read in, a (sample).script file is created.  For large samples, two scripts are created.
# The (sample).script file is used to process the sample in a google cloud vm
# Another set of scripts sets up the vms and manages the location of the sample script.
#
#

import os
import argparse

# 1. Initialize the parser
parser = argparse.ArgumentParser(description="Writes SRR*.scripts for loading/processing a sample in google cloud vm")

# 2. Define a Boolean Switch Flag (True if present, False if absent)
parser.add_argument("-v", "--verbose", action="store_true", help="Summarizes input flags")

# 3. Define a Value Flag (Expects data directly after it)
parser.add_argument("-p", "--project", type=str, required=True, help="google project id")

# 4. Define a Value Flag (Expects data directly after it)
parser.add_argument("-b", "--bucket", type=str, required=True, help="name of google bucket")

# 5. Define a Value Flag (Expects data directly after it)
parser.add_argument("-r", "--region", type=str, required=True, help="name of preferred google region")

# 6. Define a Value Flag (Expects data directly after it)
parser.add_argument("-i", "--image", type=str, required=True, help="name of image to process samples in gc")

# 7. Parse the command line inputs
args = parser.parse_args()

# 8. Access the parsed arguments in your code
project_id=args.project
bucket_name=args.bucket
google_region=args.region
pathogen_image=args.image

if args.verbose:
    print("Verbose mode is ON!")

#find the current directory path
from pathlib import Path
current_directory = Path.cwd()
#print(current_directory)

#check if current_directory/vm-scripts exists, if not create it.
scriptpath=f"{current_directory}/vm-scripts"
scripts_exists=Path(scriptpath)
scripts_exists.mkdir(parents=True,exist_ok=True)

# open input file, containing first column size of file in number of bases,
# tab separated, second column sample id number SRR# or ERR#
fin = open("sra_now.list", 'r')

# for each line in input file (base size <tab> srr or err number
for line in fin:

    # debug print("line: " + line.strip())
    # split the line into columns, two columns by tab
    columns = line.strip().split('\t')

    #debug print("n columns: " + str(len(columns)))

    # get the sra string of the second column put it into srr_number
    srr_number = columns[1]
    srr_size = columns[0]
    
    fileout2 = ""
    vm1 = 0     # If run needs to be not preempted instead of preempted
#    if int(srr_size) >= 2000000000:  # Anything >= 2GB is not preemptible
#    if int(srr_size) >= 4000000000:  # Anything >= 4GB is not preemptible
#    if int(srr_size) >= 10000000000:  # Anything >= 10GB is not preemptible
    if int(srr_size) >= 90000000000:  # Anything >= 90GB is not preemptible
        vm1 = 1
        fileout = srr_number + "-startup-vm1.script"  # script file to process first half, can be preemptible
        fileout2 = srr_number + "-startup-vm2.script" # script file to process second half (gatk), is not preemptible
    if vm1 == 0:                    # Anything < 90GB is preemptible only one file is needed to process sample
        fileout = srr_number + "-startup.script"

    # See docker-sample.flow for script information        
    fout = open(fileout, 'w') # open script file, to be executed by vm
    if vm1 == 1:
        fout2 = open(fileout2, 'w')
        fout2.write("#!/bin/bash\n")
        #fout2.write("set -euxo pipefail\n")        
        fout2.write("SAMPLE=" + srr_number + "\n")
        fout2.write("mkdir -p /home/usera/the_data\n")
        fout2.write("mkdir -p /home/usera/the_data/reference\n")
        fout2.write("mkdir -p /home/usera/the_data/reference/bwa\n")
        fout2.write("chown usera:usera /home/usera/the_data\n")
        fout2.write("chown usera:usera /home/usera/the_data/reference\n")
        fout2.write("chown usera:usera /home/usera/the_data/reference/bwa\n")
        fout2.write("# Run the docker image for google/cloud-sdk\n")
        fout2.write("docker run -d --mount type=bind,src=/home/usera/the_data,dst=/the_data google/cloud-sdk:slim sleep infinity\n")
        fout2.write("echo 'Waiting for google/cloud-sdk:slim...'\n")
        fout2.write("GSDK_TIMEOUT=300\n")
        fout2.write("GSDK_ELAPSED=0\n")
        fout2.write("GOOGLEDOCKER=google/cloud-sdk:slim\n")
        fout2.write("while [ $GSDK_ELAPSED -lt $GSDK_TIMEOUT ]; do\n")
        fout2.write("    GCONTAINER_ID=$(docker ps -q --filter ancestor=$GOOGLEDOCKER | head -n 1)\n")
        fout2.write("    [ -n \"$GCONTAINER_ID\" ] && break\n")
        fout2.write("    sleep 10; GSDK_ELAPSED=$((GSDK_ELAPSED+10))\n")
        fout2.write("done\n")
        fout2.write("if [ -z \"$GCONTAINER_ID\" ]; then echo 'ERROR: google/cloud-sdk:slim did not start in time' && exit 1; fi\n")
        fout2.write("touch /home/usera/google.runs\n")
        fout2.write("echo \"$GCONTAINER_ID\" > /home/usera/google-cloud-sdk.id\n")
        fout2.write("GOOGLEIMAGE=$GCONTAINER_ID\n")
        fout2.write("# Check if the google/cloud-sdk is running\n")
        fout2.write("GOOGLEDOCKER=google/cloud-sdk:slim\n")
        fout2.write('GCONTAINER_ID=$(docker ps --all --filter ancestor=$GOOGLEDOCKER --format="{{.ID}}" | head -n 1)\n')
        fout2.write('GCONTAINER_STATUS=$(docker inspect --format "{{json .State.Status }}" $GCONTAINER_ID)\n')
        fout2.write('running_str="running"\n')
        fout2.write("if [[ $GCONTAINER_STATUS == *$running_str* ]]; then\n")
        fout2.write("\ttouch /home/usera/google.runs\n")        
        fout2.write("fi\n")
        fout2.write("# Check if the pathogentotree is running\n")
        fout2.write("docker run -d --mount type=bind,src=/home/usera/the_data,dst=/the_data " + pathogen_image + " sleep infinity\n")
        fout2.write("echo 'Waiting for pathogentotree...'\n")
        fout2.write("PTREE_TIMEOUT=900\n")
        fout2.write("PTREE_ELAPSED=0\n")
        fout2.write("PATHOGENDOCKER=" + pathogen_image + "\n")
        fout2.write("while [ $PTREE_ELAPSED -lt $PTREE_TIMEOUT ]; do\n")
        fout2.write("    CCONTAINER_ID=$(docker ps -q --filter ancestor=$PATHOGENDOCKER | head -n 1)\n")
        fout2.write("    [ -n \"$CCONTAINER_ID\" ] && break\n")
        fout2.write("    sleep 10; PTREE_ELAPSED=$((PTREE_ELAPSED+10))\n")
        fout2.write("done\n")
        fout2.write("if [ -z \"$CCONTAINER_ID\" ]; then echo 'ERROR: pathogentotree did not start in time' && exit 1; fi\n")
        fout2.write("touch /home/usera/docker.runs\n")
        fout2.write("echo \"$CCONTAINER_ID\" > /home/usera/pathogentotree.id\n")
        fout2.write("PATHOGENIMAGE=$CCONTAINER_ID\n")
        fout2.write('CCONTAINER_STATUS="running"\n')
        fout2.write("# grab the docker image for google/cloud-sdk:slim and the pathogentotree\n")
        fout2.write('if [[ $CCONTAINER_STATUS == *$running_str* ]] && [[ $GCONTAINER_STATUS == *$running_str* ]]; then\n')
        fout2.write("\t# housekeeping\n")
        fout2.write("\tdocker exec $PATHOGENIMAGE ln -s /usr/bin/python3 /usr/bin/python\n")
        fout2.write("\t# pull reference files\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.cluster /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.coords /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.delta /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.dict /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fa /the_data/reference\n")        
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fasta /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fasta.fai /the_data/reference\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.amb /the_data/reference/bwa\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.ann /the_data/reference/bwa\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.bwt /the_data/reference/bwa\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.pac /the_data/reference/bwa\n")
        fout2.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.sa /the_data/reference/bwa\n")
        fout2.write("\tdocker exec -w /the_data/reference $PATHOGENIMAGE fix-id.sh\n")
        fout2.write("fi # if $CCONTAINER_STATUS && $GCONTAINER_STATUS are both == *$running_str*\n")
        fout2.write("# pull bam data\n")
        fout2.write("docker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/$SAMPLE.bam /the_data/$SAMPLE.bam\n")
        fout2.write("docker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/$SAMPLE.bai /the_data/$SAMPLE.bai\n")
        fout2.write("chown usera:usera *.id\n")
        fout2.write("chown usera:usera *.pathogen\n")
        fout2.write("# if data was pulled from bucket\n")
        fout2.write("if [ -f /home/usera/the_data/${SAMPLE}.bam ]; then\n")
        fout2.write("\ttouch /home/usera/running.gatk\n")    
        fout2.write('\tdocker exec -w /the_data $PATHOGENIMAGE /home/user/gatk-4.6.1.0/gatk --java-options "-Xms6G -Xmx6G" HaplotypeCaller -R reference/reference.fasta -I $SAMPLE.bam -O $SAMPLE.g.vcf.gz -ERC GVCF --sample-ploidy "1"\n')
        fout2.write("\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")    
        fout2.write("\t# if gatk ran\n")            
        fout2.write("\tif [ -f /home/usera/the_data/$SAMPLE.g.vcf.gz ]; then\n")
        fout2.write("\t\ttouch /home/usera/running.vcf_to_maple\n")
        fout2.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE /usr/bin/python3 /bin/gvcf_to_maple_haploid.py -i /the_data/$SAMPLE.g.vcf.gz -DP 20 -GQ 99 -o AND\n")
        fout2.write("\t\t# cleanup from gatk\n")                
        fout2.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.bam\n")
        fout2.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.bai\n")
        fout2.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.g.vcf.gz.tbi\n")
        fout2.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")    
        fout2.write("\t\t# if vcf_to_maple ran\n")
        fout2.write("\t\tif [ -f /home/usera/the_data/$SAMPLE.maple ]; then\n")
        fout2.write("\t\t\t# move files back to data-bucket\n")
        fout2.write("\t\t\ttouch /home/usera/the_data/$SAMPLE.done\n")
        fout2.write("\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")        
        fout2.write("\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.maple gs://" + bucket_name + "/$SAMPLE.maple\n")
        fout2.write("\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.g.vcf.gz gs://" + bucket_name + "/$SAMPLE.g.vcf.gz\n")
        fout2.write("\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.done gs://" + bucket_name + "/$SAMPLE.done\n")                        
        fout2.write("\t\tfi # if [ -f $SAMPLE.maple ]; then\n")
        fout2.write("\tfi # if [ -f $SAMPLE.g.vcf.gz ]; then\n")    
        fout2.write("fi # if [ -f $SAMPLE.bam ]; then\n")        
        fout2.write("touch /home/usera/the_data/$SAMPLE.finished\n")
        fout2.write("docker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
        fout2.write("docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.finished gs://" + bucket_name + "/$SAMPLE.finished\n")
        fout2.write("# gcloud compute instances stop vm\n")
        fout2.write("sudo shutdown now\n")        
        fout2.close()
        # move file to /vm-scripts and chmod to 775
        filemv2 = f"{current_directory}/vm-scripts/{fileout2}"
        os.rename(fileout2,filemv2)
        os.chmod(filemv2,0o775)        


    #debug print("3 columns, position: " + columns[1] + " number: " + columns[2])
    fout.write("#!/bin/bash\n")
    #fout.write("set -euxo pipefail\n")            
    fout.write("SAMPLE=" + srr_number + "\n")
    fout.write("mkdir -p /home/usera/the_data\n")
    fout.write("mkdir -p /home/usera/the_data/reference\n")
    fout.write("mkdir -p /home/usera/the_data/reference/bwa\n")
    fout.write("chown usera:usera /home/usera/the_data\n")
    fout.write("chown usera:usera /home/usera/the_data/reference\n")
    fout.write("chown usera:usera /home/usera/the_data/reference/bwa\n")
    fout.write("# Run the docker image for google/cloud-sdk\n")
    fout.write("docker run -d --mount type=bind,src=/home/usera/the_data,dst=/the_data google/cloud-sdk:slim sleep infinity\n")
    fout.write("echo 'Waiting for google/cloud-sdk:slim...'\n")
    fout.write("GSDK_TIMEOUT=300\n")
    fout.write("GSDK_ELAPSED=0\n")
    fout.write("GOOGLEDOCKER=google/cloud-sdk:slim\n")
    fout.write("while [ $GSDK_ELAPSED -lt $GSDK_TIMEOUT ]; do\n")
    fout.write("    GCONTAINER_ID=$(docker ps -q --filter ancestor=$GOOGLEDOCKER | head -n 1)\n")
    fout.write("    [ -n \"$GCONTAINER_ID\" ] && break\n")
    fout.write("    sleep 10; GSDK_ELAPSED=$((GSDK_ELAPSED+10))\n")
    fout.write("done\n")
    fout.write("if [ -z \"$GCONTAINER_ID\" ]; then echo 'ERROR: google/cloud-sdk:slim did not start in time' && exit 1; fi\n")
    fout.write("touch /home/usera/google.runs\n")
    fout.write("echo \"$GCONTAINER_ID\" > /home/usera/google-cloud-sdk.id\n")
    fout.write("GOOGLEIMAGE=$GCONTAINER_ID\n")
    fout.write("# Check if the google/cloud-sdk is running\n")
    fout.write("GOOGLEDOCKER=google/cloud-sdk:slim\n")
    fout.write('GCONTAINER_ID=$(docker ps --all --filter ancestor=$GOOGLEDOCKER --format="{{.ID}}" | head -n 1)\n')
    fout.write('GCONTAINER_STATUS=$(docker inspect --format "{{json .State.Status }}" $GCONTAINER_ID)\n')
    fout.write('running_str="running"\n')
    fout.write("if [[ $GCONTAINER_STATUS == *$running_str* ]]; then\n")
    fout.write("\ttouch /home/usera/google.runs\n")        
    fout.write("fi\n")
    
    fout.write("# Check if the pathogentotree is running\n")
    fout.write("docker run -d --mount type=bind,src=/home/usera/the_data,dst=/the_data " + pathogen_image + " sleep infinity\n")
    fout.write("echo 'Waiting for pathogentotree...'\n")
    fout.write("PTREE_TIMEOUT=900\n")
    fout.write("PTREE_ELAPSED=0\n")
    fout.write("PATHOGENDOCKER=" + pathogen_image + "\n")
    fout.write("while [ $PTREE_ELAPSED -lt $PTREE_TIMEOUT ]; do\n")
    fout.write("    CCONTAINER_ID=$(docker ps -q --filter ancestor=$PATHOGENDOCKER | head -n 1)\n")
    fout.write("    [ -n \"$CCONTAINER_ID\" ] && break\n")
    fout.write("    sleep 10; PTREE_ELAPSED=$((PTREE_ELAPSED+10))\n")
    fout.write("done\n")
    fout.write("if [ -z \"$CCONTAINER_ID\" ]; then echo 'ERROR: pathogentotree did not start in time' && exit 1; fi\n")
    fout.write("touch /home/usera/docker.runs\n")
    fout.write("echo \"$CCONTAINER_ID\" > /home/usera/pathogentotree.id\n")
    fout.write("PATHOGENIMAGE=$CCONTAINER_ID\n")
    fout.write('CCONTAINER_STATUS="running"\n')    
    fout.write("if [[ $CCONTAINER_STATUS == *$running_str* ]] && [[ $GCONTAINER_STATUS == *$running_str* ]]; then\n")
    fout.write("\t# housekeeping\n")
    fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")    
    fout.write("\tdocker exec -w /the_data/reference $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\tdocker exec -w /the_data/reference/bwa $PATHOGENIMAGE fix-id.sh\n")                  
    fout.write("\tdocker exec $PATHOGENIMAGE ln -s /usr/bin/python3 /usr/bin/python\n")
    fout.write("\t# pull reference files\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.cluster /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.coords /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.delta /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.dict /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fa /the_data/reference\n")    
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fasta /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.fasta.fai /the_data/reference\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.amb /the_data/reference/bwa\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.ann /the_data/reference/bwa\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.bwt /the_data/reference/bwa\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.pac /the_data/reference/bwa\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp gs://" + bucket_name + "/reference.sa /the_data/reference/bwa\n")
    fout.write("\tdocker exec -w /the_data/reference $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\tdocker exec -w /the_data/reference/bwa $PATHOGENIMAGE fix-id.sh\n")                  
    fout.write("\tchown usera:usera *.id\n")
    fout.write("\tchown usera:usera *.pathogen\n")
    fout.write("\t# pull and process sra data\n")
    if "SRR" in srr_number:
        fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE execute-pull.sh $SAMPLE\n")
    else:  # expecting if not 'SRR' then 'ERR'
        fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE srr-pull.sh $SAMPLE\n")
    fout.write("fi # if $CCONTAINER_STATUS && $GCONTAINER_STATUS both == *$running_str*\n")        
    fout.write("# if data was pulled from ncbi\n")
    fout.write("if [ -f /home/usera/the_data/${SAMPLE}_1.fastq ]; then\n")
    fout.write("\ttouch /home/usera/running.seqkit\n")    
    fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE seqkit pair -1 ${SAMPLE}_1.fastq -2 ${SAMPLE}_2.fastq --threads 2\n")
    fout.write("\t# cleanup from execute-pull\n")    
    fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE rm -rf $SAMPLE\n")
    fout.write("\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t# if seqkit ran\n")        
    fout.write("\tif [ -f /home/usera/the_data/${SAMPLE}_1.paired.fastq ]; then\n")
    fout.write("\t\ttouch /home/usera/running.FaQCs\n")    
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE FaQCs -d . -1 ${SAMPLE}_1.paired.fastq -2 ${SAMPLE}_2.paired.fastq --prefix $SAMPLE -t 2 --debug 2 &> /home/usera/the_data/${SAMPLE}.fastp.log\n")
    fout.write("\t\t# cleanup from seqkit\n")            
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_1.fastq\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_2.fastq\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.base_content.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.for_qual_histogram.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.length_count.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.stats.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f qa.$SAMPLE.base_content.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f qa.$SAMPLE.for_qual_histogram.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f qa.$SAMPLE.length_count.txt\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.base.matrix\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.quality.matrix\n")        
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f qa.$SAMPLE.base.matrix\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f qa.$SAMPLE.quality.matrix\n")
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.unpaired.trimmed.fastq\n")
    # fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.fastp.log\n")                
    fout.write("\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.fastp.log gs://" + bucket_name + "/$SAMPLE.fastp.log\n")
    fout.write("\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.1.trimmed.fastq gs://" + bucket_name + "/$SAMPLE.1.trimmed.fastq\n")
    fout.write("\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.2.trimmed.fastq gs://" + bucket_name + "/$SAMPLE.2.trimmed.fastq\n")    
    fout.write("\t\t# if FaQCs ran\n")                
    fout.write("\t\tif [ -f /home/usera/the_data/${SAMPLE}.1.trimmed.fastq ]; then\n")
    fout.write("\t\t\ttouch /home/usera/running.bwa\n")    
    fout.write('\t\t\tdocker exec -w /the_data $PATHOGENIMAGE sh -c "bwa mem -t 2 reference/bwa/reference $SAMPLE.1.trimmed.fastq $SAMPLE.2.trimmed.fastq | samtools sort --threads 2 -o /the_data/$SAMPLE.bam"\n')
    fout.write("\t\t\t# cleanup from FaQCs\n")        
    fout.write("\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_1.paired.fastq\n")
    fout.write("\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_2.paired.fastq\n")
    if int(srr_size) >= 4000000000:  # Anything >= 4GB then save the intermediate .bam
        fout.write("\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bam gs://" + bucket_name + "/${SAMPLE}.early.bam\n")
    fout.write("\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\t\t# if bwa ran\n")
    fout.write("\t\t\tif [ -f /home/usera/the_data/$SAMPLE.bam ]; then\n")
    fout.write("\t\t\t\ttouch /home/usera/running.MarkDuplicates\n")        
    fout.write("\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar MarkDuplicates REMOVE_DUPLICATES=true ASSUME_SORT_ORDER=coordinate VALIDATION_STRINGENCY=LENIENT I=$SAMPLE.bam O=${SAMPLE}_markdups.bam M=${SAMPLE}_markdups.MarkDuplicates.metrics.txt\n")
    fout.write("\t\t\t\t# cleanup from bwa\n")            
    fout.write("\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.1.trimmed.fastq\n")
    fout.write("\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.2.trimmed.fastq\n")
    fout.write("\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\t\t\t# if MarkDuplicates ran\n")                
    fout.write("\t\t\t\tif [ -f /home/usera/the_data/${SAMPLE}_markdups.bam ]; then\n")
    fout.write("\t\t\t\t\ttouch /home/usera/running.CleanSam\n")            
    fout.write("\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar CleanSam -I ${SAMPLE}_markdups.bam -O ${SAMPLE}_clean.bam\n")
    fout.write("\t\t\t\t\t# cleanup from MarkDuplicates\n")                    
    fout.write("\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.bam\n")
    fout.write("\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\t\t\t\t# if CleanSam ran\n")                        
    fout.write("\t\t\t\t\tif [ -f /home/usera/the_data/${SAMPLE}_clean.bam ]; then\n")
    fout.write("\t\t\t\t\t\ttouch /home/usera/running.FixMateInformation\n")                
    fout.write("\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar FixMateInformation -I ${SAMPLE}_clean.bam -O ${SAMPLE}_fixmate.bam --VALIDATION_STRINGENCY LENIENT\n")
    fout.write("\t\t\t\t\t\t# cleanup from CleanSam\n")                            
    fout.write("\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_markdups.bam\n")
    fout.write("\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_markdups.MarkDuplicates.metrics.txt\n")    
    fout.write("\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\t\t\t\t\t# if FixMateInformation ran\n")                                
    fout.write("\t\t\t\t\t\tif [ -f /home/usera/the_data/${SAMPLE}_fixmate.bam ]; then\n")
    fout.write("\t\t\t\t\t\t\ttouch /home/usera/running.AddOrReplaceReadGroups\n")
    fout.write("\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar AddOrReplaceReadGroups --INPUT ${SAMPLE}_fixmate.bam --OUTPUT $SAMPLE.bam -ID id -LB library -PL illumina -PU barcode -SM $SAMPLE -CREATE_INDEX true\n")
    fout.write("\t\t\t\t\t\t\t# cleanup from FixMateInformation\n")
    fout.write("\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_clean.bam\n")
    fout.write("\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bam gs://" + bucket_name + "/$SAMPLE.bam\n")
    fout.write("\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bai gs://" + bucket_name + "/$SAMPLE.bai\n")                
    
    fout.write("\t\t\t\t\t\t\t# if AddOrReplaceReadGroups ran\n")    
    fout.write("\t\t\t\t\t\t\tif [ -f /home/usera/the_data/$SAMPLE.bam ]; then\n")
    if vm1 == 0:  #If a non-preemptible run, then run gatk and vcf_to_maple
        fout.write("\t\t\t\t\t\t\t\ttouch /home/usera/running.gatk\n")    
        fout.write('\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE /home/user/gatk-4.6.1.0/gatk --java-options "-Xms6G -Xmx6G" HaplotypeCaller -R reference/reference.fasta -I $SAMPLE.bam -O $SAMPLE.g.vcf.gz -ERC GVCF --sample-ploidy "1"\n')
        fout.write("\t\t\t\t\t\t\t\t# cleanup AddOrReplaceReadGroups\n")        
        fout.write("\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f ${SAMPLE}_fixmate.bam\n")
        fout.write("\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
        fout.write("\t\t\t\t\t\t\t\t# if gatk ran\n")            
        fout.write("\t\t\t\t\t\t\t\tif [ -f /home/usera/the_data/$SAMPLE.g.vcf.gz ]; then\n")
        fout.write("\t\t\t\t\t\t\t\t\ttouch /home/usera/running.vcf_to_maple\n")
        fout.write("\t\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE /usr/bin/python3 /bin/gvcf_to_maple_haploid.py -i /the_data/$SAMPLE.g.vcf.gz -DP 20 -GQ 99 -o AND\n")
        fout.write("\t\t\t\t\t\t\t\t\t# cleanup from gatk\n")                
        fout.write("\t\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.bam\n")
        fout.write("\t\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.bai\n")
        fout.write("\t\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE rm -f $SAMPLE.g.vcf.gz.tbi\n")
        fout.write("\t\t\t\t\t\t\t\t\tdocker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")        
        fout.write("\t\t\t\t\t\t\t\t\t# if vcf_to_maple ran\n")
        fout.write("\t\t\t\t\t\t\t\t\tif [ -f /home/usera/the_data/$SAMPLE.maple ]; then\n")
        fout.write("\t\t\t\t\t\t\t\t\t\t# move files back to data-bucket\n")
        fout.write("\t\t\t\t\t\t\t\t\t\ttouch /home/usera/the_data/$SAMPLE.done\n")
        fout.write("\t\t\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.maple gs://" + bucket_name + "/$SAMPLE.maple\n")
        fout.write("\t\t\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.g.vcf.gz gs://" + bucket_name + "/$SAMPLE.g.vcf.gz\n")
        fout.write("\t\t\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.done gs://" + bucket_name + "/$SAMPLE.done\n")                        
        fout.write("\t\t\t\t\t\t\t\t\tfi # if [ -f $SAMPLE.maple ]; then\n")
        fout.write("\t\t\t\t\t\t\t\tfi # if [ -f $SAMPLE.g.vcf.gz ]; then\n")
        fout.write("\t\t\t\t\t\t\tfi # if [ -f $SAMPLE.bam ]; then\n")                
    else:
        fout.write("\t\t\t\t\t\t\t\ttouch /home/usera/the_data/$SAMPLE.vm1.done\n")
        fout.write("\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bam gs://" + bucket_name + "/$SAMPLE.bam\n")
        fout.write("\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bai gs://" + bucket_name + "/$SAMPLE.bai\n")
        fout.write("\t\t\t\t\t\t\t\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.vm1.done gs://" + bucket_name + "/$SAMPLE.vm1.done\n")        
        fout.write("\t\t\t\t\t\t\tfi # if [ -f $SAMPLE.bam ]; then\n")        
    fout.write("\t\t\t\t\t\tfi # if [ -f $SAMPLE_fixmate.bam ]; then\n")
    fout.write("\t\t\t\t\tfi # if [ -f $SAMPLE_clean.bam ]; then\n")
    fout.write("\t\t\t\tfi # if [ -f $SAMPLE_markdups.bam ]; then\n")
    fout.write("\t\t\tfi # if [ -f $SAMPLE.bam ]; then\n")
    fout.write("\t\tfi # if [ -f $SAMPLE.1.trimmed.fastq ]; then\n")
    fout.write("\tfi # if [ -f $SAMPLE_1.paired.fastq ]; then\n")
    fout.write("else\n")
    fout.write("\ttouch /home/usera/the_data/$SAMPLE.notpaired\n")
    fout.write("\tdocker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.notpaired gs://" + bucket_name + "/$SAMPLE.notpaired\n")      
    fout.write("fi # if [ -f $SAMPLE_1.fastq ]; then\n")
    fout.write("docker exec -w /the_data $PATHOGENIMAGE fix-id.sh\n")
    fout.write("touch /home/usera/the_data/$SAMPLE.finished\n")
    fout.write("docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.finished gs://" + bucket_name + "/$SAMPLE.finished\n")        
    fout.write("# gcloud compute instances stop vm\n")
    fout.write("sudo shutdown now\n")        
    fout.close()
    # move file to /vm-scripts and chmod to 775
    filemv = f"{current_directory}/vm-scripts/{fileout}"
    os.rename(fileout,filemv)
    os.chmod(filemv,0o775)            
    
# close files            
fin.close()
