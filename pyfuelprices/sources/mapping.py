"""Sources mapping file."""

import importlib
import inspect
import pkgutil
import os

from . import Source

# Fields are as follows:
# Key - Provider Name
# Value - (Provider Class, Enabled, Available, Country Mapping Enabled)
# Available field is used to control what options are
# shown in the Home Assistant config wizard.
# The last int is an optional value that defines if the provider will be
# included in the area auto mapping system, if set to 0, the provider
# can only be configured manually

def load_sources():
    """Dynamically load all sources defined in sources."""
    sources: dict[str, tuple[object, int, int, int]] = {}
    country_code_mapping: dict[str, list[str]] = {}
    enabled_sources: dict[str, list[str]] = {}
    package = __package__
    package_path = os.path.dirname(__file__)
    for module_info in pkgutil.walk_packages([package_path], package + "."):
        full_module_name = module_info.name
        module = importlib.import_module(full_module_name)

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not obj.__module__.startswith(full_module_name):
                continue
            if inspect.isclass(obj) and issubclass(obj, Source) and obj is not Source:
                for country in obj.country_code if isinstance(obj.country_code, list) else [obj.country_code]:
                    country_code_mapping.setdefault(country, [])
                    enabled_sources.setdefault(country, [])
                    country_code_mapping[country].append(obj.provider_name)
                    if obj.enabled:
                        enabled_sources[country].append(obj.provider_name)
                sources[obj.provider_name] = (
                    obj,
                    int(obj.enabled),
                    int(obj.available_for_setup),
                    int(obj.auto_country_mapping)
                )
    return sources, country_code_mapping, enabled_sources

SOURCE_MAP, FULL_COUNTRY_MAP, COUNTRY_MAP = load_sources()
