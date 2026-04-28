import logging

from spillway.config import SpillwayConfig

logger = logging.getLogger(__name__)


def _build_filters(config: SpillwayConfig) -> dict:
    """Translates the SpillwayConfig into the AWS Boto3 OCSF filter dictionary."""
    if config.advanced_filters:
        return config.advanced_filters

    composite_filters = []

    # Maps legacy ASFF WorkflowStatus to OCSF 'status'
    composite_filters.append(
        {
            "StringFilters": [
                {
                    "FieldName": "status",
                    "Filter": {"Value": "NEW", "Comparison": "EQUALS"},
                },
                {
                    "FieldName": "status",
                    "Filter": {"Value": "NOTIFIED", "Comparison": "EQUALS"},
                },
            ],
            "Operator": "OR",
        }
    )

    if config.severities:
        composite_filters.append(
            {
                "StringFilters": [
                    {
                        "FieldName": "severity",
                        "Filter": {"Value": sev.upper(), "Comparison": "EQUALS"},
                    }
                    for sev in config.severities
                ],
                "Operator": "OR",
            }
        )

    if config.accounts:
        composite_filters.append(
            {
                "StringFilters": [
                    {
                        "FieldName": "cloud.account.uid",
                        "Filter": {"Value": acc, "Comparison": "EQUALS"},
                    }
                    for acc in config.accounts
                ],
                "Operator": "OR",
            }
        )

    return {"CompositeFilters": composite_filters, "CompositeOperator": "AND"}
