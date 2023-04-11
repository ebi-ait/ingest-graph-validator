# -*- coding: utf-8 -*-

"""Runs graph validation tests in the specified folder."""

import json
import logging
import time

import requests.exceptions
from hca_ingest.api.ingestapi import IngestApi
from hca_ingest.utils.s2s_token_client import S2STokenClient, ServiceCredential
from hca_ingest.utils.token_manager import TokenManager
from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

from .common import load_test_queries
from .test_action import TestAction
from ..config import Config
from ..hydrators.ingest_hydrator import IngestHydrator


class ValidationHandler:
    def __init__(self, sub_uuid, graph, test_path):
        self._sub_uuid = sub_uuid
        self._graph = graph
        self._test_path = test_path

    def run(self):
        IngestHydrator(self._graph, self._sub_uuid).hydrate()
        return TestAction(self._graph, self._test_path, False).run()


class ValidationListener(ConsumerMixin):
    def __init__(self, connection, validation_queue, graph, test_path):
        self.connection = connection
        self.validation_queue = validation_queue
        self._graph = graph
        self._test_path = test_path

        if Config["INGEST_API"] == "http://localhost:8080" or not (
            Config["GOOGLE_APPLICATION_CREDENTIALS"] and Config["INGEST_JWT_AUDIENCE"]
        ):
            self._ingest_api = IngestApi(Config['INGEST_API'])
        else:
            s2s_token_client = S2STokenClient(
                credential=ServiceCredential.from_file(Config['GOOGLE_APPLICATION_CREDENTIALS']),
                audience=Config['INGEST_JWT_AUDIENCE']
            )
            token_manager = TokenManager(s2s_token_client)
            self._ingest_api = IngestApi(Config['INGEST_API'], token_manager=token_manager)

        self._logger = logging.getLogger(__name__)

    def get_consumers(self, consumer, channel):
        return [consumer(queues=self.validation_queue, accept=["application/json;charset=UTF-8", "json"],
                         on_message=self.handle_message, prefetch_count=10)]

    def __patch_entity(self, message, entity_link):
        entity = self._ingest_api.get(entity_link).json()
        errors = entity["graphValidationErrors"] or []
        errors.append(message)
        patch = {
            "graphValidationErrors": errors
        }
        self._ingest_api.patch(entity_link, json=patch)

    def __attempt_validation(self, submission, sub_uuid):
        try:
            submission_url = submission["_links"]["self"]["href"]
            if submission["submissionState"] == "Graph validating":
                raise RuntimeError(f"Cannot perform validation on submission {sub_uuid} as it is already validating.")

            self._ingest_api.put(f'{submission_url}/graphValidatingEvent', data=None)

            validation_result = ValidationHandler(sub_uuid, self._graph, self._test_path).run()

            if validation_result is not None:
                self._logger.info(f"validation finished for {sub_uuid}")

                if not validation_result["valid"]:
                    self._ingest_api.put(f'{submission_url}/graphInvalidEvent', data=None)

                    retries = 0
                    while True:
                        try:
                            time.sleep(0.5)
                            retries += 1
                            for failure in validation_result["failures"]:
                                for entity in failure['affectedEntities']:
                                    self.__patch_entity(failure['message'], entity['link'])
                            break

                        except requests.exceptions.HTTPError as e:
                            self._logger.info("Unable to patch entities right now. Probably since the submission "
                                              "state hasn't been updated yet. Retrying...")
                            if retries > 10:
                                raise Exception(e)
                else:
                    self._ingest_api.put(f'{submission_url}/graphValidEvent', data=None)
                self._logger.info(f'Finished validating {sub_uuid}.')
        except Exception as e:
            self._logger.error(f"Failed validation with error {e}.")
            # TODO add endpoint to restore submission to metadata valid and log error

        self._graph.delete_all()

    def handle_message(self, message):
        try:
            payload = json.loads(message.payload)
            sub_uuid = payload['documentUuid']

            if payload["documentType"] != "submissionenvelope":
                raise RuntimeError(f"Cannot process document since is not a submission envelope. UUID: f{sub_uuid}")

            self._logger.info(f"received validation request for {sub_uuid}")

            submission = self._ingest_api.get_submission_by_uuid(sub_uuid)
            self.__attempt_validation(submission, sub_uuid)
        except Exception as e:
            self._logger.error(f"Failed handling with error {e}.")

        message.ack()


class IngestValidatorAction:
    def __init__(self, graph, test_path, connection, exchange_name, queue_name, routing_key):
        self._graph = graph
        self._test_path = test_path
        self._connection = connection
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._routing_key = routing_key

        self._test_queries = {}
        """Test query dict. Keys are test file names, values are cypher queries"""

        self._logger = logging.getLogger(__name__)

    def run(self):
        self._logger.info("loading tests")

        self._test_queries = load_test_queries(self._test_path)
        self._logger.info(f"loaded [{len(self._test_queries)}] test queries")

        validation_exchange = Exchange(self._exchange_name, type='direct')
        validation_queue = Queue(self._queue_name, validation_exchange, routing_key=self._routing_key)

        with Connection(Config['AMQP_CONNECTION']) as conn:
            self._logger.info(f"listening for messages at {conn}")
            try:
                ValidationListener(conn, validation_queue, self._graph, self._test_path).run()
            except KeyboardInterrupt:
                self._logger.info("AMQP listener stopped")
