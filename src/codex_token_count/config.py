from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


CONFIG_FILE_NAME = ".codex-token.toml"


@dataclass(frozen=True)
class PricingConfig:
    input_per_million_usd: float
    cached_input_per_million_usd: float
    output_per_million_usd: float


@dataclass(frozen=True)
class DefaultsConfig:
    trend_days: int = 7
    project_limit: int = 3
    include_archived: bool = False


@dataclass(frozen=True)
class AppConfig:
    config_path: Path | None
    codex_home: Path
    defaults: DefaultsConfig
    pricing: PricingConfig | None


def find_config_file(start_dir: str | Path | None = None) -> Path | None:
    current = Path(start_dir or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / CONFIG_FILE_NAME
        if candidate.is_file():
            return candidate
    for candidate in _fallback_config_candidates():
        if candidate.is_file():
            return candidate
    return None


def load_config(start_dir: str | Path | None = None) -> AppConfig:
    config_path = find_config_file(start_dir)
    payload: dict[str, object] = {}
    if config_path is not None:
        with config_path.open("rb") as handle:
            payload = tomllib.load(handle)

    codex_section = _as_dict(payload.get("codex"))
    defaults_section = _as_dict(payload.get("defaults"))
    pricing_section = _as_dict(payload.get("pricing"))

    codex_home_value = codex_section.get("home")
    if codex_home_value:
        raw_home = Path(str(codex_home_value)).expanduser()
        if raw_home.is_absolute() or config_path is None:
            codex_home = raw_home
        else:
            codex_home = (config_path.parent / raw_home).resolve()
    else:
        codex_home = Path.home() / ".codex"

    defaults = DefaultsConfig(
        trend_days=_positive_int(defaults_section.get("trend_days"), 7),
        project_limit=_positive_int(defaults_section.get("project_limit"), 3),
        include_archived=_bool_value(defaults_section.get("include_archived"), False),
    )
    pricing = _load_pricing(pricing_section)

    return AppConfig(
        config_path=config_path,
        codex_home=codex_home,
        defaults=defaults,
        pricing=pricing,
    )


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _positive_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int) and value > 0:
        return value
    return default


def _load_pricing(section: dict[str, object]) -> PricingConfig | None:
    input_price = _float_value(section.get("input_per_million_usd"))
    cached_price = _float_value(section.get("cached_input_per_million_usd"))
    output_price = _float_value(section.get("output_per_million_usd"))
    if input_price is None or cached_price is None or output_price is None:
        return None
    return PricingConfig(
        input_per_million_usd=input_price,
        cached_input_per_million_usd=cached_price,
        output_per_million_usd=output_price,
    )


def _float_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _bool_value(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _fallback_config_candidates() -> tuple[Path, ...]:
    project_root = Path(__file__).resolve().parents[2]
    return (project_root / CONFIG_FILE_NAME,)
