# -*- coding: utf-8 -*-

"""Runs graph validation tests in the specified folder."""

import logging

from .common import load_test_queries
from ..config import Config

class TestAction:

    def __init__(self, graph, test_path, exit_on_failure):
        self._graph = graph
        self._test_path = test_path
        self._exit_on_failure = exit_on_failure

        self._test_queries = {}
        """Test query dict. Keys are test file names, values are cypher queries"""

        self._logger = logging.getLogger(__name__)

    def run(self):
        self._logger.info("loading tests")

        self._test_queries = load_test_queries(self._test_path)
        self._logger.info(f"loaded [{len(self._test_queries)}] test queries")

        self._logger.info("running tests")

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

        
        self._logger.info("All tests finished")
        error_message = f"Failed test names: {', '.join(total_result.keys())}"

        return {
            "message": error_message,
            "valid": is_valid
        }

