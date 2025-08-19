# -*- coding: utf-8 -*-

"""Shared utility methods."""


from time import time
import logging
import requests

from functools import wraps

from hca_ingest.api.ingestapi import IngestApi
from hca_ingest.utils.s2s_token_client import S2STokenClient, ServiceCredential
from hca_ingest.utils.token_manager import TokenManager

from ingest_graph_validator.config import Config


def benchmark(function):
    @wraps(function)
    def _time_it(*args, **kwargs):
        logger = logging.getLogger(__name__)
        start = int(round(time() * 1000))

        try:
            return function(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            logger.info(f"[{function.__name__}] took [{end_}] ms")

    return _time_it


def download_file(url, destination_filename):
    """Downloads a file using a stream buffer."""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(destination_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return destination_filename

def get_ingest_api():
    _logger = logging.getLogger("get_ingest_api")
    api = None
    if Config["INGEST_API"] == "http://localhost:8080" or not (
        Config["GOOGLE_APPLICATION_CREDENTIALS"] and Config["INGEST_JWT_AUDIENCE"]
    ):
        _logger.info(f"connecting to ingest on {Config['INGEST_API']}")
        api = IngestApi(Config['INGEST_API'])
    else:
        _logger.info(
            f"connecting to ingest using token manager from {Config['GOOGLE_APPLICATION_CREDENTIALS']} with audience {Config['INGEST_JWT_AUDIENCE']} on {Config['INGEST_API']}")
        s2s_token_client = S2STokenClient(
            credential=ServiceCredential.from_file(Config['GOOGLE_APPLICATION_CREDENTIALS']),
            audience=Config['INGEST_JWT_AUDIENCE']
        )
        token_manager = TokenManager(s2s_token_client)
        api = IngestApi(Config['INGEST_API'], token_manager=token_manager)
    return api
