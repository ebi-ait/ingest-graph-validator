# -*- coding: utf-8 -*-

"""Runs graph validation tests in the specified folder."""

import logging

from ingest.utils.s2s_token_client import S2STokenClient, ServiceCredential
from ingest.utils.token_manager import TokenManager
from ingest.api.ingestapi import IngestApi

from .common import load_test_queries
from ..config import Config




class TestAction:

    def __init__(self, graph, test_path, exit_on_failure, submission_uuid = None):
        self._graph = graph
        self._test_path = test_path
        self._exit_on_failure = exit_on_failure
        self._submission_uuid = submission_uuid

        if self._submission_uuid:
            # Note all logic surrounding adding to ingest can be moved to ingest_validator_action.py in dcp-506
            # ingest_validator_action.py spins up a queue to listen to
            s2s_token_client = S2STokenClient(
                credential=ServiceCredential.from_file(Config['GOOGLE_APPLICATION_CREDENTIALS']),
                audience=Config['INGEST_JWT_AUDIENCE']
            )
            token_manager = TokenManager(s2s_token_client)
            self._ingest_api = IngestApi(Config['INGEST_API'], token_manager=token_manager)


        self._test_queries = {}
        """Test query dict. Keys are test file names, values are cypher queries"""

        self._logger = logging.getLogger(__name__)

    def run(self):
        self._logger.info("loading tests")

        self._test_queries = load_test_queries(self._test_path)
        self._logger.info(f"loaded [{len(self._test_queries)}] test queries")

        self._logger.info("running tests")

        if self._submission_uuid:
            submission = self._ingest_api.get_submission_by_uuid(self._submission_uuid)
            if submission["graphValidationState"] != "Pending":
                raise RuntimeError(f"Cannot perform validation on submission {self._submission_uuid} as grapValidationState is not 'Pending'")
            submission_url = submission["_links"]["self"]["href"]
            self._ingest_api.put(f'{submission_url}/graphValidatingEvent', data=None)

        bad_tests = 0
        is_valid = True
        total_result = {}

        for test_name, test_query in self._test_queries.items():
            self._logger.debug(f"running test [{test_name}]")
            result = self._graph.run(test_query).data()

            if len(result) != 0:
                is_valid = False
                self._logger.error(f"test [{test_name}] failed: non-empty result.")
                self._logger.error(f"result: {result}")
                total_result[test_name] = result

                if self._exit_on_failure is True:
                    self._logger.info("execution terminated")
                    exit(1)

        
        self._logger.info(f"all tests finished {'([{}] failed)'.format(bad_tests) if bad_tests > 0 else ''}")
        
        if self._submission_uuid:
            if is_valid:
                self._ingest_api.put(f'{submission_url}/graphValidEvent', data=None)
            else:
                self._ingest_api.put(f'{submission_url}/graphInvalidEvent', data=None)

        return {
            "messages": total_result,
            "valid": is_valid
        }
