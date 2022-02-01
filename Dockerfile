FROM quay.io/ebi-ait/ingest-base-images:python_3.7-alpine

WORKDIR /ingest-graph-validator

# Install build essentials (needed to build some python requirements)
RUN apk add --no-cache gcc musl-dev libffi-dev python3-dev libressl-dev git
RUN pip install --upgrade pip

# Install cryptography first to get around errors on install
RUN pip install cryptography==3.3.1

# Install prerequisites
ADD ./requirements.txt /ingest-graph-validator/requirements.txt
# Install cryptography first to get around errors on install
RUN pip install cryptography==3.3.1
RUN pip install -r requirements.txt

ADD . /ingest-graph-validator/
RUN pip install -r requirements.txt

ENV INGEST_GRAPH_VALIDATOR_INGEST_API_URL="https://api.ingest.archive.data.humancellatlas.org"
ENV INGEST_GRAPH_VALIDATOR_GOOGLE_APPLICATION_CREDENTIALS="/.secrets/gcp_credentials"
ENV INGEST_GRAPH_VALIDATOR_INGEST_JWT_AUDIENCE="https://data.humancellatlas.org/"
ENV AMQP_CONNECTION="amqp://guest:guest@localhost:5672"
ENV INGEST_GRAPH_VALIDATOR_NEO4J_URL="localhost"

CMD echo "[START] Starting ingest graph validator"; ingest-graph-validator -d $INGEST_GRAPH_VALIDATOR_NEO4J_URL action ingest-validator graph_test_set
