#!/bin/bash

echo "Enter the SRR or the SAMN id# to pull from ncbi:"
inputValue=$1

substrSRR='SRR'
substrSAMN='SAMN'

cd /
directory="the_data"
if [ -d "$directory" ]; then
    cd the_data
    if [[ $inputValue =~ $substrSRR ]]; then
        echo "You entered SRR type value"
        /bin/srr-pull.sh $inputValue
        /bin/fix-id.sh
    elif [[ $inputValue =~ $substrSAMN ]]; then
        echo "You entered SAMN type value"
        /bin/samn-pull.sh $inputValue
        /bin/fix-id.sh        
    else         
        echo "You entered: '${inputValue}' This is not a valid id."
    fi
else
    echo "You must create a folder called \'the_data\' in the current directory"
fi
