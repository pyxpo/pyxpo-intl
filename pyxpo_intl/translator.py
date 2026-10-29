"""Translators over nested message catalogs, and a locale-bound formatter.

    messages = {"posts": {"count": "{n, plural, one {# post} other {# posts}}"}}
    t = create_translator(messages, "posts", "en-US")
    t("count", {"n": 2})     # "2 posts"
    t("missing")             # "posts.missing": a missing key shows its path, so it is easy to spot

    fmt = Formatter("de-DE", "Europe/Berlin")
    fmt.number(1234.5)                                  # "1.234,5"
    fmt.date_time("2026-10-30T15:04:00Z", dateStyle="medium")  # "30.10.2026"
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional

from .dates import format_datetime
from .message import format_message, format_rich
from .number import format_number


def lookup(messages: Mapping[str, Any], path: str) -> Any:
    """The value at a dotted `path` ("dash.shell.title") in nested dicts, or None."""
    node: Any = messages
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return None
        node = node[part]
    return node


def with_fallback(base: Mapping[str, Any], over: Mapping[str, Any]) -> Dict[str, Any]:
    """`over` merged into `base`, deeply. Lists and strings in `over` replace the base value whole."""
    out: Dict[str, Any] = dict(base)
    for key, value in over.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
            out[key] = with_fallback(out[key], value)
        else:
            out[key] = value
    return out


class Translator:
    """Formats the messages under `namespace`. Calls are `t(key, values)`."""

    def __init__(self, messages: Mapping[str, Any], namespace: Optional[str] = None, locale: str = "en-US",
                 time_zone: Optional[str] = None,
                 on_missing: Optional[Callable[[str], Any]] = None) -> None:
        self.messages = messages
        self.namespace = namespace
        self.locale = locale
        self.time_zone = time_zone
        self.on_missing = on_missing

    def _path(self, key: str) -> str:
        return "%s.%s" % (self.namespace, key) if self.namespace else key

    def raw(self, key: str) -> Any:
        """The unformatted value: a string, a nested dict, a list, or None."""
        return lookup(self.messages, self._path(key))

    def has(self, key: str) -> bool:
        return isinstance(self.raw(key), str)

    def _message(self, key: str) -> Optional[str]:
        value = self.raw(key)
        if isinstance(value, str):
            return value
        if self.on_missing:
            self.on_missing(self._path(key))
        return None

    def __call__(self, key: str, values: Optional[Mapping[str, Any]] = None) -> str:
        msg = self._message(key)
        if msg is None:
            return self._path(key)
        return format_message(msg, values, self.locale, self.time_zone)

    def rich(self, key: str, values: Optional[Mapping[str, Any]] = None) -> List[Any]:
        """Parts with tag callbacks applied: `t.rich("terms", {"link": lambda kids: Link(*kids)})`."""
        msg = self._message(key)
        if msg is None:
            return [self._path(key)]
        return format_rich(msg, values, self.locale, self.time_zone)

    def namespaced(self, namespace: str) -> "Translator":
        """A translator for a sub-namespace."""
        return Translator(self.messages, self._path(namespace), self.locale, self.time_zone, self.on_missing)


def create_translator(messages: Mapping[str, Any], namespace: Optional[str] = None, locale: str = "en-US",
                      time_zone: Optional[str] = None, on_missing: Optional[Callable[[str], Any]] = None) -> Translator:
    return Translator(messages, namespace, locale, time_zone, on_missing)


class Formatter:
    """Number and date formatting bound to one locale and time zone."""

    def __init__(self, locale: str = "en-US", time_zone: Optional[str] = None) -> None:
        self.locale = locale
        self.time_zone = time_zone

    def number(self, value: Any, **opts: Any) -> str:
        return format_number(value, self.locale, **opts)

    def date_time(self, value: Any, **opts: Any) -> str:
        if self.time_zone and "timeZone" not in opts and "time_zone" not in opts:
            opts["timeZone"] = self.time_zone
        return format_datetime(value, self.locale, **opts)

    dateTime = date_time
