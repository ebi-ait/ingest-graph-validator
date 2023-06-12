# -*- coding: utf-8 -*-

"""Ingest Service Submission hydrator."""
import logging
import time
from importlib import reload

from hca_ingest.api.ingestapi import IngestApi
from py2neo import Node, Relationship, Graph

from .common import flatten, convert_to_macrocase
from .hydrator import Hydrator
from ..config import Config
from ..utils import benchmark


# Example sub_uuid for a small submission (wong retina): 668791ed-deec-4470-b23a-9b80fd133e1c
class IngestHydrator(Hydrator):
    """
    DCP Ingest Service Submission hydrator class.

    Enables importing of HCA Ingest Service submissions by specifying a Submission ID.
    """

    def __init__(self, graph:Graph, submission_uuid):
        super().__init__(graph)
        self.ingest_throttle_period = Config['INGEST_THROTTLE_PERIOD']
        self._logger.info(f"Started ingest hydrator for for submission [{submission_uuid}]")

        self._ingest_api = IngestApi(Config['INGEST_API'])

        project_url = self._ingest_api.get_submission_by_uuid(submission_uuid)['_links']['relatedProjects']['href']
        project = self._ingest_api.get(project_url).json()['_embedded']['projects'][0]

        self._logger.info(f"Found project for submission {project['uuid']['uuid']}")

        self._entities = []
        for submission in self.fetch_submissions_in_project(project):
            self.process_submission(submission)

        self._nodes = self.get_nodes()
        self._edges = self.get_edges()

    @benchmark
    def process_submission(self, submission):
        self._logger.info(f"Found submission for project with uuid {submission['uuid']['uuid']}")
        self._entities.extend(list(self.build_entities_from_submission(submission)))

    def fetch_submissions_in_project(self, project: dict) -> [dict]:
        self._logger.debug(f"Fetching submissions for project {project['uuid']['uuid']}")
        url = self._ingest_api.get_link_from_resource(project, link_name='submissionEnvelopes')
        return self._ingest_api.get(url).json()['_embedded']['submissionEnvelopes']

    @benchmark
    def build_entities_from_submission(self, submission: dict):
        id_field_map = {
            'biomaterials': "biomaterial_core.biomaterial_id",
            'files': "file_core.file_name",
            'processes': "process_core.process_id",
            'projects': "project_core.project_short_name",
            'protocols': "protocol_core.protocol_id",
        }

        for entity_type in ["biomaterials", "files", "processes", "projects", "protocols"]:
            self._logger.info(f"processing entity type {entity_type}")
            submission_url = self._ingest_api.get_link_from_resource(submission, link_name='self')
            entity_num = 0
            for entity in self._ingest_api.get_entities(submission_url, entity_type):
                if entity_num % self.batch_size == 0:
                    self._logger.info(f'finished {entity_num} items of type {entity_type}')
                entity_num = entity_num + 1
                properties = flatten(entity['content'])

                new_entity = {
                    'properties': properties,
                    'labels': [entity['type'].lower()],
                    'node_id': properties[id_field_map[entity_type]],
                    'links': entity['_links'],
                    'uuid': entity['uuid']['uuid'],
                }
                self._logger.debug(f"processing {entity_type} node with id {new_entity['node_id']}")

                concrete_type = new_entity['properties']['describedBy'].rsplit('/', 1)[1]
                new_entity['labels'].append(concrete_type)

                yield new_entity
            self._logger.info(f'finished {entity_num} items of type {entity_type}')

    @benchmark
    def get_nodes(self):
        self._logger.info("importing nodes")

        nodes = {}

        for entity in self._entities:
            node_id = entity['node_id']
            nodes[entity['uuid']] = Node(*entity['labels'],
                                         **entity['properties'],
                                         uuid=entity['uuid'],
                                         self_link=entity['links']['self']['href'],
                                         id=node_id)

        self._logger.info(f"imported {len(nodes)} nodes")

        return nodes

    @benchmark
    def get_edges(self):
        self._logger.info("importing edges")

        relationship_map = {
            'projects': "projects",
            'protocols': "protocols",
            'inputToProcesses': "processes",
            'derivedByProcesses': "processes",
            'inputBiomaterials': "biomaterials",
            'derivedBiomaterials': "biomaterials",
            'supplementaryFiles': "files",
            'inputFiles': "files",
            'derivedFiles': "files",
        }

        entity_num = 0
        for entity in self._entities:
            for relationship_type in relationship_map.keys():
                if relationship_type in entity['links']:
                    url = entity['links'][relationship_type]['href']
                    entity_type = relationship_map[relationship_type]
                    relationships = self._ingest_api.get_all(url, entity_type)
                    start_node = self._nodes[entity['uuid']]
                    relationship_name = convert_to_macrocase(relationship_type)
                    for end_entity in relationships:
                        if entity_num % self.batch_size == 0:
                            self._logger.info(f'get_edges: completed {entity_num} items')
                        entity_num = entity_num + 1

                        try:
                            end_node = self._nodes[end_entity['uuid']['uuid']]
                            yield Relationship(start_node, relationship_name, end_node)

                            # Adding additional relationships to the graphs.
                            if relationship_name == 'INPUT_TO_PROCESSES':
                                yield Relationship(start_node, 'DUMMY_EXPERIMENTAL_DESIGN', end_node)
                            if relationship_name == 'DERIVED_BY_PROCESSES':
                                yield Relationship(end_node, 'DUMMY_EXPERIMENTAL_DESIGN', start_node)

                            self._logger.debug(f"({start_node['id']})-[:{relationship_name}]->({end_node['id']})")
                        except KeyError:
                            self._logger.debug(f"Missing end node at a [{start_node['id']}] entity.")

        self._logger.info(f"importing edges finished")
