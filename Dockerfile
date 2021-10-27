FROM quay.io/ebi-ait/ingest-base-images:python_3.7-alpine
LABEL maintainer="Javier Ferrer <jferrer@ebi.ac.uk>"

# Install build essentials (needed to build some python requirements)
RUN apk add --no-cache gcc musl-dev libffi-dev python3-dev libressl-dev git
RUN pip install --upgrade pip

# Prepare contents
ADD . /ingest-graph-validator
WORKDIR /ingest-graph-validator

# Install prerequisites
RUN pip install -e .

ENV INGEST_GRAPH_VALIDATOR_INGEST_API_URL="https://api.ingest.archive.data.humancellatlas.org"
ENV INGEST_GRAPH_VALIDATOR_GOOGLE_APPLICATION_CREDENTIALS="~/.secrets/gcp_credentials"
ENV INGEST_GRAPH_VALIDATOR_INGEST_JWT_AUDIENCE="https://data.humancellatlas.org/"
ENV AMQP_CONNECTION="amqp://guest:guest@localhost:5672"

# Run app
CMD echo "[START] Starting ingest graph validator"; ingest-graph-validator init; ingest-graph-validator ingest-validator graph_test_set
