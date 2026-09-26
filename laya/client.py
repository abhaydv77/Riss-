"""Shared client for the official Laya SDK and base English checkpoint."""
from __future__ import annotations

from importlib import metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from threading import Lock
from types import ModuleType

MODEL_ID = "convaiinnovations/laya"


class LayaClientError(RuntimeError):
    """Raised when SDK loading or a model prediction fails."""


_agent = None
_sdk_module: ModuleType | None = None
_lock = Lock()


def _load_sdk_module() -> ModuleType:
    """Load the installed SDK under an alias because this repo also has laya/."""
    global _sdk_module
    if _sdk_module is not None:
        return _sdk_module
    try:
        sdk_init = Path(metadata.distribution("laya").locate_file("laya/__init__.py"))
        if not sdk_init.is_file():
            raise FileNotFoundError(f"Installed laya SDK not found at {sdk_init}")
        name = "_guapd_laya_sdk"
        spec = spec_from_file_location(
            name, sdk_init, submodule_search_locations=[str(sdk_init.parent)]
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load installed SDK package at {sdk_init}")
        module = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _sdk_module = module
        return module
    except Exception as exc:
        raise LayaClientError(
            "Could not import the installed 'laya' SDK. Install the pinned project requirements."
        ) from exc


def get_agent():
    """Load the requested base checkpoint once per process."""
    global _agent
    if _agent is None:
        with _lock:
            if _agent is None:
                try:
                    _agent = _load_sdk_module().load(MODEL_ID)
                except Exception as exc:
                    raise LayaClientError(
                        f"Could not load base Laya checkpoint {MODEL_ID!r}: {exc}"
                    ) from exc
    return _agent


def predict(state: dict, questions: dict, agent=None) -> dict:
    """Send every typed question in one SDK call and return its raw response."""
    try:
        return (agent if agent is not None else get_agent()).predict(state, questions)
    except Exception as exc:
        raise LayaClientError(f"Laya prediction failed: {exc}") from exc


__all__ = ["MODEL_ID", "LayaClientError", "get_agent", "predict"]
