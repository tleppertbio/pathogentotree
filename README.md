# pathogentotree
Loads a list of sra files from ncbi, compares the files to a reference sequence using google vms running docker image tleppertwood/pathogentotree:latest running a mycosnp environment, and creates a folder with .g.vcf.gz and .maple files, which contain the edit differences for each sra sample.
