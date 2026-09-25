#!/bin/bash
##echo "Enter SRA accession (SRR/ERR/DRR): "
YOUR_ACCESSION_HERE=$1
echo "Processing SRR type identifier"

# if starting with SRA accession (SRR/ERR/DRR)
# max-size is in KB, so 20000000 is 20 GB
timeout -v 10m prefetch --max-size 20000000 $YOUR_ACCESSION_HERE
timeout -v 10m fasterq-dump -vvv -x $YOUR_ACCESSION_HERE
chmod 666 $YOUR_ACCESSION_HERE/$YOUR_ACCESSION_HERE.sra
