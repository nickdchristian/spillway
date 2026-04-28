from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SpillwayConfig:
    region: str = "us-east-1"
    profile: str | None = None
    severities: list[str] = field(default_factory=lambda: ["CRITICAL", "HIGH"])
    accounts: list[str] = field(default_factory=list)
    dry_run: bool = True
    advanced_filters: dict | None = None


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"Warning: Failed to parse YAML config at {path}: {e}")
        return {}


def load_configuration(
    explicit_file: str | None = None,
    cli_region: str | None = None,
    cli_profile: str | None = None,
    cli_severities: list[str] | None = None,
    cli_accounts: list[str] | None = None,
    cli_dry_run: bool | None = None,
) -> SpillwayConfig:

    config_data = {}
    config_data.update(_load_yaml(Path.home() / ".spillway.yaml"))
    config_data.update(_load_yaml(Path.cwd() / "spillway.yaml"))

    if explicit_file:
        config_data.update(_load_yaml(Path(explicit_file)))

    advanced_filters = config_data.pop("CompositeFilters", None)
    if advanced_filters:
        config_data["advanced_filters"] = {"CompositeFilters": advanced_filters}

    if cli_region is not None:
        config_data["region"] = cli_region
    if cli_profile is not None:
        config_data["profile"] = cli_profile
    if cli_severities:
        config_data["severities"] = cli_severities
    if cli_accounts:
        config_data["accounts"] = cli_accounts
    if cli_dry_run is not None:
        config_data["dry_run"] = cli_dry_run

    valid_keys = SpillwayConfig.__dataclass_fields__.keys()
    filtered_data = {k: v for k, v in config_data.items() if k in valid_keys}

    return SpillwayConfig(**filtered_data)
