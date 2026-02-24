In order to run the tutorial...
You have to create a new directory (or reload an existing directory) using the get_started.script.

Read [pathogentotree.README.md](https://github.com/tleppertbio/pathogentotree/pathogentotree.README.md) for information on
- You will need a google project id (enable billing for your Cloud project)
- You will need a google bucket
- You will need to know the google region that you want to use

In another window, run the following commands

./get_started.script    <- downloads all repos from github, initializes scripts using project_id, bucket, google region
./tutorial-setup.script   <- initializes sra_now.list, ref-bucket-setup.script
./ref-bucket-setup.script    <- put reference files in your bucket
python3 ./make_mycosnp_script.py    <- create vm scripts
python3 ./invoke_mycosnp_script.py  <- create invoke scripts
cd vm-scripts
./execute-vm-size-date-time.script  <- invoke the vms
cd ../

wait 30 minutes or until the .finished and .done files appear (you may look at the bucket and the running vm)
 - To look at the bucket: https://console.cloud.google.com/storage/browser/YOURBUCKETNAME
 - To look at the vm list: https://console.cloud.google.com/compute/instances?project=YOURPROJECTNAME

python3 ./mycosnp-bucket-clean.py  <- look in the bucket create the cleanup-mycosnp-vm.script
./cleanup-mycosnp-vm.script     <- execute the cleanup-mycosnp-vm.script
./finish-project-clean.script   <- cleanup this tutorial/runs when finished with the project

