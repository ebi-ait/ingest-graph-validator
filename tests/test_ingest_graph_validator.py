#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ingest_graph_validator` package."""

import pytest

from click.testing import CliRunner

from ingest_graph_validator import ingest_graph_validator


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""

    runner = CliRunner()
    result = runner.invoke(ingest_graph_validator.entry_point)
    assert result.exit_code == 0
    assert 'entry-point' in result.output
    help_result = runner.invoke(ingest_graph_validator.entry_point, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output
