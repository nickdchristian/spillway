from pathlib import Path

import pytest

from spillway.aws.filters import _build_filters
from spillway.config import SpillwayConfig, load_configuration


@pytest.fixture
def example_yaml(tmp_path):
    """Generates a temporary YAML file based on example.spillway.yaml."""
    yaml_content = """
    region: us-west-2
    dry_run: false
    severities:
      - CRITICAL
    accounts:
      - "111122223333"
    CompositeFilters:
      - Operator: AND
        StringFilters:
          - FieldName: cloud.account.uid
            Filter:
              Value: "555555555555"
              Comparison: NOT_EQUALS
    """
    config_file = tmp_path / "spillway.yaml"
    config_file.write_text(yaml_content)
    return config_file


@pytest.fixture(autouse=True)
def isolate_paths(monkeypatch):
    """Prevents tests from reading actual system configuration files."""
    monkeypatch.setattr("spillway.config.Path.home", lambda: Path("/nonexistent_home"))
    monkeypatch.setattr("spillway.config.Path.cwd", lambda: Path("/nonexistent_cwd"))


def test_default_config():
    """Tests the dataclass defaults when no files or args are provided."""
    config = load_configuration()
    assert config.region == "us-east-1"
    assert config.dry_run is True
    assert config.severities == ["CRITICAL", "HIGH"]
    assert config.accounts == []
    assert config.advanced_filters is None


def test_yaml_config_loading(example_yaml):
    """Tests that values are correctly parsed from a YAML file."""
    config = load_configuration(explicit_file=str(example_yaml))

    assert config.region == "us-west-2"
    assert config.dry_run is False
    assert config.severities == ["CRITICAL"]
    assert config.accounts == ["111122223333"]
    assert config.advanced_filters is not None

    # Verifies the extraction and nesting of CompositeFilters
    assert "CompositeFilters" in config.advanced_filters
    assert config.advanced_filters["CompositeFilters"][0]["Operator"] == "AND"


def test_cli_overrides_yaml(example_yaml):
    """Tests that CLI arguments take precedence over YAML values."""
    config = load_configuration(
        explicit_file=str(example_yaml),
        cli_region="eu-central-1",
        cli_severities=["MEDIUM", "LOW"],
        cli_dry_run=True,
    )

    # These should be overridden by CLI args
    assert config.region == "eu-central-1"
    assert config.severities == ["MEDIUM", "LOW"]
    assert config.dry_run is True

    # This should be retained from the YAML file
    assert config.accounts == ["111122223333"]


def test_build_standard_filters():
    """Tests generation of standard OCSF filters."""
    config = SpillwayConfig(severities=["high", "medium"], accounts=["12345"])
    filters = _build_filters(config)

    assert "CompositeFilters" in filters
    assert filters["CompositeOperator"] == "AND"

    composite = filters["CompositeFilters"]
    # We expect 3 blocks: status, severity, and account
    assert len(composite) == 3

    # Check status block
    status_filter = composite[0]
    assert status_filter["Operator"] == "OR"
    assert status_filter["StringFilters"][0]["FieldName"] == "status"
    assert status_filter["StringFilters"][0]["Filter"]["Value"] == "NEW"

    # Check severity block
    sev_filter = composite[1]
    assert sev_filter["Operator"] == "OR"
    assert sev_filter["StringFilters"][0]["FieldName"] == "severity"
    assert sev_filter["StringFilters"][0]["Filter"]["Value"] == "HIGH"
    assert sev_filter["StringFilters"][1]["Filter"]["Value"] == "MEDIUM"

    # Check account block
    acc_filter = composite[2]
    assert acc_filter["Operator"] == "OR"
    assert acc_filter["StringFilters"][0]["FieldName"] == "cloud.account.uid"
    assert acc_filter["StringFilters"][0]["Filter"]["Value"] == "12345"


def test_build_advanced_filters_escape_hatch(example_yaml):
    """
    Tests that the presence of advanced_filters completely bypasses standard logic.
    """
    config = load_configuration(explicit_file=str(example_yaml))
    filters = _build_filters(config)

    # Output should exactly match the nested advanced_filters dict
    assert "CompositeFilters" in filters
    assert (
        filters["CompositeFilters"][0]["StringFilters"][0]["FieldName"]
        == "cloud.account.uid"
    )
    assert "CompositeOperator" not in filters  # Because it wasn't in the example YAML
