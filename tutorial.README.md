In order to run the tutorial...
You have to create a new directory (or reload an existing directory) using the get_started.script.

Read [pathogentotree.README.md](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md) for information on
- You will need a google project id (enable billing for your Cloud project)
- You will need a google bucket
- You will need to know the google region that you want to use

In another window, run the following commands

- git clone https://github.com/tleppertbio/pathogentotree &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#clone the pathogentotree repository
- cd pathogentotree&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#switch to the pathogentotree folder
- chmod 775 ./get_started.script&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#make the get_started.script executable
- ./get_started.script&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#downloads all repos from github, initializes scripts using project_id, bucket, google region
- ./tutorial-setup.script&nbsp;&nbsp;&nbsp;#initializes sra_now.list, ref-bucket-setup.script
- ./ref-bucket-setup.script&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#put reference files in your bucket
- python3 ./invoke_mycosnp_script.py&nbsp;&nbsp;#create invoke scripts
- cd vm-scripts&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#change to the vm-scripts folder
- ./execute-vm-size-date-time.script&nbsp;&nbsp;#invoke the vms
- cd ../&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#go back to the original folder

- wait 30 minutes or until the .finished and .done files appear (you may look at the bucket and the running vm)
    - To look at the bucket: https://console.cloud.google.com/storage/browser/YOURBUCKETNAME
    - To look at the vm list: https://console.cloud.google.com/compute/instances?project=YOURPROJECTNAME

- python3 ./mycosnp-bucket-clean.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#look in the bucket create the cleanup-mycosnp-vm.script
- ./cleanup-mycosnp-vm.script&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#execute the cleanup-mycosnp-vm.script
- ./finish-project-clean.script&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;#cleanup this tutorial/runs when finished with the project

