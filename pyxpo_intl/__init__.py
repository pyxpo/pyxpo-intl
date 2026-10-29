"""Locale-aware messages, plurals, numbers and dates for pyxpo apps, in pure Python.

ICU MessageFormat, CLDR plural rules, and the parts of Intl.NumberFormat and Intl.DateTimeFormat that apps
use, with no native code and no ICU data download.
"""
from .dates import days_between, format_date_range, format_datetime, set_default_time_zone, to_datetime
from .message import MessageError, format_message, format_rich, parse
from .number import format_number, symbols_for
from .plural import plural_category
from .provider import IntlContext, IntlProvider, IntlValue, use_formatter, use_intl, use_locale, use_translations
from .translator import Formatter, Translator, create_translator, lookup, with_fallback

__version__ = "0.1.0a1"

__all__ = [
    "Formatter", "IntlContext", "IntlProvider", "IntlValue", "MessageError", "Translator", "create_translator",
    "days_between", "format_date_range", "format_datetime", "format_message", "format_number", "format_rich",
    "lookup", "parse", "plural_category", "set_default_time_zone", "symbols_for", "to_datetime",
    "use_formatter", "use_intl", "use_locale", "use_translations", "with_fallback",
]
