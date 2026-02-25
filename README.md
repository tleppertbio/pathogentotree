
# tleppertwood/pathogentotree:latest docker container

**What does this container do?**

Loads a list of sra files from ncbi, compares the files to a reference sequence using google vms, and creates a folder with .g.vcf.gz and .maple files, which contain the edits for each downloaded sra sample.

---

## What will you need

1) [metadata](./metadata.README.md) to determine if you have the correct samples and the size of the sample file.
2) [reference data](./reference.README.md) prepped for analysis using nucmer, bedtools maskfasta, samtools faidx, picard.jar and bwa.
3) [get_started.script](./get_started.script) run to download repos, fix scripts to reflect the google project, bucket and region
4) [invoke bash scripts](#running-makemycosnpscriptpy) to set up and run google cloud pathogentotree docker container analysis.
5) [bucket scripts](#running-mycosnpbucketcleanpy) to download results from your google bucket to your local directory.

## Directory structure on your local machine

In your running directory the scripts will create four directories ./vm-scripts, ./vm-running, ./maple and ./partials.
The vm-running folder will have sub folders for the difference size categories of the sra sample data you have.
It's best to use the same running directory for the reference sequence you are using.  It is possible to
use multiple reference sequences (not simultaneously).
Once a set of runs have completed using a reference sequence, then another reference sequence may be used.

The difference size categories are as follows:
1) <1GB you can queue up to 1000 of these at the same time without overloading the cloud in your zone<sup>*</sup>.
2) 1-<2GB you can queue up to 1000 of these at the same time without overloading the cloud in your zone<sup>*</sup>.
3) 2-<4GB you can queue up to 1000 of these at the same time without overloading the cloud in your zone<sup>*</sup>.
4) 4GB-<10GB you can queue up to 1000 of these at the same time without overloading the cloud in your zone<sup>*</sup>.
5) 10GB-<15GB you can queue up to 100 of these at the same time without overloading the cloud in your zone<sup>*</sup>.
6) =>15GB you can queue up to 10 of these at the same time without overloading the cloud in your zone<sup>*</sup>.

<sup>*</sup>watching if flags warning that vm's are not available during queuing is required.  Queuing in the evening or weekends are recommended for lowering costs and usually more vms are available during off peak times.
[Create a google project](#how-to-create-a-google-project)
[How to pick google zones](#how-to-create-a-bucket-identify-your-google-region-and-viewing-pricing-tablessizes-for-vms)

---

## How to create a google project

1) [create a project](https://developers.google.com/workspace/guides/create-project)
2) [identify the best google region](https://cloud.withgoogle.com/region-picker/ "Google Region Picker").
3) [view google vm pricing tables](https://cloud.google.com/compute/vm-instance-pricing?hl=en "Google vm pricing").

---

## How to create a bucket, identify your google region and viewing pricing tables/sizes for vms.

1) [create a bucket](https://docs.cloud.google.com/storage/docs/creating-buckets "Google Buckets").
2) [identify the best google region](https://cloud.withgoogle.com/region-picker/ "Google Region Picker").
3) [view google vm pricing tables](https://cloud.google.com/compute/vm-instance-pricing?hl=en "Google vm pricing").

---

### get-started.script

Download all of the repos, update the scripts to reflect your
1) google project id 
2) google bucket name
3) know the google region that you want to use     

What is in the [get-started.script](./get-started.script) from [github pathogentotree](http://github.com/tleppertbio/pathogentotree)

---

## Auxiliary programs/methods to use before and after running the docker container tleppertwood/pathogentotree:latest.

### Collection of metadata

**What is the purpose of this step?**

Collecting and reviewing metadata is a critical initial step prior to running analysis.  It enables you to collect two important pieces of information.

1) Collecting only those samples that are relevant to the reference sequence you have chosen.
2) Knowing the size of each of your samples is critical for choosing how many vm's you can queue.

In this example, we are looking for candida haemuli samples.

To get metadata use two methods. Each method can return very different data depending on the organism.

  1) https://www.ncbi.nlm.nih.gov/sra/?term=candida+haemuli
     - select 'Send to:' pulldown in upper right under the sra search bar
     - select the File option button
     - select Format pulldown option 'Full XML'
	 - select 'Create File' button
     - this will download a file called bioproject_result.xml
     
     How to create a nice list of metadata? read [metadata.howto](./metadata.README.md)
     
  3) bigquery https://www.ncbi.nlm.nih.gov/sra/docs/sra-bigquery-examples/
     - You will need to create your own google console cloud bigquery location.
     - You will need an active Google Cloud account with an active project.
     - Make sure you have IAM permissions such as bigquery.datasets.create permission.
     - Go to the BigQuery page in the google cloud console.
     - In the Explorer pane on the left, select the project where you want to create the dataset.
     - Click the View actions (three vertical dots) icon next to your project ID and select Create dataset.
     - On the Create dataset page:
        - For Dataset ID, enter a unique name for your dataset. This name must contain only letters, numbers, or underscores.
        - For Location type, choose a geographic location for the dataset. Note that this location cannot be changed after the dataset is created.
        - Configure any additional options if needed (e.g., default table expiration, description, or encryption settings).
        - Click Create dataset. 

     generate an sql query such as one of these:
     a) SELECT distinct(tax_id) from `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis`
        WHERE name like "%andid%aemuli%"
     b) SELECT * FROM `nih-sra-datastore.sra.metadata` as m
        JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis` as tax ON m.acc = tax.acc
	WHERE tax.tax_id = 45357
     c) SELECT * FROM `nih-sra-datastore.sra.metadata` as m
        JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis_info` as info ON m.acc = info.acc
	JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis` as tax on m.acc = tax.acc
	WHERE tax.tax_id = 45357 and m.librarylayout = "PAIRED"
     d) SELECT * FROM `nih-sra-datastore.sra.metadata` WHERE organism = 'Candidozyma haemuli' OR
        sample_name LIKE '%andid%haemuli%' OR organism LIKE '%andid%haemuli%'

     save the results of your query to a file on your computer.

     How to create a [sra_now.list](./metadata.README.md) from metadata.
 
### Create sra_now.list file

  Create file sra_now.list add SRR#'s or ERR#'s to this list, the list has two columns.
  The first column is the size in bases of the SRR file (used to determine the size of VM to use)
  The second column is the SRR number (ERR# or SRR#) like:
  5888677200(tab)SRR16249997

  This information comes from your metadata results [Collecting Metadata](./metadata.README.md)
  Example [sra_now.list](./sra_now.list) file.

### Create and execute ref-bucket-setup.script file

  Edit the file ref-bucket-setup.script
     This file contains the directories for the following reference files
     How to create these files? read [reference files](./reference.README.md).
     
  The script will copy these files into the bucket for use by the vm's.
     reference.amb
     reference.ann
     reference.bwt
     reference.pac
     reference.sa
     reference.cluster
     reference.coords
     reference.delta
     reference.dict
     reference.fa
     reference.fasta
     reference.fasta.fai

   Use this format in the ref-bucket-setup.script file:
   gsutil cp /Path-to-reference/reference.fa gs://name-of-data-bucket/reference.fa

   Execute this script:
   chmod 775 ./ref-bucket-setup.script
   ./ref-bucket-setup.script

   Example [ref-bucket-setup.script](./ref-bucket-setup.script)

### Running make_mycosnp_script.py

  **What does this do?**
  
  [make_mycosnp_script.py](https://github.com/tleppertbio/make_mycosnp_script) reads in the sra_now.list and creates a vm processing script for each sample.
  These processing scripts need to be pushed (invoked) to an appropriately configured vm size and location.
  The processing scripts interact with the pathogentotree docker image via a google vm.
  This script executes a sequence of programs to compare sample sequences to a reference and finds edit differences
  Edit differences are listed in .g.vcf.gz and .maple files.
  [Diagram of mycosnp based workflow](http://github/tleppertbio/make_mycosnp_script/mycosnp-based-workflow.png)

  **How to run it?**
  
  python3 make_mycosnp_script.py

  **Things to know**
  
  - When the size of the sample file is >= 9GB this script creates two vm process scripts SRR#-startup-vm1.script and SRR#-startup-vm2.script.
  - The two scripts are created as separate processes, because the second half of the protocol can take longer than the 24 hour preemptible window.
  - The second script *-vm2.script is invoked with non-preemptible parameters.
  - A non-preemptible run is more expensive than a preemptible run.
  - If the size of the sample file is < 9GB bases, the process can run with one vm instance.
  - The make_mycosnp_script.py determines when the file size is >= 9GB, this is read in the sra_now.list file.
  - These execute vm files are copied to ./vm-scripts in your working directory and are chmod 775.
  - If the ./vm-scripts folder does not exist, the make_mycosnp_script.py will create it.
  - If you wish to change parameters for any of the internal process, you can modify or specify those parameters in this python code. 
  
  Here is an example of the type of file that is created by this make_mycosnp_scripts.py python program 
  [example mycosnp processing file script](./mycosnp.sample.script) 

### Running invoke_mycosnp_script.py

  **What does this do?**
  
  [invoke_mycosnp_script.py](http://github.com/tleppertbio/invoke_mycosnp_script) reads sra_now.list and finds corresponding vm scripts in ./vm-scripts.
  This python program creates an invoke script which starts the vm with the correct configuration.
  This script pushes the process script to the vm running the docker container tleppertwood/pathogentotree.
  The processing scripts are invoked in the appropriately configured vm size and location.  
  
  **How to run it?**
  
  python3 invoke_mycosnp_script.py

  **Things to know**
  
  - You will need to know the number of samples in each size category of your sample set.
  - The user enters the number of files to queue (up to 1000 in most cases) per size category.
  - The 1000 or 100 or 10 is a recommended number of vms to invoke, occasionally there will not be a vm available to queue.
  - When you execute the ./execute-vm-size-date-time.script watch the execution carefully.
  - You may sometimes see a failed queue because a vm is not available.
  - You can enter '0' for the number of files to queue, if you do not wish to queue any file in that size category.
  - This program makes scripts to invoke the *RR#.scripts in the ./vm-scripts directory
  - These invoke scripts are made executable and moved into the ./vm-scripts directory
  - These directories are created if they don't already exist vm-running, vm-running/xlow, vm-running/low,
    vm-running/medium, vm-running/large, vm-running/xlarge and vm-running/xxlarge

  Here is an example of the type of file that is created by this invoke_mycosnp_scripts.py python program                 
  [example vm invoke script](./execute-vm-large-2026-01-29.15.48.script)

### Execute scripts to invoke docker image on google vms

  **What does this do?**
  
  The user invokes these scripts manually, controlling when the run scripts are invoked.

  **How to run it?**
  
  cd vm-scripts
  ./execute-vm-size-date-time.script

  **Things to know**
  
  - Sometimes there will not be enough vms available to queue.  When you execute the ./execute-vm-size-date-time.script carefully watch the execution.  You may sometimes see a failed queue because a vm is not available.  A failed queue can happen one moment and in the next moment, a vm can become available. A failed vm does not always occur at the end of the execute file, a failed invoke of a vm can happen in the beginning, middle or end of the invoke script.
  - The output of the vm process if completed will be placed in the google bucket.
  - You can monitor if the script is running by looking at Google Cloud, Compute Engine, VM instances/monitoring.
  - The status of the vms will have a green check mark if running, grey circle if not running.
  - You can monitor the bucket by looking at Google Cloud, Cloud Storage, Buckets
  - When the script has run properly (not failed, not crashed, and data is valid), the .g.vcf.gz, .done, .finished and .maple file will be in the bucket.
  - There will be other files in the bucket that will tell you how far the vm got before it crashed.
  - Sometimes, it is easy to just pick up with an intermediate file and continue on processing, rather than restarting from the beginning. [Restarting failed runs](#running-mycosnpbucketcleanpy).
  - When the process script is invoked, the process script is moved from /vm-scripts to /vm-running/size/

### Running mycosnp-bucket-clean.py

  **What does this do?**
  
  This python program looks at the bucket to see if any queued SRR completed to .maple, .g.vcf.gz, .done and .finished.
  It creates a file bucket.list which the program uses to determine if a run has completed successfully or possibly needs re-queuing or has failed.
  The bucket.list file is generated by mycosnp-bucket-clean.py and contains a list of files currently in the bucket.

  Here is an example of a bucket.list file that is created by this mycosnp-bucket-clean.py python program.
  [example bucket.list file](./bucket.list.example)   
  
  **How to run it?**
  
  python3 mycosnp-bucket-clean.py
  
  **Things to know**
  
  - Reads bucket.list to determine which SRAs have a completed .maple and .g.vcf.gz and .finished and .done file.
  - Creates cleanup-mycosnp-vm.script, which processes the finished, or incomplete or failed runs.
  - Note the underlying reset.script actually determines if a vm is 'TERMINATED' or 'RUNNING'.
  - A log will be created of what files were removed.
  - mycosnp-bucket-clean.example explains the list of possible files in the bucket and what order they are generated and by what process. [mycosnp-bucket-clean.example](./mycosnp-bucket-clean.example)

  Here is an example of every type of trigger that can be contained in the cleanup-mycosnp-vm.script file that is created by this mycosnp-bucket-clean.py python program.
  [example cleanup-mycosnp-vm.script](./cleanup-mycosnp-vm.script.example)

  Here is an example of a log file that is created by this mycosnp-bucket-clean.py python program.
  [example cleanup-bucket-DATE.log](./cleanup-bucket_2026-01-30_09-49-39.log)   

### Execute cleanup-mycosnp-vm.script to clean and sort data and pull data from bucket

  **What does this do?**
  
  cleanup-mycosnp-vm.script runs reset.script, a script that executes in six ways.
  Requeues a vm using an earlybam file from the bucket, requeues a vm using a .bam and .bai file from the bucket.
  Requeues a vm using a .1.trimmed.fastq and .2.trimmed.fastq from the bucket.
  Continues queuing the second half of a process vm2's if the first have of a large run is finished.
  Pulls files from the bucket to a local ./maple directory and cleans up old files and vms.
  Flags when a run has failed completely and needs to be requeued by the user.
  Pulls a list of vms to a file compute_instances.list from the google cloud to check on the status as well as finding the zone.       
  The file compute_instances.list is used for determining which vms to remove and how define the components of the remove command.
  
  Here is an example of a bucket.list file that is created by the reset.script.
  [example bucket.list file](./bucket.list.example)

  Here is an example of a compute_instances.list file that is created by this reset.script.
  [example compute_instances.list file](./compute_instances.list.example)
  
  **How to run it?**
  
  ./cleanup-mycosnp-vm.script

  **Things to know**
  
  - reset.script finalbam - requeues partially run samples
  - reset.script done - cleans up finished samples, cleans up the bucket for done runs
  - reset.script vm2 - queues the second half of large runs for the second half run on non-preemptible vms
  - reset.script failed - cleans up failed sample runs
  - can pull scripts from ./partials and modify the sample # so that a partial run can re-start for a sample.
  - reset.script failed moves scripts back into the /vm-running directory to be restarted (often it runs to completion)
  - [partial scripts](#partialscripts)

  Here is an example of every type of trigger that can be contained in the cleanup-mycosnp-vm.script file that is created by the mycosnp-bucket-clean.py python program.
  [example cleanup-mycosnp-vm.script](./cleanup-mycosnp-vm.script.example)

### Reset script
Invoked in the cleanup-mycosnp-vm.script

  **What does this do?**
  
  reset.script is run from cleanup-mycosnp-vm.script, reset.script executes in six ways.
  Requeues a vm using an earlybam file from the bucket, requeues a vm using a .bam and .bai file from the bucket.
  Requeues a vm using a .1.trimmed.fastq and .2.trimmed.fastq from the bucket.
  Continues queuing the second half of a process vm2's if the first have of a large run is finished.
  Pulls files from the bucket to a local ./maple directory and cleans up old files and vms.
  Flags when a run has failed completely and needs to be requeued by the user.
  Pulls a list of vms to a file compute_instances.list from the google cloud to check on the status as well as finding the zone.
  The file compute_instances.list is used for determining which vms to remove and how define the components of the remove command.

  Here is an example of a bucket.list file that is created by this reset.script.
  [example bucket.list file](./bucket.list.example)

  Here is an example of a compute_instances.list file that is created by this reset.script.
  [example compute_instances.list file](./compute_instances.list.example)

  **How to run it?**
  
  ./cleanup-mycosnp-vm.script
  reset.script is run from ./cleanup-mycosnp-vm.script

  **Things to know**
  
  - reset.script finalbam - requeues partially run samples.
  - reset.script done - cleans up finished samples, cleans up the bucket for done runs.
  - reset.script vm2 - queues the second half of large runs for the second half run on non-preemptible vms.
  - reset.script failed - cleans up failed sample runs.
  - can pull scripts from ./partials and modify the sample # so that a partial run can re-start for a sample.
  - reset.script failed moves scripts back into the /vm-running directory to be restarted (often it runs to completion)
  - [partial scripts](https://github.com/tleppertbio/pathogentotree/partials.README.md)

  Here is an example of every type of trigger that can be contained in the cleanup-mycosnp-vm.script file that is created by this mycosnp-bucket-clean.py python program.
  [example cleanup-mycosnp-vm.script](https://github.com/tleppertbio/pathogentotree/cleanup-mycosnp-vm.script.example)

  Here the actual [reset.script](./reset.script) file.

### Partial Scripts
  Invoked if a sample has been partially run and a complete intermediate file has been generated.
  The intermediate file (residing in the bucket), can be pulled into a new vm and the processing can be started from the point after the generation of that (or those) file(s).

  **What do these do?**
  
  reset.script is run from cleanup-mycosnp-vm.script, reset.script executes in six ways, two can be requeued runs.
  Requeues a vm using an .early.bam file from the bucket.
  Requeues a vm using a .1.trimmed.fastq and .2.trimmed.fastq from the bucket.
  Requeues a vm using a .bam and .bai from the bucket.  

  The mycosnp-bucket-clean.example, shows the list of files in the bucket that are required for requeuing
  [mycosnp-bucket-clean.example file](./mycosnp-bucket-clean.example)

  **How to run it?**
  
  reset.script is run when ./cleanup-mycosnp-vm.script is invoked.
  reset.script automatically pulls the partial run scripts from ./partials, adjusts the scripts for the current sample and places the updated script in the vm-scripts folder.
  The user will need to invoke the execute file in the vm-scripts folder that was created by the ./cleanup-mycosnp-vm.script execution.

  **Things to know**
  
  - reset.script finalbam - requeues partially run samples with .bam and .bai files.
  - reset.script trimmed - requeues partially run samples with .1.trimmed.fastq and .2.trimmed.fastq files.
  - reset.script earlybam - requeues partially run samples with the .early.bam file.

  The script for [earlybam-pickup-startup.script](./partials/earlybam-pickup-startup.script)
  The script for [finalbam-pickup-startup.script](./partials/finalbam-pickup-startup.script)
  The script for [trimmed-pickup-startup.script](./partials/trimmed-pickup-startup.script]

### End of project - cleanup

  **What does this do?**
  
  Empties bucket and removes all google vm instances.
  Creates bucket.list and compute_instances.list files.
  Uses bucket.list and compute_instances.list files to determine which files and vms need to be removed.
  It also removes the bucket.list file and the compute_instances.list file when done.
  Use ONLY at the end of an entire analysis when all samples have been run and no more vm's are to be queued.

  Here is an example of a bucket.list file that is created by this reset.script.
  [example bucket.list file](./bucket.list.example)
  
  Here is an example of a compute_instances.list file that is created by this reset.script.
  [example compute_instances.list file](./compute_instances.list.example)
  
  **How to run it?**
  
  ./finish-project-clean.script

  **Things to know**
  
  - There may be files still left in the bucket and possibly files in the vm instances list.
  - You may need to remove them manually.

  Here is the actual [finish-project-clean.script](./finish-project-clean.script)
  
---

### Tutorial to run

In order to run the tutorial,
You have to create a new directory (or reload an existing directory) using the get_started.script

view sra-now.list by typing 'cat sra-now.list'; contains the list of samples to run
view ref-bucket-setup.script by typing 'cat ref-bucket-setup.script'; script to move reference files to the bucket
run ref-bucket-setup.script by typing './ref-bucket-setup.script'; put the reference files into the bucket

run make_mycosnp_script.py by typing 'python3 make_mycosnp_script.py'; make the script to process the sample
run invoke_mycosnp_script.py by typing 'python3 invoke_mycosnp_script.py'; make the script to invoke the sample
move to the vm-scripts folder by typing 'cd ./vm-scripts'; 

run execute-vm-size-date-time.script by typing './execute-vm-size-date-time.script'; invoke the vm
move back to the /example directory by typing 'cd ../'

wait 30 minutes or until the .finished and .done files appear (you may look at the bucket and the running vm)
 - To look at the bucket: https://console.cloud.google.com/storage/browser/YOURBUCKETNAME
 - To look at the vm list: https://console.cloud.google.com/compute/instances?project=YOURPROJECTNAME
 
run mycosnp-bucket-clean.py by typing 'python3 mycosnp-bucket-clean.py'; look for runs to clean up
run cleanup-mycosnp-vm.script by typing './cleanup-mycosnp-vm.script'; cleanup files that have finished
run finish-project-clean.script by typing './finish-project-clean.script'; at the end of the project, cleanup

[tutorial](https://github.com/tleppertbio/pathogentotree/tutorial.README.md)

---

### How to create the docker image tleppertwood/pathogentotree:latest

docker run -it ashedpotatoes/sranwrp:1.1.26
root@f2cc5eb30ffe:#
cd /home
mkdir -p tleppert   # The username here is irrelevant, the userid will be assigned to match your userid
mkdir -p tleppert/the_data   # All data will be piped through the /the_data wormhole
mkdir -p tleppert/the_data/reference     # Reference data is expected to be here
mkdir -p tleppert/the_data/reference/bwa # Reference data is expected to be here
sudo apt-get update
apt-get install -y openjdk-17-jdk
sudo apt update
sudo apt --reinstall install python3 python3-minimal

#in another window outside of docker
#note the f2cc53b30ffe is from running ashedpototoes/sranwrp:1.1.26 and viewing the root@#
docker cp bin/execute-pull.sh f2cc5eb30ffe:/bin
docker cp bin/bwa f2cc5eb30ffe:/bin
docker cp bin/FaQCs f2cc5eb30ffe:/bin
docker cp bin/fasterq-dump-orig.3.2.1 f2cc5eb30ffe:/bin/fasterq-dump
docker cp bin/fix-docker-id.sh f2cc5eb30ffe:/bin
docker cp bin/fix-id.sh f2cc5eb30ffe:/bin
docker cp bin/picard.jar f2cc5eb30ffe:/bin
docker cp bin/prefetch-orig.3.2.1 f2cc5eb30ffe:/bin/prefetch
docker cp bin/samn-pull.sh f2cc5eb30ffe:/bin
docker cp bin/seqkit f2cc5eb30ffe:/bin
docker cp bin/srr-pull.sh f2cc5eb30ffe:/bin
docker cp bin/gvcf_to_maple_haploid.py f2cc5eb30ffe:/bin
docker cp bin/gatk-4.6.1.0.tar f2cc5eb30ffe:/home/tleppert

#back in the docker window
#unpack the gatk just uploaded
cd /home/tleppert
tar -xvf gatk-4.6.1.0.tar
rm gatk-4.6.1.0.tar

#adjust path in the docker
PATH="/home/user/gatk-4.6.1.0:/usr/lib/jvm/java-17-openjdk-amd64/bin:$PATH"

#then exit
exit

(now the image has been modified)
docker commit f2cc5eb30ffe pathogen_tree
sha256:77fd77f6d46c39d2006015c676f7b9a4e03006f1486fd2d6460786867e983a09
(base) 10:12:48 SB:/storage2/tami/C.posadasii/docker$  Tuesday October 14 2025 4.64GB

#docker tag local-image:tagname new-repo:tagname
#docker push new-repo:tagname
docker tag pathogen_tree:latest pathogentotree:latest
docker tag pathogen_tree:latest tleppertwood/pathogentotree:latest
docker push tleppertwood/pathogentotree:latest
latest: digest: sha256:817254ed0a574557853395b4596186f656a62ec5940e870e04794a3415325cee size: 6637
Docker repository 2.21GB

# for a new repository go here:
https://console.cloud.google.com/artifacts/create-repo?project=NAMEOFPROJECT

docker tag tleppertwood/pathogentotree:latest us-west1-docker.pkg.dev/NAMEOFPROJECT/pathogen-repo/pathogentotree
docker push us-west1-docker.pkg.dev/NAMEOFPROJECT/pathogen-repo/pathogentotree

(Now you can run your new image with the new software inside /bin)
docker run --mount type=bind,src=/local/pathname/the_data,dst=/the_data -it pathogen_tree

### Example processing file script using docker image tleppertwood/pathogentotree

[pathogentotree](./mycosnp.sample.script)
#!/bin/bash
#Assign the sample number
SAMPLE=SRR#
#the username does not matter, the userid will be appropriately assigned by fix_id.sh
mkdir -p /home/tleppert/the_data
mkdir -p /home/tleppert/the_data/reference
mkdir -p /home/tleppert/the_data/reference/bwa
chown tleppert:tleppert /home/tleppert/the_data
chown tleppert:tleppert /home/tleppert/the_data/reference
chown tleppert:tleppert /home/tleppert/the_data/reference/bwa
# Run the docker image for google/cloud-sdk
docker run -d --mount type=bind,src=/home/tleppert/the_data,dst=/the_data -it google/cloud-sdk:slim
# Give it time to get going
sleep 60
# Check if the google/cloud-sdk is running
GOOGLEDOCKER=google/cloud-sdk:slim
GCONTAINER_ID=$(docker ps --all --filter ancestor=$GOOGLEDOCKER --format="{{.ID}}" | head -n 1)
GCONTAINER_STATUS=$(docker inspect --format "{{json .State.Status }}" $GCONTAINER_ID)
running_str="running"
if [[ $GCONTAINER_STATUS == *$running_str* ]]; then
        touch /home/tleppert/google.runs
fi
# get pathogentotree running
docker run -d --mount type=bind,src=/home/tleppert/the_data,dst=/the_data -it us-west1-docker.pkg.dev/c-auris-cdc/pathogen-repo/pathogentotree
# Give it time to get going
sleep 60
# Check if the pathogentotree is running
PATHOGENDOCKER=us-west1-docker.pkg.dev/c-auris-cdc/pathogen-repo/pathogentotree
CCONTAINER_ID=$(docker ps --all --filter ancestor=$PATHOGENDOCKER --format="{{.ID}}" | head -n 1)
cat $CCONTAINER_ID >> /home/tleppert/first.$CCONTAINER_ID.pathogen
CCONTAINER_STATUS=$(docker inspect --format "{{json .State.Status }}" $CCONTAINER_ID)
cat $CCONTAINER_STATUS >> /home/tleppert/first.$CCONTAINER_STATUS.pathogen
running_str="running"
if [[ $CCONTAINER_STATUS == *$running_str* ]]; then
        touch /home/tleppert/docker.runs
fi
# grab the docker image for google/cloud-sdk:slim and the pathogentotree
docker ps | grep google | head -n 1 | awk '{print $1}' > /home/tleppert/google-cloud-sdk.id
docker ps | grep us-west1 | head -n 1 | awk '{print $1}' > /home/tleppert/pathogentotree.id
GOOGLEIMAGE=$(<"/home/tleppert/google-cloud-sdk.id")
PATHOGENIMAGE=$(<"/home/tleppert/pathogentotree.id")
if [[ $CCONTAINER_STATUS == *$running_str* ]] && [[ $GCONTAINER_STATUS == *$running_str* ]]; then
        # housekeeping
        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
        docker exec -w /the_data/reference $PATHOGENIMAGE fix-id.sh
        docker exec -w /the_data/reference/bwa $PATHOGENIMAGE fix-id.sh
        docker exec $PATHOGENIMAGE ln -s /usr/bin/python3 /usr/bin/python
        # pull reference files
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.cluster /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.coords /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.delta /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.dict /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.fa /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.fasta /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.fasta.fai /the_data/reference
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.amb /the_data/reference/bwa
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.ann /the_data/reference/bwa
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.bwt /the_data/reference/bwa
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.pac /the_data/reference/bwa
        docker exec $GOOGLEIMAGE gsutil cp gs://test-154312-data-bucket/reference.sa /the_data/reference/bwa
	docker exec -w /the_data/reference $PATHOGENIMAGE fix-id.sh
        docker exec -w /the_data/reference/bwa $PATHOGENIMAGE fix-id.sh
        chown tleppert:tleppert *.id
        chown tleppert:tleppert *.pathogen
        # pull and process sra data
        docker exec -w /the_data $PATHOGENIMAGE execute-pull.sh $SAMPLE
fi # if $CCONTAINER_STATUS && $GCONTAINER_STATUS both == *$running_str*
# if data was pulled from ncbi
if [ -f /home/tleppert/the_data/${SAMPLE}_1.fastq ]; then
        touch /home/tleppert/running.seqkit
        docker exec -w /the_data $PATHOGENIMAGE seqkit pair -1 ${SAMPLE}_1.fastq -2 ${SAMPLE}_2.fastq --threads 2
        # cleanup from execute-pull
	docker exec -w /the_data $PATHOGENIMAGE rm -rf $SAMPLE
        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
        # if seqkit ran
        if [ -f /home/tleppert/the_data/${SAMPLE}_1.paired.fastq ]; then
                touch /home/tleppert/running.FaQCs
		docker exec -w /the_data $PATHOGENIMAGE FaQCs -d . -1 ${SAMPLE}_1.paired.fastq -2 ${SAMPLE}_2.paired.fastq --prefix $SAMPLE -t 2 --debug 2 > /home/tleppert/the_data/${SAMPLE}.fastp.log
                # cleanup from seqkit
                docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_1.fastq
                docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_2.fastq
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.base_content.txt
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.for_qual_histogram.txt
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.length_count.txt
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.stats.txt
                docker exec -w /the_data $PATHOGENIMAGE rm qa.$SAMPLE.base_content.txt
                docker exec -w /the_data $PATHOGENIMAGE rm qa.$SAMPLE.for_qual_histogram.txt
                docker exec -w /the_data $PATHOGENIMAGE rm qa.$SAMPLE.length_count.txt
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.base.matrix
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.quality.matrix
                docker exec -w /the_data $PATHOGENIMAGE rm qa.$SAMPLE.base.matrix
                docker exec -w /the_data $PATHOGENIMAGE rm qa.$SAMPLE.quality.matrix
                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.unpaired.trimmed.fastq
                docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.fastp.log gs://test-154312-data-bucket/$SAMPLE.fastp.log
                docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.1.trimmed.fastq gs://test-154312-data-bucket/$SAMPLE.1.trimmed.fastq
                docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.2.trimmed.fastq gs://test-154312-data-bucket/$SAMPLE.2.trimmed.fastq
                # if FaQCs ran
                if [ -f /home/tleppert/the_data/${SAMPLE}.1.trimmed.fastq ]; then
                        touch /home/tleppert/running.bwa
			docker exec -w /the_data $PATHOGENIMAGE sh -c "bwa mem -t 2 reference/bwa/reference $SAMPLE.1.trimmed.fastq $SAMPLE.2.trimmed.fastq | samtools sort --threads 2 -o /the_data/$SAMPLE.bam"
			# cleanup from FaQCs
                        docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_1.paired.fastq
                        docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_2.paired.fastq
                        docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bam gs://test-154312-data-bucket/${SAMPLE}.early.bam
                        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                        # if bwa ran
                        if [ -f /home/tleppert/the_data/$SAMPLE.bam ]; then
                                touch /home/tleppert/running.MarkDuplicates
				docker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar MarkDuplicates REMOVE_DUPLICATES=true ASSUME_SORT_ORDER=coordinate VALIDATION_STRINGENCY=LENIENT I=$SAMPLE.bam O=${SAMPLE}_markdups.bam M=${SAMPLE}_markdups.MarkDuplicates.metrics.txt
                                # cleanup from bwa
                                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.1.trimmed.fastq
                                docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.2.trimmed.fastq
                                docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                # if MarkDuplicates ran
                                if [ -f /home/tleppert/the_data/${SAMPLE}_markdups.bam ]; then
                                        touch /home/tleppert/running.CleanSam
                                        docker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar CleanSam -I ${SAMPLE}_markdups.bam -O ${SAMPLE}_clean.bam
                                        # cleanup from MarkDuplicates
                                        docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.bam
                                        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                        # if CleanSam ran
					if [ -f /home/tleppert/the_data/${SAMPLE}_clean.bam ]; then
                                                touch /home/tleppert/running.FixMateInformation
						docker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar FixMateInformation -I ${SAMPLE}_clean.bam -O ${SAMPLE}_fixmate.bam --VALIDATION_STRINGENCY LENIENT
                                                # cleanup from CleanSam
                                                docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_markdups.bam
                                                docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_markdups.MarkDuplicates.metrics.txt
                                                docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                                # if FixMateInformation ran
                                                if [ -f /home/tleppert/the_data/${SAMPLE}_fixmate.bam ]; then
                                                        touch /home/tleppert/running.AddOrReplaceReadGroups
							docker exec -w /the_data $PATHOGENIMAGE java -jar /bin/picard.jar AddOrReplaceReadGroups --INPUT ${SAMPLE}_fixmate.bam --OUTPUT $SAMPLE.bam -ID id -LB library -PL illumina -PU barcode -SM $SAMPLE -CREATE_INDEX true
							# cleanup from FixMateInformation
                                                        docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_clean.bam
                                                        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                                        docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bam gs://test-154312-data-bucket/$SAMPLE.bam
                                                        docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.bai gs://test-154312-data-bucket/$SAMPLE.bai
                                                        # if AddOrReplaceReadGroups ran
							if [ -f /home/tleppert/the_data/$SAMPLE.bam ]; then
                                                                touch /home/tleppert/running.gatk
								docker exec -w /the_data $PATHOGENIMAGE /home/user/gatk-4.6.1.0/gatk --java-options "-Xms6G -Xmx6G" HaplotypeCaller -R reference/reference.fasta -I $SAMPLE.bam -O $SAMPLE.g.vcf.gz -ERC GVCF --sample-ploidy "1"
       		     		    	    	                # cleanup AddOrReplaceReadGroups
                                                                docker exec -w /the_data $PATHOGENIMAGE rm ${SAMPLE}_fixmate.bam
                                                                docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                                                # if gatk ran
                                                                if [ -f /home/tleppert/the_data/$SAMPLE.g.vcf.gz ]; then
                                                                        touch /home/tleppert/running.vcf_to_maple
									docker exec -w /the_data $PATHOGENIMAGE /usr/bin/python3 /bin/gvcf_to_maple_haploid.py -i /the_data/$SAMPLE.g.vcf.gz -DP 20 -GQ 99 -o AND
                                                                        # cleanup from gatk
                                                                        docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.bam
                                                                        docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.bai
                                                                        docker exec -w /the_data $PATHOGENIMAGE rm $SAMPLE.g.vcf.gz.tbi
                                                                        docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
                                                                        # if vcf_to_maple ran
                                                                        if [ -f /home/tleppert/the_data/$SAMPLE.maple ]; then
                                                                                # move files back to data-bucket
                                                                                touch /home/tleppert/the_data/$SAMPLE.done
										docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.maple gs://test-154312-data-bucket/$SAMPLE.maple
										docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.g.vcf.gz gs://test-154312-data-bucket/$SAMPLE.g.vcf.gz
										docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.done gs://test-154312-data-bucket/$SAMPLE.done
									fi # if [ -f $SAMPLE.maple ]; then
								fi # if [ -f $SAMPLE.g.vcf.gz ]; then
                                                        fi # if [ -f $SAMPLE.bam ]; then
                                                fi # if [ -f $SAMPLE_fixmate.bam ]; then
                                        fi # if [ -f $SAMPLE_clean.bam ]; then
                                fi # if [ -f $SAMPLE_markdups.bam ]; then
                        fi # if [ -f $SAMPLE.bam ]; then
                fi # if [ -f $SAMPLE.1.trimmed.fastq ]; then
        fi # if [ -f $SAMPLE_1.paired.fastq ]; then
fi # if [ -f $SAMPLE_1.fastq ]; then
docker exec -w /the_data $PATHOGENIMAGE fix-id.sh
touch /home/tleppert/the_data/$SAMPLE.finished
docker exec $GOOGLEIMAGE gsutil cp /the_data/$SAMPLE.finished gs://test-154312-data-bucket/$SAMPLE.finished
# gcloud compute instances stop vm, avoid extra charges
sudo shutdown now

[Link to Section 2 in document2.md](/document2.md#section-2)
[Link to Section 2 in document2.md](/document2.md#section-2)
Note:
turning on a shutdown vm, restarts the processing of the invoking script from the beginning.
This is fine if you are not too far along the process.
If you've spent a fair amount of resources calculating, then it's better to remove the vm
and requeue using another script that copies the intermediate saved files from the bucket
back to the newly created vm.  NOTE: the newly created vm will have the same name, so you
will need to remove the old vm first.  or name the new vm with -a or something. There are
scripts that can help you. mycosnp-bucket-clean.py makes a cleanup-mycosnp-vm.script that
executes reset.script which cleans the buckets and creates new run scripts with data from
the bucket that is complete but not the final files for the process.
