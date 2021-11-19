# Tests directory
In this folder you will find the tests the Human Cell Atlas uses for validating entities in their experiments

# How to request new tests
To request the creation of new tests, please follow this guide:

1. Open an issue with the template `Test addition`, filling in all the fields (When possible)
1. If you don't know how to create/modify cypher queries or create pull requests (PR) in GitHub, please wait for the admins of the repository to create a PR for you and skip to step 7.
1. Create a new branch and copy the contents of `graph_test_set/template.txt` into a new document inside the same folder. The newly created rule should be evident in the filename (e.g. `file_have_links.adoc`)
1. Fill in the template. The test is a Cypher query which should try to identify when a dataset is not following the rule. For example:
```
File: 10x_has_more_than_2_files.adoc
---
MATCH (r:library_preparation_protocol)<-[:PROTOCOLS]-(p:process)<-[d]-(f:sequence_file)
WITH r, p, COUNT(d) as num_files
WHERE r.`library_construction_method.ontology_label` =~ "10[xX] ([35]' ){0,1}v[1-3]" // 10x v1, v2 and v3
AND NOT num_files >= 2 // Number of files is more than 1
RETURN p, "Sequencing processes using 10x library preparation protocols must have more than 1 linked files", labels(p)
---
```
Will identify those 10x experiments in which the `num_files` is not in between 2 and 4 (Both included).

5. Commit your changes and push into your branch.
1. Create a PR indicating:
   - Title: `<Short description of issue>.Fixes #<Issue number>`
   - Name of the new file created
   - Description of the test
1. If the creator of the PR is an admin of the repository, please ping the creator of the ticket to confirm this is the issue they want to tackle.
If the person who created the PR is the same one as the person who created the ticket, wait for the administrators to review the PR.
1. The PR should be reviewed within 3-4 working days, and the last person to review the PR should merge it to master.

# Index of tests currently performed by the validator

Last updated: **2021-11-19**

## max2files_in_set
#### Test description
The same sequence data file must not be linked to two different processes.

## Paired end experiment has 2 or more files
#### Test description
When a sequencing protocol is paired-end, test whether it has 2 or more sequencing files linked.

## ensure_seq_libr_prep_protocols
#### Test description
Ensure that exactly one pair of sequencing and library preparation  protocols are linked to each sequence_file.

## ensure_lane_index
#### Test description
If more than one R1/R2/I1/I2 in a set, then ensure lane indices are specified.
If more than one set of R1/R2/I1/I2 SEQUENCE_FILEs belong to a single  process (sequencing experiment) AND those files lack any lane_index, then this snippet returns an error.

## Processes using 10x library preparation protocols have 1 or more files linked
#### Test description
Processes using 10x library preparation protocols have more than 1 files linked

## HSAPDV ontology is used for human donors
#### Test description
Ensure the Human developmental stages ontology is used for human donors to describe their development stage.

## Non-standard technologies (Non-10x, non-SS2) have information about the cell barcodes
#### Test description
When a sequencing protocol is non-10x, non-ss2, test whether metadata is complete.

## Donor to file path must have at least 5 nodes
#### Test description
There should be a minimum of 5 modes from a donor to a data file:
`(donor_organism)->(process)->(biomaterial)->(process)->(file)`

## If a protocol has a document, a matching supplementary file must exist
#### Test description
If a protocol defines a supplementary file as the document describing it, there must exist a supplementary file that
is named exactly the same.
If any filenames are returned by this test, that means those files are missing as they are specified in protocols and
do not exist.

## Non-standard technologies (Non-10x, non-SS2) have information about the parity of the reads
#### Test description
When a sequencing protocol is non-10x, non-ss2, test whether metadata is complete.

## Library preparations should only contain 1 read type per lane index
#### Test description
Library preparations (defined by process ID of the process linking cell suspension to sequence files) should never
contain a repeated type of read within the same lane (e.g. only 1 R1 in library_prep_1 and lane_index=1).

## No orphaned entities
#### Test description
Ensure that orphan nodes do not exist in a dataset graph. Orphan nodes with no relationships must not exist in dataset graph.
Every node must have at least one connection.

## the file extension provided in the field "file_format" must match the file name provided in the metadata.
#### Test description
Test whether file format is present in the name of the file.

## Sequence files link to cell suspension in single cell experiments
#### Test description
The biomaterial linked to the process linked to a sequence file must be a cell suspension in single cell experiments.
This next query provides the filenames, biomaterial IDs and nucleic acid sources linked together that break this assumption

## Experimental design is acyclical
#### Test description
This test searches for directed cycles in the experimental design.

## Donors are not derived
#### Test description
Makes sure the indegree of donor_organism nodes when excluding INPUT_BIOMATERIALS type is 0. They should be the root
of the _experimental design_.

## Processes using smartseq2 library preparation protocols have 2 or 3 files linked
#### Test description
Processes using smartseq2 library preparation protocols have 2 or 3 files linked.

## Non-standard technologies (Non-10x, non-SS2) have information about the UMI barcodes
#### Test description
When a sequencing protocol is non-10x, non-ss2, test whether metadata is complete.


