# Partial Scripts                                                                                                            
  Invoked if a sample has been partially run and a complete intermediate file has been generated.                              
  The intermediate file (residing in the bucket), can be pulled into a new vm and the processing can be started from the point after the generation of that (or those) file(s).
  The partial scripts are contained in the ./partials folder.<br/>
  
  The script for [earlybam-pickup-startup.script](./partials/earlybam-pickup-startup.script)<br/>
  - is copied by the reset.script (invoked by cleanup-mycosnp-vm.script)
  - the sample id is modified to be the current sample
  - the script is placed in the vm-scripts folder
  - an execute-SRR#-DATE.script is created to invoke the vm to run.<br/>
  
  The script for [finalbam-pickup-startup.script](./partials/finalbam-pickup-startup.script)<br/>
  - is copied by the reset.script (invoked by cleanup-mycosnp-vm.script)
  - the sample id is modified to be the current sample
  - the script is placed in the vm-scripts folder
  - an execute-SRR#-DATE.script is created to invoke the vm to run.<br/>
  
  The script for [trimmed-pickup-startup.script](./partials/trimmed-pickup-startup.script)<br/>
  - is copied by the reset.script (invoked by cleanup-mycosnp-vm.script)
  - the sample id is modified to be the current sample
  - the script is placed in the vm-scripts folder
  - an execute-SRR#-DATE.script is created to invoke the vm to run.<br/>
  

  **What do these do?**
  
  reset.script is run from cleanup-mycosnp-vm.script, reset.script executes in six ways, two can be requeued runs.<br/>
  Requeues a vm using an .early.bam file from the bucket.<br/>
  Requeues a vm using a .1.trimmed.fastq and .2.trimmed.fastq from the bucket.<br/>
  Requeues a vm using a .bam and .bai from the bucket.<br/>

  The mycosnp-bucket-clean.example, shows the list of files in the bucket that are required for requeuing.
  [mycosnp-bucket-clean.example file](./mycosnp-bucket-clean.example)

  **How to run it?**
  
  reset.script is run when ./cleanup-mycosnp-vm.script is invoked.<br/>
  reset.script automatically pulls the partial run scripts from ./partials, adjusts the scripts for the current sample and places the updated script in the vm-scripts folder.<br/>
  The user will need to invoke the execute file in the vm-scripts folder that was created by the ./cleanup-mycosnp-vm.script execution.<br/>

  **Things to know**
  
  - reset.script finalbam - requeues partially run samples with .bam and .bai files.
  - reset.script trimmed - requeues partially run samples with .1.trimmed.fastq and .2.trimmed.fastq files.
  - reset.script earlybam - requeues partially run samples with the .early.bam file.

  The script for [earlybam-pickup-startup.script](./partials/earlybam-pickup-startup.script)
  The script for [finalbam-pickup-startup.script](./partials/finalbam-pickup-startup.script)
  The script for [trimmed-pickup-startup.script](./partials/trimmed-pickup-startup.script]
