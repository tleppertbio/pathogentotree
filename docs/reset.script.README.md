#  Execute reset.script
Invoked from cleanup-mycosnp-vm.script.
Cleans up bucket and vms, pulls intermediate and final data from bucket and reqeues failed runs.

After running a docker images of tleppertwood/pathogentotree process on a google vms, look at the bucket and vm queues.
Find sra sample data from nih that has been analyzed and download it to a local directory, or requeue partially finished data.
Finished sample data analysis has been compared to reference sequence and has returned comparison edits in the form of .g.vcf.gz and .maple files.
Partially analyzed sample data can be re-queued to complete comparison to reference sequence.

---

## What will you need

1) collect metadata
2) sra_now.list, a file containing the size of the sample file and the sra number, tab separated.
3) google bucket, creating a bucket to house your output data until you can retrieve it to your local machine.
4) reference data, reference files prepped for analysis using nucmer, bedtools maskfasta, samtools faidx, picard.jar and bwa, which reside in the google bucket and vms during analysis.
5) The directory structure that is created on your local machine, pathogentotree's expected structure.

### reset.script

  **What does this do?**
  
  reset.script is run from cleanup-mycosnp-vm.script, reset.script executes in six ways.<br/>
  Requeues a vm using an earlybam file from the bucket, requeues a vm using a .bam and .bai file from the bucket.<br/>
  Requeues a vm using a .1.trimmed.fastq and .2.trimmed.fastq from the bucket.<br/>
  Continues queuing the second half of a process vm2's if the first have of a large run is finished.<br/>
  Pulls files from the bucket to a local ./maple directory and cleans up old files and vms.<br/>
  Flags when a run has failed completely and needs to be requeued by the user.<br/>
  Pulls a list of vms to a file compute_instances.list from the google cloud to check on the status as well as finding the zone.<br/>
  The file compute_instances.list is used for determining which vms to remove and how define the components of the remove command.<br/>

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

