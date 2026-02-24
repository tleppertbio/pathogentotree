#  Execute reset.script
Invoked from cleanup-mycosnp-vm.script.
Cleans up bucket and vms, pulls intermediate and final data from bucket and reqeues failed runs.

After running a docker images of tleppertwood/pathogentotree process on a google vms, look at the bucket and vm queues.
Find sra sample data from nih that has been analyzed and download it to a local directory, or requeue partially finished data.
Finished sample data analysis has been compared to reference sequence and has returned comparison edits in the form of .g.vcf.gz and .maple files.
Partially analyzed sample data can be re-queued to complete comparison to reference sequence.
See [Docker container pathogentotree](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md) the docker container that performs the comparisons.

---

## What will you need

1) [collect metadata](https://github.com/tleppertbio/pathogentotree/metadata.README.md), to determine if you have the correct samples and the size of the sample file.
2) [sra_now.list](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#create-sranowlist-file), a file containing the size of the sample file and the sra number, tab separated.
3) [google buckets](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#how-to-create-a-bucket-identify-your-google-region-and-viewing-pricing-tablessizes-for-vms), creating a bucket to house your output data until you can retrieve it to your local machine.
4) [reference data](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#create-and-execute-refbucketsetupscript-file), reference files prepped for analysis using nucmer, bedtools maskfasta, samtools faidx, picard.jar and bwa, which reside in the google bucket and vms during analysis.
5) [directory structure](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#directory-structure-on-your-local-machine), the directory structure that is created on your local machine, pathogentotree's expected structure.
6) After this program, loop the process by creating more analysis scripts using [make_mycosnp_script.py](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#running-makemycosnpscriptpy) invoking with [scripts](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#running-invokemycosnpscriptpy) and [invoke](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#execute-scripts-to-invoke-docker-image-on-google-vms) pulling finished data [vm bucket management](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#running-mycosnpbucketcleanpy) and [cleanup](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md#execute-cleanupmycosnpvmscript-to-clean-and-sort-data-and-pull-data-from-bucket).
7) [complete pathogentotree package](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md) full documentation to the entire process, setting up google cloud vms to run pathogentotree docker container to analyze nih sra datasets to find reference compared sequence edits.

### reset.script

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
  [example bucket.list file](https://github.com/tleppertbio/pathogentotree/bucket.list.example)

  Here is an example of a compute_instances.list file that is created by this reset.script.
  [example compute_instances.list file](https://github.com/tleppertbio/pathogentotree/compute_instances.list.example)

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
