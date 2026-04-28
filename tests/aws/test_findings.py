import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from spillway.aws.findings import get_findings
from spillway.config import SpillwayConfig


@pytest.fixture
def mock_config():
    return SpillwayConfig(region="us-east-1", profile="default-profile")


def test_get_findings_local_mode_success(monkeypatch, tmp_path, mock_config):
    """
    Tests that local mode successfully loads and yields findings from the JSON file.
    """
    monkeypatch.setenv("SPILLWAY_ENV", "local")
    monkeypatch.chdir(tmp_path)  # Isolate file creation to the temp directory

    dummy_data = {
        "Findings": [
            {"Id": "123", "Title": "Bad SG"},
            {"Id": "456", "Title": "Open S3"},
        ]
    }
    dummy_file = tmp_path / "dummy_findings.json"
    dummy_file.write_text(json.dumps(dummy_data))

    findings = list(get_findings(mock_config))

    assert len(findings) == 2
    assert findings[0]["Id"] == "123"


def test_get_findings_local_mode_missing_file(monkeypatch, tmp_path, mock_config):
    """Tests that local mode raises a FileNotFoundError if the dummy file is missing."""
    monkeypatch.setenv("SPILLWAY_ENV", "local")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="missing"):
        list(get_findings(mock_config))


@patch("spillway.aws.findings._build_filters")
@patch("spillway.aws.findings.get_securityhub_client")
def test_get_findings_aws_mode_pagination(
    mock_get_client, mock_build_filters, monkeypatch, mock_config
):
    """
    Tests that the AWS mode correctly unpacks the paginator and yields findings.
    """
    monkeypatch.delenv("SPILLWAY_ENV", raising=False)

    # Setup the mock filter payload
    mock_filters = {"CompositeFilters": [{"Operator": "AND"}]}
    mock_build_filters.return_value = mock_filters

    # Setup the Boto3 mock chain
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator

    # Simulate an AWS API response with two pages of results
    mock_paginator.paginate.return_value = iter(
        [{"Findings": [{"Id": "1"}]}, {"Findings": [{"Id": "2"}, {"Id": "3"}]}]
    )

    findings = list(get_findings(mock_config))

    mock_build_filters.assert_called_once_with(mock_config)
    mock_get_client.assert_called_once_with(
        region="us-east-1", profile="default-profile"
    )
    mock_client.get_paginator.assert_called_once_with("get_findings_v2")
    mock_paginator.paginate.assert_called_once_with(Filters=mock_filters)

    assert len(findings) == 3
    assert [f["Id"] for f in findings] == ["1", "2", "3"]


@patch("spillway.aws.findings.logger")
@patch("spillway.aws.findings._build_filters")
@patch("spillway.aws.findings.get_securityhub_client")
def test_get_findings_aws_mode_client_error(
    mock_get_client, mock_build_filters, mock_logger, monkeypatch, mock_config
):
    """Tests that Boto3 ClientErrors are caught, logged, and re-raised."""
    monkeypatch.delenv("SPILLWAY_ENV", raising=False)

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Simulate an Access Denied error from AWS
    error_response = {
        "Error": {"Code": "AccessDeniedException", "Message": "User is not authorized"}
    }
    mock_client.get_paginator.side_effect = ClientError(error_response, "GetFindingsV2")

    with pytest.raises(ClientError):
        list(get_findings(mock_config))

    mock_logger.error.assert_called_once_with("AWS API Error: User is not authorized")
