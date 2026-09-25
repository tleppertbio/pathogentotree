# tleppertbio/pathogentotree

Automated pipeline to download *Candida* / *Candidozyma auris* sequencing
data from NCBI, call variants from reference, mask problematic regions, and build/optimize
a parsimony phylogenetic tree (UShER / matOptimize) with metadata on Google Cloud.

> **Status:** under active development. See [Known issues](#known-issues)
> before running this on a new project.

## Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Quick start](#quick-start)
- [Repository layout](#repository-layout)
- [How it works](#how-it-works)
- [Running on your own GCP project](#running-on-your-own-gcp-project)
- [Reference genome](#reference-genome)
- [Known issues](#known-issues)

## Prerequisites

- **Conda/Mamba** — [Miniforge](https://github.com/conda-forge/miniforge) is
  the simplest way to get `conda-forge` + `bioconda` set up.
- **Docker** — for building/pulling the `pathogentotree` image used inside
  cloud VMs.
- **Google Cloud SDK** (`gcloud`, `gsutil`) — authenticated to a project with
  Compute Engine and Cloud Storage enabled, if you intend to run the cloud
  VM stages. 
- A GCP **service account** with `roles/compute.instanceAdmin` and
  `roles/storage.objectAdmin` on the bucket you'll use.
- A brew installation to install the following:
- A brew nucmer (MUMmer) installation to process the reference file.
- A brew bedtools installation to process the reference file.
- A brew show-coords bioconda installation to process the reference file.
- A java installation to process the reference file.
- picard.jar from pathogentotree installation
- A brew bwa installation to process the reference file.
- An Entrez Direct installation to download SRA data from ncbi.
- A conda ncbi_datasets installation to download SRA data from ncbi.

- Using pathogentotree/bin/pre-check.script to install/test if you have everything.

- A reference sequence number e.g. GCA_003013715.2

macOS and Linux are both supported. Windows is untested; WSL2 should work
but is not covered here.

## Setup

```bash
git clone https://github.com/tleppertbio/pathogentotree.git
cd pathogentotree

conda env create -f environment.yml
conda activate pathogentotree

# Every or One-time: authenticate gcloud, if using the cloud stages
# This may need to be re-run occasionally - watch for gs errors
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>

may wish to use ./bin/pre-check.script  # Can check if setup for running this package has been done properly
```

## Quick start

```bash
./bin/sra-setup.script \
  --project <YOUR_PROJECT_ID> \
  --bucket  <YOUR_BUCKET> \
  --region  <YOUR_REGION> \
  --service <YOUR_SERVICE_ACCOUNT_EMAIL>
```

In your running directory the scripts will create eleven directories ./allchrom ./disqualified_maples ./log
./maple ./mask_chrom ./mask_parsimony_allchrom ./metadata ./split_chrom ./tree, ./vm-scripts and ./vm-running.
The vm-running folder will have sub folders for the difference size categories of the sra sample data you have.
A set of master-vm-YEAR-MO-DAY-HOUR_MINUTE.log files will appear as the master_vm moves through the samples.
A calculated_ratios.dat file and tabulated_bases_from_maple.dat file will be created at the end of the process
to inform you of the contents of your sample files.  A disqualified_n.list file will list those samples that
did not pass the qc threshold for tree building.  A sra_now.list is a list of all samples that will be run.

Downloading the metadata may take several hours, running the vms may take a week, depending on how many samples
you will analyze.  Samples are queued into the vm on weekdays after 5:30 and on weekends in the mornings and
again in the afternoon.  Sometimes the vm's are not available, there will be error messages about unavailability.
The algorithm will recover these samples and requeue them in a later time slot.  Monitoring the queue and bucket
is an on-going process and occurs roughly every half hour.  There are periods where programs will sleep for a few
minutes to allow for gc vms to start.  You will receive notices when the process is sleeping.

## Repository layout

```
pathogentotree/
├── bin/                  # pipeline scripts (entry point: sra-setup.script)
│   ├── sra-setup.script  ← entry point
│   ├──   picard.jar                # used by sra-setup.script to create reference files
│   ├──   Entrez_batch_fetch_sra.sh # used by sra-setup.script to fetch sra data
│   ├──   parse_entrez.py           # used by sra-setup.script to parse metadata downloads
│   ├──   parse_sra_xml.py          # used by sra-setup.script to parse metadata xml
│   ├──   build_metadata.script     # used by sra-setup.script to organize metadata
│   ├──   make_mycosnp_script.py    # used by sra-setup.script to make processing scripts for each sample
│   ├──   master_vm.script          # script controlling and processing samples through gvms, used by sra-setup.script
│   ├──     mycosnp-bucket-clean.py          # used by master_vm.script monitor and clean vm and bucket
│   ├──       reset.script                       # used by mycosnp-bucket-clean.py requeue partial runs/ cleanup
│   ├──     invoke_mycosnp_script.py         # used by master_vm.script writes the vm queuing scripts
│   ├──     invoke_vm.script                 # used by master_vm.script invoke the vm queuing scripts
│   ├──     count_maple_guts.py              # used by master_vm.script after vms are finished count maple info
│   ├──     calc_coverage.py                 # used by master_vm.script after vms are finished calculate sample coverage
│   ├──     disqualified_maples.script       # used by master_vm.script after vms are finished disqualify samples
│   ├──     split_maples_by_chrom.script     # used by master_vm.script after vms are finished split maples into chromosome
│   ├──     mask_controller.script           # used by master_vm.script after vms are finished mask by chromosome
│   ├──       mask_maple.py                      # used by mask_controller.script and mask_parsimony_controller.script to perfom actual masking
│   ├──     paste_maples.py                  # used by master_vm.script after vms are finished paste split maples together
│   ├──     mask_parsimony_controller.script # used by master_vm.script after vms are finished mask by parsimony scores
│   ├──     maples_parsimony_packs.script    # used by master_vm.script after vms are finished package maples together for tree building
│   ├──   make_matOpt_script.py     # used by sra-setup.script to optimize phylogenetic tree
│   └──   pre-check.script  # Can be used by user to check if setup for running this package has been done properly
finish-project-clean.script # used by sra-setup.script and master_vm.script to clean up bucket and vm instances.
│   └── partials/         # generated-script templates (startup scripts, etc.)
│         ├── earlybam-pickup-startup.script # scripts used by reset.script to pick up and finish partially run samples
│         ├── finalbam-pickup-startup.script # scripts used by reset.script to pick up and finish partially run samples
│         └── trimmed-pickup-startup.script  # scripts used by reset.script to pick up and finish partially run samples
├── mask_files/           # tandem-repeat & parsimony mask BED files
│   ├──  fasTAN_1.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_2.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_3.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_4.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_5.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_6.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_7.bed     # chromosome 1 bed file reference analysis masking
│   ├──  fasTAN_all.bed   # all chromosome bed file reference analysis masking
│   ├──  fasTAN.bed       # all chromosome bed file reference analysis masking
│   ├──  fasTAN.bed.orig  # all chromosome bed file reference analysis masking
│   ├──  genome_size.tsv  # genome size file
│   ├──  parsimony_mask_pad500_merged.bed   # parsimony mask file +- 500 score, not used
│   ├──  parsimony_mask.bed     # parsimony mask bed file anything with parsimony score > 1000 is removed
│   ├──  parsimony_mask.script  # parsimony mask create file anything with parsimony score > 1000 is removed
│   └──  parsimony_per_site.tsv	# parsimony mask file anything with parsimony score > 1000 is removed				 
├── reference/            # reference genome build + provenance files CP043531.1-CP043537.1
│   ├── masked_ref_BEFORE_ORDER.bed  
│   ├── masked_ref_BEFORE_ORDER2.bed 
│   ├── masked_ref.bed               
│   ├── reference.cluster            
│   ├── reference.coords             
│   ├── reference.copy.fa            
│   ├── reference.delta              
│   ├── reference.dict               
│   ├── reference.fa                 
│   ├── reference.fa.fai
│   ├── reference.fasta
│   ├── reference.fasta.fai
│   ├── reference.howto
│   └── bwa/  
│         ├── reference.amb
│         ├── reference.ann
│         ├── reference.bwt
│         ├── reference.pac
│         └── reference.sa
├── docker/               # Dockerfile + NCBI pull scripts + mycosnp processing scripts for the pipeline image
│   ├── bwa               # For processing of sample files
│   ├── FaQCs             # For processing of sample files
│   ├── execute-pull.sh   # For pulling sra data
│   ├── fasterq-dump-orig.3.2.1  # for pulling sra data
│   ├── fix-docker-id.sh  # For fixing ids
│   ├── fix-id.sh         # For fixing ids
│   ├── gatk              # For processing of sample files
│   ├── gatk-4.6.1.0      # For processing of sample files
│   ├── gatk-package-4.6.1.0-local.jar  # For processing of sample files
│   ├── gatk-package-4.6.1.0-spark.jar  # For processing of sample files
│   ├── gvcf_to_maple_haploid.py  # For creating gvcf from .maple files
│   ├── picard.jar        # For processing of sample files
│   ├── prefetch-orig.3.2.1   # For processing of sample files
│   ├── python3.12        # For processing of sample files
│   ├── samn-pull.sh      # For pulling sra data
│   ├── seqkit            # For processing of sample files
│   └── srr-pull.sh       # For pulling sra data
├── environment.yml
└── docs/
     ├── documentation.dat                # Full documentation
     ├── mycosnp-based-workflow.png       # Diagram of mycosnp workflow
     ├── mycosnp.sample.script            # Example of mycosnp script
     ├── execute-vm-large-2026-01-29.15.48.script    # Example of execute mycosnp script
     ├── bucket.list.example              # Example of bucket.list
     ├── mycosnp-bucket-clean.example
     ├── cleanup-mycosnp-vm.script.example
     ├── compute_instances.list.example
     └── reset.script
     
```

## How it works

     1. sra-setup.script — fetch NCBI metadata, filter candidate samples
     2. master_vm.script  
         2A. per-sample VM: download SRA → align → call variants → .maple
	 2B. per-sample VM: push results to bucket
	 2C. monitor VM and bucket, requeue partial runs, save finished results
         2D. when all samples are finished VM. Then mask, QC samples.
     3. sra-setup.script build tree (usher-sampled) and optimize (matOptimize)

## Running on your own GCP project

By default, VM scripts pull the pipeline image from:

```
ghcr.io/tleppertbio/pathogentotree:1.0.0
```
To avoid repeated cross-region pulls when running many VMs, mirror the
image into your own project once:

```bash
gcloud auth configure-docker <YOUR_REGION>-docker.pkg.dev
docker pull ghcr.io/tleppertbio/pathogentotree:<VERSION>
docker tag ghcr.io/tleppertbio/pathogentotree:<VERSION> \
  <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/pathogen-repo/pathogentotree:<VERSION>
docker push <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/pathogen-repo/pathogentotree:<VERSION>
```

Then pass `--image <YOUR_REGION>-docker.pkg.dev/<YOUR_PROJECT_ID>/...` to
`sra-setup.script`.

## Reference genome

How this routine processes a new reference file:
1) cp ../reference.fa .
2) cp reference.fa reference.copy.fa
3) nucmer -p reference --coords --maxmatch --nosimplify reference.fa reference.copy.fa
4) show-coords -r -T -H reference.delta > masked_ref_BEFORE_ORDER.bed
5) awk '{if ($1 != $3 && $2 != $4) print $0}' masked_ref_BEFORE_ORDER.bed > masked_ref_BEFORE_ORDER2.bed
6) awk '{print $8"\t"$1"\t"$2}' masked_ref_BEFORE_ORDER2.bed > masked_ref.bed
7) bedtools maskfasta -fi reference.fa -bed masked_ref.bed -fo reference.fasta
8) samtools faidx reference.fasta
9) java -jar /home/tami/bin/picard.jar CreateSequenceDictionary R=reference.fasta O=reference.dict
10) mkdir bwa
11) bwa index -p bwa/reference reference.fasta

Note: step 5) Claude points out that this step actually does not mask reference.
              Someone needs to confirm it actually finds off-diagonal repeat hits before trusting it.

## Known issues

Tracking in [issues](../../issues). Highlights as of this writing:
