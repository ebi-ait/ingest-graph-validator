[![PyPI](https://img.shields.io/pypi/v/ingest-graph-validator.svg)](https://pypi.org/project/ingest-graph-validator/)

# HCA Ingest Service Graph Validation Suite

## What is this useful for in the scope of the HCA:

1. Enables data wranglers to visually analyze the relationships inside a submission to look for inconsistencies.
2. Provides an automated graph validator for which to create tests using step 1 and can be run fully containerized.


## Features

The suite is divided in two separate, extensible parts:

* **hydrators** enable users to import and populate data into a graph database. The reason not to call them importers is `import` is a reserved keyword in Python and `from importers import importer` is a bit confusing. :dizzy_face:

* **actions** provide different tools to work with the generated graph. The first and most important is to run a series of tests to validate the constraints Data Wranglers want to impose on submissions. Another action is generating reports and extracting statistics from the graph to send to the submitters. Any other actions can be implemented to extend the suite.

## Functionality

So far, the functionality planned is as follows (WIP items are still not fully implemented):

* Hydrators:
    * Ingest Service Spreadsheet.
    * Ingest Service API Submission.
    * BioSamples API (WIP).

* Actions:
    * Opening an interactive visualizer to query the graph.
    * Running tests on the graph.
    * Generating reports for the graph (WIP).


## Installation

The Graph Validator Suite requires docker running in the host machine.

### From the git repo

```
git clone git@github.com:ebi-ait/ingest-graph-validator.git
cd ingest-graph-validator
pip install .
```

### <a name="install_pypi"></a>From PyPI

A Python package has been published in (PyPI)[https://pypi.org/project/ingest-graph-validator].

*The installation into a (virtualenv)[https://packaging.python.org/guides/installing-using-pip-and-virtual-environments] is heavily recommended.*

```pip install ingest-graph-validator```

If you install the Graph Validator Suite this way, you should head to the [github repo](https://github.com/ebi-ait/ingest-graph-validator) to get the [graph tests](https://github.com/ebi-ait/ingest-graph-validator/tree/master/graph_test_set) and the [graph reports](https://github.com/ebi-ait/ingest-graph-validator/tree/master/graph_report_set).


## Usage

### Wrangler EC2
The graph validator is installed on the Wrangler EC2. The Neo4j Browser UI of this instance can be accessed at http://tool.archive.data.humancellatlas.org:7474/browser/.

If you have HCAWrangler user credientials configured in a profile called `hca-util`, the username/password stored in AWS Secrets can be retrieved using the command:

```
$ aws secretsmanager get-secret-value --secret-id ingest/tool/wrangler/ec2/neo4j --region us-east-1 --query SecretString --output text --profile hca-util
```


To import/load new project into the graph db:
- log into the EC2 via SSH
- navigate to the installation dir and activate the environment
    ```
    $ cd /data/tools/ingest-graph-validator/
    $ . venv/bin/activate
    ```
- you don't need to run `ingest-graph-validator init` as the server is already running in the background

- you will need to run the following command before importing a spreadsheet or ingest submission uuid, where password is determined using the aws secretsmanager command shown above (password includes quotation marks):

    ```
    $ export INGEST_GRAPH_VALIDATOR_NEO4J_DB_PASSWORD=[password]
    ```

- import a spreadsheet
    ```
    $ ingest-graph-validator hydrate xls <path/to/xls>
    ```
- import using an ingest submission uuid
    ```
    $ ingest-graph-validator hydrate ingest <sub_uuid>
    ```
- run tests (commonly used dir is graph_test_set)
    ```
    $ ingest-graph-validator action test <path/to/tests_dir>
    ```
- don't forget to exit the virtual environment when done
    ```
    $ deactivate
    ```

### Step by step usage for running locally

1. Ensure Docker is installed and running

1. Once [installed from the Python package](#install_pypi), start the backend by opening a terminal and typing:

    `ingest-graph-validator init`

    **Keep in mind**, first time executing the `init` command will take longer as it has to pull the Neo4j Docker image from dockerhub.

1. Import a spreadsheet:

    `ingest-graph-validator hydrate xls <spreadsheet filename>`

1. Go to <http://localhost:7474> in a browser to open the frontend.

1. Connect to the backend (you do not need to change any fields, leave username/password empty):

   ![](.readme/connect_backend.png)

1. You can then start writing [cypher queries](https://neo4j.com/graphacademy/online-training/introduction-to-neo4j/) in the input field on top of the web frontend to visualize the graph. For example:

    ```MATCH p=(n) RETURN p```

    Will show the entire graph. Keep in mind this will crash the browser on huge datasets.

**Note**
The server backend will continue running in the background, and you only need to open the browser again to continue your work. If you want to shutdown the backend, open a terminal and type:

`ingest-graph-validator shutdown`

### How to run tests
In order to run the tests in the `graph_test_set` directory, you need to run the following commands:

1. In a shell, run:
```
ingest-graph-validator init
```
If you want to run using an ingest submission uuid:
```
ingest-graph-validator hydrate ingest <ingest_submission_uuid>
```
If you want to run using a spreadsheet
```
ingest-graph-validator hydrate xls <path/to/spreadsheet>
```
then
```
ingest-graph-validator action test <path_to_tests>
```

### More help

The Graph Validator Suite uses a CLI similar to [git](https://git-scm.com/). Running a command without specifying anything else will show help for that command. At each level, the commands have different arguments and options. Running any subcommand with `-h` or `--help` with give you more information about it.

The root level commands are:

* **`ingest-graph-validator init`** starts the database backend and enables a frontend visualizer to query the database, in `http://localhost:7474` by default.

* **`ingest-graph-validator hydrate`** shows the list of available hydrators.

* **`ingest-graph-validator actions`** shows the list of available actions.

* **`ingest-graph-validator shutdown`** stops the backend.


### Running as a queue listener
It is possible to run the graph validator so that it listens to a queue on RabbitMQ that receives submission UUIDs. Once a message is received from the queue the hydrate and action commands are ran for the given submission UUID.

`ingest-graph-validator action ingest-validator graph_test_set`

The above command runs the listener for the `graph_test_set`

#### Running queue listener locally against locally running ingest
1. Ensure you have a locally running and populated [Ingest Mongo DB](https://ebi-ait.github.io/hca-ebi-dev-team/admin_setup/Onboarding.html#mongodb)
2. Make sure ingest-core and rabbitMQ are running
3. `export INGEST_GRAPH_VALIDATOR_INGEST_API_URL=http://localhost:8080`
4. `docker run -p7687:7687 -p7474:7474 --env NEO4J_AUTH=neo4j/password --env=NEO4J_ACCEPT_LICENSE_AGREEMENT=yes neo4j:3.5.14-enterprise`
5. `ingest-graph-validator action ingest-validator graph_test_set`
6. Use the `localhost:8080/submissionEnvelopes/<ID>/validateGraph` endpoint to add to the queue


#### Running queue listener with docker-compose
1. `mkdir _secrets; aws secretsmanager get-secret-value --region us-east-1 --secret-id ingest/dev/gcp-credentials.json | jq -r .SecretString > _secrets/gcp_credentials`
  - The ingest-graph-validator uses the dev ingest API as configured in docker-compose.yml
2. `docker-compose up --build`
3. Ensure you have a locally running and populated [Ingest Mongo DB](https://ebi-ait.github.io/hca-ebi-dev-team/admin_setup/Onboarding.html#mongodb)
4. Run ingest core locally
5. Use the `localhost:8080/submissionEnvelopes/<ID>/validateGraph` endpoint to add to the queue
  - Since the graph validator is running and listening to dev ingest API, make sure you are submitting a submission ID that exists in dev
  - It is not possible to forward local ports to the docker network created by docker-compose so cannot expose the locally running ingest core to the running ingest-graph-validator container


*Note: change the environment variables defined in docker-compose.yml to connect to prod or staging ingest API*
# Extra stuff

## Useful cypher queries

### Show all nodes and relationships
```
MATCH p = (n)
RETURN p
```

### Show all nodes and relationship excluding some
```
MATCH p = (n)
WHERE NOT n:LABEL AND NOT n:LABEL
RETURN p
```

### Expands paths from a node
This one will be shown with an example. The example selects the donor CBTM-376C from [Meyer's Tissue Stability](https://ui.ingest.data.humancellatlas.org/submissions/detail?uuid=fd52efcc-6924-4c8a-b68c-a299aea1d80f) dataset, and expands the paths to show all biomaterials, processes and files linked to it.

**Note**: Make sure to strictly define **only one node** to use as the source, otherwise it will be confusing.

**Note**: You have to be careful not to include nodes that would link your path to another one. For example, `protocol` or `project` are linked to more than one _experimental design_.

The first two lines are used to select one single node from which to expand. The third line expands the path using these parameters:

1. `n`, the starting node or nodes (preferably one for your first queries).
2. `""`, the [relationship filter](http://neo4j-contrib.github.io/neo4j-apoc-procedures/3.5/path-finding/path-expander/#_relationship_filter). We are not filtering by any relations in this query.
3. `"-project|-protocol"`, the [label filter](http://neo4j-contrib.github.io/neo4j-apoc-procedures/3.5/path-finding/path-expander/#_label_filter). We are excluding (hence the minus sign) any nodes with the labels `project` or (that is represented by the `|`) `protocol`.
4. `0` is the minimum depth. Normally 0. Otherwise the starting nodes get excluded.
5. `-1` is used to determine the maximum depth for the path expansion. -1 means no limit. If you would set a 1 here, the result would be the `CBTM-376C` donor and its first level neighbours.

```
MATCH (n:donor_organism)
WHERE n.`biomaterial_core.biomaterial_id` = "CBTM-376C"
CALL apoc.path.expand(n, "", "-project|-protocol", 0, -1) YIELD path
RETURN path
```


## Releasing a new version to PyPI

You should have a maintainer role access for [this project in PyPI](https://pypi.org/project/ingest-graph-validator/).

1. Bump the version and create a tag
    ```
    make patch|minor|major
    ```
1. Upload to PyPI
    ```
    make release
    ```

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter).

