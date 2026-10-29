"""Locale number formatting, the subset of Intl.NumberFormat apps need.

    format_number(1234.5, "de-DE")                                   # "1.234,5"
    format_number(0.256, "en-US", style="percent")                   # "26%"
    format_number(0.2567, "fr-FR", style="percent", maximumFractionDigits=1)  # "25,7 %"
    format_number(1234, "en-IN")                                     # "1,234"; 1234567 gives "12,34,567"
    format_number(12.5, "en-US", style="currency", currency="USD")   # "$12.50"
    format_number(15300, "en-US", notation="compact")                # "15K"

Options use the JavaScript names (snake_case works too): style ("decimal", "percent", "currency"),
currency, minimumFractionDigits, maximumFractionDigits, minimumIntegerDigits, useGrouping, notation
("standard", "compact"), signDisplay ("auto", "always", "exceptZero", "never"). Rounding is half away from
zero, as in JavaScript.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, NamedTuple, Optional

NBSP, NNBSP = " ", " "


class Symbols(NamedTuple):
    decimal: str = "."
    group: str = ","
    min_grouping: int = 1      # 2: four-digit numbers are not grouped (es-ES 1234, but 12.345)
    indian: bool = False       # 12,34,567
    percent: str = "{}%"
    digits: str = "0123456789"
    currency: str = "{s}{n}"   # {s} symbol, {n} number


_DOT_COMMA = Symbols(",", ".", percent="{}\u00a0%", currency="{n} {s}")
_SPACE_COMMA = Symbols(",", NBSP, percent="{} %", currency="{n} {s}")
_ARAB = Symbols("٫", "٬", percent="{}٪؜", digits="٠١٢٣٤٥٦٧٨٩",
                currency="{n} {s}")

# By language, then overrides by full tag. Values from CLDR 44, as browsers ship them.
LANGUAGES: Dict[str, Symbols] = {
    "en": Symbols(),
    "de": _DOT_COMMA,
    "es": Symbols(",", ".", min_grouping=2, percent="{} %", currency="{n} {s}"),
    "pt": Symbols(",", ".", percent="{}%", currency="{s} {n}"),
    "fr": Symbols(",", NNBSP, percent="{} %", currency="{n} {s}"),
    "it": Symbols(",", ".", percent="{}%", currency="{n} {s}"),
    "nl": Symbols(",", ".", percent="{}%", currency="{s} {n}"),
    "da": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "el": Symbols(",", ".", percent="{}%", currency="{n} {s}"),
    "hr": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "is": Symbols(",", ".", percent="{}%", currency="{n} {s}"),
    "ro": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "sl": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "tr": Symbols(",", ".", percent="%{}", currency="{s}{n}"),
    "id": Symbols(",", ".", percent="{}%", currency="{s}{n}"),
    "cs": _SPACE_COMMA, "sk": _SPACE_COMMA, "fi": _SPACE_COMMA, "nb": _SPACE_COMMA, "no": _SPACE_COMMA,
    "sv": Symbols(",", NBSP, percent="{} %", currency="{n} {s}"),
    "et": Symbols(",", NBSP, min_grouping=2, percent="{}%", currency="{n} {s}"),
    "lv": Symbols(",", NBSP, percent="{}%", currency="{n} {s}"),
    "lt": Symbols(",", NBSP, percent="{} %", currency="{n} {s}"),
    "hu": Symbols(",", NBSP, percent="{}%", currency="{n} {s}"),
    "pl": Symbols(",", NBSP, min_grouping=2, percent="{}%", currency="{n} {s}"),
    "ru": Symbols(",", NBSP, percent="{} %", currency="{n} {s}"),
    "uk": Symbols(",", NBSP, percent="{}%", currency="{n} {s}"),
    "hi": Symbols(indian=True),
    "ar": Symbols(),
    "he": Symbols(currency="‏{n} {s}"),
    "ja": Symbols(), "zh": Symbols(), "ko": Symbols(), "th": Symbols(),
}

TAGS: Dict[str, Symbols] = {
    "en-IN": Symbols(indian=True),
    "en-150": Symbols(",", ".", percent="{}%", currency="{n} {s}"),
    "en-SE": Symbols(",", NBSP, percent="{} %"),
    "en-DE": Symbols(",", ".", percent="{} %"),
    "es-MX": Symbols(percent="{} %", currency="{s}{n}"),
    "es-PR": Symbols(percent="{} %", currency="{s}{n}"),
    "es-US": Symbols(percent="{} %", currency="{s}{n}"),
    "es-419": Symbols(percent="{} %", currency="{s}{n}"),
    "es-CL": Symbols(",", ".", percent="{} %", currency="{s}{n}"),
    "es-CO": Symbols(",", ".", percent="{} %", currency="{s} {n}"),
    "es-UY": Symbols(",", ".", percent="{} %", currency="{s} {n}"),
    "pt-PT": Symbols(",", NBSP, min_grouping=2, percent="{}%", currency="{n} {s}"),
    "de-AT": Symbols(",", NBSP, percent="{} %", currency="{s} {n}"),
    "de-CH": Symbols(".", "’", percent="{}%", currency="{s} {n}"),
    "it-CH": Symbols(".", "’", percent="{}%", currency="{s} {n}"),
    "fr-CH": Symbols(",", NNBSP, percent="{}%", currency="{n} {s}"),
    "fr-CA": Symbols(",", NBSP, percent="{} %", currency="{n} {s}"),
    "fr-LU": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "fr-MA": Symbols(",", ".", percent="{} %", currency="{n} {s}"),
    "nl-BE": Symbols(",", ".", percent="{}%", currency="{s} {n}"),
    "ar-SA": _ARAB, "ar-QA": _ARAB, "ar-EG": _ARAB, "ar-JO": _ARAB,
    "ar-MA": Symbols(",", ".", percent="{}‎%‎", currency="{n} {s}"),
    "ar-AE": Symbols(percent="{}‎%‎", currency="‏{n} {s}"),
}

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹", "BRL": "R$",
                    "CNY": "¥", "KRW": "₩", "ILS": "₪", "CAD": "CA$", "AUD": "A$", "MXN": "MX$"}
CURRENCY_DIGITS = {"JPY": 0, "KRW": 0, "CLP": 0, "ISK": 0, "HUF": 2}

# Compact suffixes by language: (thousand, million, billion, trillion). Others use English.
COMPACT = {
    "en": ("K", "M", "B", "T"),
    "es": (" mil", " M", " mil M", " B"),
    "pt": (" mil", " mi", " bi", " tri"),
    "de": (" Tsd.", " Mio.", " Mrd.", " Bio."),
    "fr": (" k", " M", " Md", " Bn"),
    "it": ("", " Mln", " Mrd", " Bln"),
}


def symbols_for(locale: str) -> Symbols:
    tag = (locale or "en").replace("_", "-")
    parts = tag.split("-")
    lang = parts[0].lower()
    region = next((p.upper() for p in parts[1:] if len(p) == 2 and p.isalpha() or p.isdigit()), None)
    key = "%s-%s" % (lang, region) if region else lang
    return TAGS.get(key) or LANGUAGES.get(lang) or LANGUAGES["en"]


def _opt(opts: Dict[str, Any], camel: str, default: Any = None) -> Any:
    snake = "".join("_" + c.lower() if c.isupper() else c for c in camel)
    return opts.get(camel, opts.get(snake, default))


def _group(digits: str, sym: Symbols, grouping: bool) -> str:
    if not grouping or len(digits) < 4 or (sym.min_grouping == 2 and len(digits) < 5):
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    size = 2 if sym.indian else 3
    while len(head) > size:
        parts.insert(0, head[-size:])
        head = head[:-size]
    parts.insert(0, head)
    return sym.group.join(parts + [tail])


def _digits(text: str, sym: Symbols) -> str:
    if sym.digits == "0123456789":
        return text
    return "".join(sym.digits[ord(c) - 48] if "0" <= c <= "9" else c for c in text)


def _plain(value: Decimal, sym: Symbols, min_fd: int, max_fd: int, min_id: int, grouping: bool) -> str:
    q = value.quantize(Decimal(1).scaleb(-max_fd), rounding=ROUND_HALF_UP)
    whole, _, frac = format(abs(q), "f").partition(".")
    frac = frac.rstrip("0")
    if len(frac) < min_fd:
        frac = frac + "0" * (min_fd - len(frac))
    whole = whole.rjust(min_id, "0")
    out = _group(whole, sym, grouping)
    if frac:
        out += sym.decimal + frac
    return _digits(out, sym)


def format_number(value: Any, locale: str = "en-US", **opts: Any) -> str:
    """Formats `value` (int, float, Decimal or numeric string) for `locale`. See the module doc for options."""
    if isinstance(value, bool):
        value = int(value)
    d = Decimal(repr(value)) if isinstance(value, float) else Decimal(str(value))
    if d.is_nan():
        return "NaN"
    if d.is_infinite():
        return ("-" if d < 0 else "") + "∞"
    sym = symbols_for(locale)
    style = _opt(opts, "style", "decimal")
    notation = _opt(opts, "notation", "standard")
    grouping = _opt(opts, "useGrouping", True) not in (False, "false")
    currency = (_opt(opts, "currency") or "").upper()
    if style == "currency" and not currency:
        raise ValueError("style='currency' needs a currency code, for example currency='USD'")
    if style == "percent":
        d = d * 100
        default_min, default_max = 0, 0
    elif style == "currency":
        default_min = default_max = CURRENCY_DIGITS.get(currency, 2)
    else:
        default_min, default_max = 0, 3
    suffix = ""
    if notation == "compact" and style != "percent":
        lang = (locale or "en").split("-")[0].lower()
        names = COMPACT.get(lang, COMPACT["en"])
        for power in (12, 9, 6, 3):
            if abs(d) >= Decimal(10) ** power and names[power // 3 - 1]:
                d = d / (Decimal(10) ** power)
                suffix = names[power // 3 - 1]
                break
        default_min, default_max = 0, (1 if abs(d) < 10 and suffix else 0)
    min_fd = _opt(opts, "minimumFractionDigits")
    max_fd = _opt(opts, "maximumFractionDigits")
    if min_fd is None:
        min_fd = min(default_min, max_fd) if max_fd is not None else default_min
    if max_fd is None:
        max_fd = max(default_max, min_fd)
    if not (0 <= min_fd <= max_fd <= 100):
        raise ValueError("fraction digits must satisfy 0 <= minimumFractionDigits <= maximumFractionDigits <= 100")
    min_id = int(_opt(opts, "minimumIntegerDigits", 1))
    body = _plain(d, sym, int(min_fd), int(max_fd), min_id, grouping) + suffix
    rounded_zero = d.quantize(Decimal(1).scaleb(-int(max_fd)), rounding=ROUND_HALF_UP) == 0
    negative = d < 0 and not rounded_zero
    if style == "percent":
        body = sym.percent.format(body)
    elif style == "currency":
        body = sym.currency.format(s=CURRENCY_SYMBOLS.get(currency, currency), n=body)
    sign_display = _opt(opts, "signDisplay", "auto")
    if sign_display == "never":
        return body
    if negative:
        return "-" + body
    if sign_display == "always" or (sign_display == "exceptZero" and not rounded_zero):
        return "+" + body
    return body
