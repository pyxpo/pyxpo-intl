"""pyxpo bindings: put a locale and its messages in context, then read translators anywhere below.

    @component
    def App():
        return IntlProvider(Home(), locale="es-ES", messages=load("es"), time_zone="Europe/Madrid")

    @component
    def Home():
        t = use_translations("home")
        fmt = use_formatter()
        return Text(t("greeting", {"name": "Ana"}) + " " + fmt.number(1234.5))
"""
from __future__ import annotations

from typing import Any, Mapping, NamedTuple, Optional

from pyxpo import component, create_context, use_context, use_memo

from .translator import Formatter, Translator


class IntlValue(NamedTuple):
    locale: str
    messages: Mapping[str, Any]
    time_zone: Optional[str]


IntlContext = create_context(IntlValue("en-US", {}, None))


@component
def IntlProvider(*children: Any, locale: str = "en-US", messages: Optional[Mapping[str, Any]] = None,
                 time_zone: Optional[str] = None):
    value = use_memo(lambda: IntlValue(locale, messages or {}, time_zone), [locale, id(messages), time_zone])
    return IntlContext.Provider(*children, value=value)


def use_intl() -> IntlValue:
    return use_context(IntlContext)


def use_locale() -> str:
    return use_intl().locale


def use_translations(namespace: Optional[str] = None) -> Translator:
    v = use_intl()
    return use_memo(lambda: Translator(v.messages, namespace, v.locale, v.time_zone), [v, namespace])


def use_formatter() -> Formatter:
    v = use_intl()
    return use_memo(lambda: Formatter(v.locale, v.time_zone), [v.locale, v.time_zone])
