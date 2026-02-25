# Protocol to create necessary reference files for docker image pathogentotree analysis

 Copy from another directory the reference.fa file and make a copy by naming it so (reference.copy.fa):
 - cp /from another directory/reference.fa .
 - cp reference.fa reference.copy.fa

 Run the nucmer program:
 - nucmer -p reference --coords --maxmatch --nosimplify reference.fa reference.copy.fa

 Run the show-coords program, then modify the result to look like masked_ref.bed:
 - show-coords -r -T -H reference.delta > masked_ref_BEFORE_ORDER.bed
 - awk '{if ($1 != $3 && $2 != $4) print $0}' masked_ref_BEFORE_ORDER.bed > masked_ref_BEFORE_ORDER2.bed
 - awk '{print $8"\t"$1"\t"$2}' masked_ref_BEFORE_ORDER2.bed > masked_ref.bed

 Run the bedtools maskfasta:
 - bedtools maskfasta -fi reference.fa -bed masked_ref.bed -fo reference.fasta

 Run the samtools faidx:
 - samtools faidx reference.fasta

 Run the picard.jar v 2.26.10 CreateSequenceDictionary
 - java -jar /home/tami/bin/picard.jar CreateSequenceDictionary R=reference.fasta O=reference.dict

 Create a ./bwa directory and run the bwa index program:
 - mkdir bwa
 - bwa index -p bwa/reference reference.fasta

 Files created for use in mycosnp/docker process:
 Copy them to the bucket using the script ref-bucket-setup.script
 
 gsutil cp /path/to/files/bwa/reference.amb gs://NameOfBucket/reference/bwa/<br/>
 gsutil cp /path/to/files/bwa/reference.ann gs://NameOfBucket/reference/bwa/<br/>
 gsutil cp /path/to/files/bwa/reference.bwt gs://NameOfBucket/reference/bwa/<br/>
 gsutil cp /path/to/files/bwa/reference.pac gs://NameOfBucket/reference/bwa/<br/>
 gsutil cp /path/to/files/bwa/reference.sa gs://NameOfBucket/reference/bwa/<br/>
 gsutil cp /path/to/files/reference.cluster gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.coords gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.delta gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.dict gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.fa gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.fasta gs://NameOfBucket/reference<br/>
 gsutil cp /path/to/files/reference.fasta.fai gs://NameOfBucket/reference<br/>
 

For users in the UCSC lab, perform the first 11 operations (including bwa index) on silverbullet
