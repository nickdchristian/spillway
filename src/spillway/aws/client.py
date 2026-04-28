import boto3
from botocore.config import Config


def get_securityhub_client(
    region: str = "us-east-1",
    profile: str | None = None,
    endpoint_url: str | None = None,
):
    """Establishes and returns an enterprise-configured Security Hub client."""
    boto_config = Config(
        region_name=region,
        retries={"max_attempts": 10, "mode": "adaptive"},
        max_pool_connections=50,
        user_agent_extra="Spillway-Security-Automation/1.0",
    )

    session = boto3.Session(profile_name=profile, region_name=region)

    return session.client("securityhub", config=boto_config, endpoint_url=endpoint_url)
