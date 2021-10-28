# -*- coding: utf-8 -*-

"""Runs graph validation tests in the specified folder."""

import logging, json

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin
from ingest.utils.s2s_token_client import S2STokenClient, ServiceCredential
from ingest.utils.token_manager import TokenManager
from ingest.api.ingestapi import IngestApi

from ..hydrators.ingest_hydrator import IngestHydrator
from .test_action import TestAction


from .common import load_test_queries

from ..config import Config


class ValidationHandler():

    def __init__(self, subid, graph, test_path):
        self._subid = subid
        self._graph = graph
        self._test_path = test_path

    def run(self):
        IngestHydrator(self._graph, self._subid).hydrate()
        return TestAction(self._graph, self._test_path, False).run()



class ValidationListener(ConsumerMixin):

    def __init__(self, connection, validation_queue, graph, test_path):
        self.connection = connection
        self.validation_queue = validation_queue
        self._graph = graph
        self._test_path = test_path

        if Config["INGEST_API"] == "http://localhost:8080":
            self._ingest_api = IngestApi(Config['INGEST_API'])
        else:
            s2s_token_client = S2STokenClient(
                credential=ServiceCredential.from_file(Config['GOOGLE_APPLICATION_CREDENTIALS']),
                audience=Config['INGEST_JWT_AUDIENCE']
            )
            token_manager = TokenManager(s2s_token_client)
            self._ingest_api = IngestApi(Config['INGEST_API'], token_manager=token_manager)


        self._logger = logging.getLogger(__name__)

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.validation_queue, accept=["application/json;charset=UTF-8", "json"], on_message=self.handle_message, prefetch_count=10)]

    def handle_message(self, message):
        payload = json.loads(message.payload)
        subid = payload['documentUuid']
        
        if(payload["documentType"] != "submissionenvelope"):
            self._logger.error(f"Cannot process document since is not a submission envelope. UUID: f{subid}")
            message.ack()
            return

        self._logger.info(f"received validation request for {subid}")

        submission = self._ingest_api.get_submission_by_uuid(subid)
        submission_url = submission["_links"]["self"]["href"]

        try:
            if submission["graphValidationState"] != "Validating":
                 self._logger.error(f"Cannot perform validation on submission {subid} as grapValidationState is not 'Pending'")
                 message.nack()
                 return
            
            self._ingest_api.put(f'{submission_url}/graphValidatingEvent', data=None)

            validation_result = ValidationHandler(subid, self._graph, self._test_path).run()

            if validation_result is not None:
                self._logger.info(f"validation finished for {subid}")
                self._logger.debug(f"result: {validation_result['message']}")

                if validation_result["valid"]:
                    self._ingest_api.put(f'{submission_url}/graphValidEvent', data=None)
                else:
                    self._ingest_api.put(f'{submission_url}/graphInvalidEvent', data=validation_result["message"])

                message.ack()
        except Exception as e:
            self._logger.error(f"Failed with error {e}.")
            self._logger.info("Reverting submission graphValidationState to Pending")
            self._ingest_api.put(f'{submission_url}/graphPendingEvent', data=None)
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
