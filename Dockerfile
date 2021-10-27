# ingest-graph-validator dockerfile
#
# Author: Javier Ferrer

FROM python:3.7-alpine
LABEL maintainer="Javier Ferrer <jferrer@ebi.ac.uk>"

# Install build essentials (needed to build some python requirements)
RUN apk add --no-cache gcc musl-dev libffi-dev python-dev libressl-dev

# Prepare contents
ADD . /ingest-graph-validator
WORKDIR /ingest-graph-validator

# Install prerequisites
RUN pip install -r requirements.txt

ENV INGEST_GRAPH_VALIDATOR_INGEST_API_URL="https://api.ingest.archive.data.humancellatlas.org"
ENV INGEST_GRAPH_VALIDATOR_GOOGLE_APPLICATION_CREDENTIALS="~/.secrets/gcp_credentials"
ENV INGEST_GRAPH_VALIDATOR_INGEST_JWT_AUDIENCE="https://data.humancellatlas.org/"
ENV AMQP_CONNECTION="amqp://guest:guest@localhost:5672"

# Run app
CMD echo "[START] Starting ingest graph validator"; ./testrun.py
