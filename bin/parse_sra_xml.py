#!/usr/bin/env python3
"""
SRA Experiment Package XML → TSV parser
Usage: python parse_sra_xml.py <input.xml> [output.tsv]
"""
# Program parse_sra_xml.py is called from sra-setup.script, translating xml to tsv
# Code written by claude to parse candida_metadata.xml creating candida_metadata.tsv
# Note, if ncbi format changes then this code will have to change as well...
import sys
import csv
from xml.etree import ElementTree as ET

def get_text(element, path, default=""):
    """Safely extract text from an element via XPath."""
    node = element.find(path)
    return (node.text or "").strip() if node is not None else default

def get_attr(element, path, attr, default=""):
    """Safely extract an attribute from an element via XPath."""
    node = element.find(path) if path else element
    return (node.get(attr) or "").strip() if node is not None else default

def get_sample_attributes(sample_el):
    """Return dict of all SAMPLE_ATTRIBUTE TAG→VALUE pairs."""
    attrs = {}
    if sample_el is None:
        return attrs
    for sa in sample_el.findall(".//SAMPLE_ATTRIBUTE"):
        tag = get_text(sa, "TAG")
        val = get_text(sa, "VALUE")
        if tag:
            attrs[tag] = val
    return attrs

def parse_experiment_package(pkg):
    """Extract flat fields from one EXPERIMENT_PACKAGE element."""
    row = {}

    # --- EXPERIMENT ---
    exp = pkg.find("EXPERIMENT")
    row["experiment_accession"] = get_attr(exp, None, "accession") if exp is not None else ""
    row["experiment_alias"]     = get_attr(exp, None, "alias")     if exp is not None else ""
    row["center_name"]          = get_attr(exp, None, "center_name") if exp is not None else ""
    row["experiment_title"]     = get_text(exp, "TITLE") if exp is not None else ""

    # Platform / instrument
    if exp is not None:
        plat_el = exp.find("PLATFORM")
        if plat_el is not None:
            plat_child = list(plat_el)
            row["platform"] = plat_child[0].tag if plat_child else ""
            row["instrument_model"] = get_text(plat_child[0], "INSTRUMENT_MODEL") if plat_child else ""
        else:
            row["platform"] = row["instrument_model"] = ""

        # Library
        lib = exp.find(".//LIBRARY_DESCRIPTOR")
        row["library_name"]      = get_text(lib, "LIBRARY_NAME")      if lib is not None else ""
        row["library_strategy"]  = get_text(lib, "LIBRARY_STRATEGY")  if lib is not None else ""
        row["library_source"]    = get_text(lib, "LIBRARY_SOURCE")     if lib is not None else ""
        row["library_selection"] = get_text(lib, "LIBRARY_SELECTION")  if lib is not None else ""
        layout_el = lib.find("LIBRARY_LAYOUT") if lib is not None else None
        if layout_el is not None:
            children = list(layout_el)
            row["library_layout"] = children[0].tag if children else ""
        else:
            row["library_layout"] = ""
    else:
        for k in ("platform","instrument_model","library_name","library_strategy",
                  "library_source","library_selection","library_layout"):
            row[k] = ""

    # --- STUDY ---
    study = pkg.find("STUDY")
    row["study_accession"]  = get_attr(study, None, "accession") if study is not None else ""
    row["study_title"]      = get_text(study, ".//STUDY_TITLE")
    row["study_abstract"]   = get_text(study, ".//STUDY_ABSTRACT")
    row["bioproject_id"]    = ""
    if study is not None:
        for ext in study.findall(".//EXTERNAL_ID"):
            if ext.get("namespace") == "BioProject":
                row["bioproject_id"] = (ext.text or "").strip()
                break

    # --- SAMPLE ---
    sample = pkg.find("SAMPLE")
    row["sample_accession"]   = get_attr(sample, None, "accession")       if sample is not None else ""
    row["biosample_id"]       = ""
    row["sample_title"]       = get_text(sample, "TITLE")                 if sample is not None else ""
    row["taxon_id"]           = get_text(sample, ".//TAXON_ID")           if sample is not None else ""
    row["scientific_name"]    = get_text(sample, ".//SCIENTIFIC_NAME")    if sample is not None else ""

    if sample is not None:
        for ext in sample.findall(".//EXTERNAL_ID"):
            if ext.get("namespace") == "BioSample":
                row["biosample_id"] = (ext.text or "").strip()
                break

    # Sample attributes (common fields + catch-all)
    sam_attrs = get_sample_attributes(sample)
    for field in ("collected_by","collection_date","geo_loc_name","host",
                  "host_disease","isolation_source","isolation_type",
                  "lat_lon","host_sex","strain","isolate","BioSampleModel"):
        row[field] = sam_attrs.pop(field, "")
    # Remaining attributes collapsed into one column
    row["other_sample_attrs"] = "; ".join(f"{k}={v}" for k, v in sam_attrs.items())

    # --- RUN (first run in the set) ---
    run = pkg.find(".//RUN_SET/RUN")
    row["run_accession"]  = get_attr(run, None, "accession")     if run is not None else ""
    row["total_spots"]    = get_attr(run, None, "total_spots")   if run is not None else ""
    row["total_bases"]    = get_attr(run, None, "total_bases")   if run is not None else ""
    row["run_published"]  = get_attr(run, None, "published")     if run is not None else ""

    # --- SUBMISSION ---
    sub = pkg.find("SUBMISSION")
    row["submission_accession"] = get_attr(sub, None, "accession") if sub is not None else ""

    return row

# Column order for the TSV header
COLUMNS = [
    "experiment_accession","experiment_alias","center_name","experiment_title",
    "platform","instrument_model",
    "library_name","library_strategy","library_source","library_selection","library_layout",
    "study_accession","bioproject_id","study_title","study_abstract",
    "sample_accession","biosample_id","sample_title",
    "taxon_id","scientific_name",
    "collected_by","collection_date","geo_loc_name","host","host_disease",
    "isolation_source","isolation_type","lat_lon","host_sex","strain","isolate",
    "BioSampleModel","other_sample_attrs",
    "run_accession","total_spots","total_bases","run_published",
    "submission_accession",
]

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.xml> [output.tsv]", file=sys.stderr)
        sys.exit(1)

    xml_path = sys.argv[1]
    tsv_path = sys.argv[2] if len(sys.argv) > 2 else xml_path.rsplit(".", 1)[0] + ".tsv"

    print(f"Parsing {xml_path} …", file=sys.stderr)

    # Iterparse to handle large files without loading the whole tree
    n = 0
    with open(tsv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t",
                                extrasaction="ignore", lineterminator="\n")
        writer.writeheader()

        context = ET.iterparse(xml_path, events=("end",))
        for event, elem in context:
            if elem.tag == "EXPERIMENT_PACKAGE":
                row = parse_experiment_package(elem)
                writer.writerow(row)
                n += 1
                if n % 500 == 0:
                    print(f"  … {n} packages processed", file=sys.stderr)
                elem.clear()   # free memory

    print(f"Done. {n} records written to {tsv_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
