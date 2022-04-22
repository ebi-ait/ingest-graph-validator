# -*- coding: utf-8 -*-

"""Ingest Service Submission hydrator."""

import time

from ingest.api.ingestapi import IngestApi
from py2neo import Node, Relationship

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

    def __init__(self, graph, submission_uuid):
        super().__init__(graph)

        self._logger.info(f"Started ingest hydrator for for submission [{submission_uuid}]")

        self._ingest_api = IngestApi(Config['INGEST_API'])

        project_url = self._ingest_api.get_submission_by_uuid(submission_uuid)['_links']['relatedProjects']['href']
        project = self._ingest_api.get(project_url).json()['_embedded']['projects'][0]

        self._logger.info(f"Found project for submission {project['uuid']['uuid']}")

        self._entities = {}
        for submission in self.fetch_submissions_in_project(project):
            self._logger.info(f"Found submission for project with uuid {submission['uuid']['uuid']}")
            for entity in self.build_entities_from_submission(submission):
                self._entities[entity['uuid']] = entity

        self._nodes = self.get_nodes()
        self._edges = self.get_edges()

    def fetch_submissions_in_project(self, project: dict) -> [dict]:
        self._logger.debug(f"Fetching submissions for project {project['uuid']['uuid']}")
        return self._ingest_api.get(project['_links']['submissionEnvelopes']['href']).json()['_embedded']['submissionEnvelopes']

    def build_entities_from_submission(self, submission: dict):
        id_field_map = {
            'biomaterials': "biomaterial_core.biomaterial_id",
            'files': "file_core.file_name",
            'processes': "process_core.process_id",
            'projects': "project_core.project_short_name",
            'protocols': "protocol_core.protocol_id",
        }

        for entity_type in ["biomaterials", "files", "processes", "projects", "protocols"]:
            for entity in self._ingest_api.get_entities(submission['_links']['self']['href'], entity_type):
                properties = flatten(entity['content'])

                new_entity = {
                    'properties': properties,
                    'labels': [entity['type'].lower()],
                    'node_id': properties[id_field_map[entity_type]],
                    'links': entity['_links'],
                    'uuid': entity['uuid']['uuid'],
                }

                concrete_type = new_entity['properties']['describedBy'].rsplit('/', 1)[1]
                new_entity['labels'].append(concrete_type)

                time.sleep(0.3)  # rate limit to stop overloading core

                yield new_entity

    @benchmark
    def get_nodes(self):
        self._logger.debug("importing nodes")

        nodes = {}

        for entity_uuid, entity in self._entities.items():
            node_id = entity['node_id']
            nodes[entity_uuid] = Node(*entity['labels'], **entity['properties'], uuid=entity['uuid'], self_link=entity['links']['self']['href'], id=node_id)

            self._logger.debug(f"({node_id})")

        self._logger.info(f"imported {len(nodes)} nodes")

        return nodes

    @benchmark
    def get_edges(self):
        self._logger.debug("importing edges")

        edges = []
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

        for entity_uuid, entity in self._entities.items():
            for relationship_type in relationship_map.keys():
                if relationship_type in entity['links']:
                    relationships = self._ingest_api.get_all(
                        entity['links'][relationship_type]['href'],
                        relationship_map[relationship_type]
                    )

                    for end_entity in relationships:
                        start_node = self._nodes[entity_uuid]
                        relationship_name = convert_to_macrocase(relationship_type)
                        try:
                            end_node = self._nodes[end_entity['uuid']['uuid']]
                            edges.append(Relationship(start_node, relationship_name, end_node))

                            # Adding additional relationships to the graphs.
                            if relationship_name == 'INPUT_TO_PROCESSES':
                                edges.append(Relationship(start_node, 'DUMMY_EXPERIMENTAL_DESIGN', end_node))
                            if relationship_name == 'DERIVED_BY_PROCESSES':
                                edges.append(Relationship(end_node, 'DUMMY_EXPERIMENTAL_DESIGN', start_node))

                            self._logger.debug(f"({start_node['id']})-[:{relationship_name}]->({end_node['id']})")
                        except KeyError:
                            self._logger.debug(f"Missing end node at a [{start_node['id']}] entity.")

        self._logger.info(f"imported {len(edges)} edges")

        return edges
