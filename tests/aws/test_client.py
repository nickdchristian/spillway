from unittest.mock import MagicMock, patch

from spillway.aws.client import get_securityhub_client


@patch("spillway.aws.client.Config")
@patch("spillway.aws.client.boto3.Session")
def test_get_securityhub_client_defaults(mock_session, mock_config_cls):
    """
    Tests client creation with default parameters and verifies the enterprise Config.
    """
    mock_client_instance = MagicMock()
    mock_session.return_value.client.return_value = mock_client_instance

    mock_config_instance = MagicMock()
    mock_config_cls.return_value = mock_config_instance

    client = get_securityhub_client()

    # Verify Config was created with the right enterprise settings
    mock_config_cls.assert_called_once_with(
        region_name="us-east-1",
        retries={"max_attempts": 10, "mode": "adaptive"},
        max_pool_connections=50,
        user_agent_extra="Spillway-Security-Automation/1.0",
    )

    # Verify session was created with correct defaults
    mock_session.assert_called_once_with(profile_name=None, region_name="us-east-1")

    # Verify client was created using the mock Config
    mock_session.return_value.client.assert_called_once_with(
        "securityhub", config=mock_config_instance, endpoint_url=None
    )

    assert client == mock_client_instance


@patch("spillway.aws.client.Config")
@patch("spillway.aws.client.boto3.Session")
def test_get_securityhub_client_custom_args(mock_session, mock_config_cls):
    """Tests client creation using specific AWS profile, region, and endpoint."""
    mock_client_instance = MagicMock()
    mock_session.return_value.client.return_value = mock_client_instance

    mock_config_instance = MagicMock()
    mock_config_cls.return_value = mock_config_instance

    get_securityhub_client(
        region="eu-central-1",
        profile="security-audit",
        endpoint_url="http://localhost:4566",
    )

    mock_config_cls.assert_called_once_with(
        region_name="eu-central-1",
        retries={"max_attempts": 10, "mode": "adaptive"},
        max_pool_connections=50,
        user_agent_extra="Spillway-Security-Automation/1.0",
    )

    mock_session.assert_called_once_with(
        profile_name="security-audit", region_name="eu-central-1"
    )

    mock_session.return_value.client.assert_called_once_with(
        "securityhub", config=mock_config_instance, endpoint_url="http://localhost:4566"
    )
