#!/bin/bash
#echo "Enter BioSample accession (SAME/SAMN/SAMD): "
YOUR_ACCESSION_HERE=$1
echo "Processing SAMN type identifier"

# if starting with BioSample accession (SAME/SAMN/SAMD)
SRRS_STR=$(timeout -v 10m esearch -db sra -query $YOUR_ACCESSION_HERE | \
			esummary | xtract -pattern DocumentSummary -element Run@acc)
read -ra SRRS_ARRAY -d ' ' <<<"$SRRS_STR"
for SRR in "${SRRS_ARRAY[@]}"
do
timeout -v 10m prefetch --max-size 20000000 "$SRR"
timeout -v 20m fasterq-dump "$SRR"
chmod 666 $SRR/$SRR.sra
done
