# Collection of metadata

**What is the purpose of this step?**

Collecting and reviewing metadata is a critical initial step prior to running analysis.
It enables you to collect two important pieces of information.

1) Collecting only those samples that are relevant to the reference sequence you have chosen.
2) Knowing the size of each of your samples is critical for choosing how many vm's you can queue.

In this example, we are looking for candida haemuli samples.
To get metadata use two methods. Each method can return very different data depending on the organism.

  1) https://www.ncbi.nlm.nih.gov/sra/?term=candida+haemuli
          select 'Send to:' pulldown in upper right under the sra search bar
          select the File option button
          select Format pulldown option 'Full XML'
          select 'Create File' button
     this will download a file called bioproject_result.xml

     If the .xml is very large use this script.
     ./split_to_lines.script
     
     ./find_all_full_meta.awk # creates Accession.out, Alias_Isolate.out, BioProject.out, Biosample.out, Collection_Date.out, Experiment_Accession.out, Geo_Locate.out, Isolation.out, Lab_Name.out, Library_Layout.out, Library_Source.out, Library_Strategy.out, Platform.out, Primary_ID.out, Sample_Descriptor_Accession.out, SampleType.out, Scientifc_Name.out, Size.out, Strain.out, Study_Ref_Accession.out, TaxonID.out


  2) bigquery https://www.ncbi.nlm.nih.gov/sra/docs/sra-bigquery-examples/
     - You will need to create your own google console cloud bigquery location.
     - You will need an active Google Cloud account with an active project.
     - Make sure you have IAM permissions such as bigquery.datasets.create permission.               
     - Go to the BigQuery page in the google cloud console.
     - In the Explorer pane on the left, select the project where you want to create the dataset.
     - Click the View actions (three vertical dots) icon next to your project ID and select Create dataset.
     - On the Create dataset page:
        - For Dataset ID, enter a unique name for your dataset. This name must contain only letters, numbers, or underscores.
        - For Location type, choose a geographic location for the dataset. Note that this location cannot be changed after the dataset is created.
        - Configure any additional options if needed (e.g., default table expiration, description, or encryption settings).
        - Click Create dataset.
	
     generate an sql query such as one of these:
     - SELECT distinct(tax_id) from `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis` WHERE name like "%andid%aemuli%"
     - SELECT * FROM `nih-sra-datastore.sra.metadata` as m JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis` as tax ON m.acc = tax.acc WHERE tax.tax_id = 45357 
     - SELECT * FROM `nih-sra-datastore.sra.metadata` as m JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis_info` as info ON m.acc = info.acc JOIN `nih-sra-datastore.sra_tax_analysis_tool.tax_analysis` as tax on m.acc = tax.acc WHERE tax.tax_id = 45357 and m.librarylayout = "PAIRED"
     - SELECT * FROM `nih-sra-datastore.sra.metadata` WHERE organism = 'Candidozyma haemuli' OR sample_name LIKE '%andid%haemuli%' OR organism LIKE '%andid%haemuli%'
	
     save the results of your query to a file on your computer.

