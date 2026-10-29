"""CLDR cardinal plural rules: which of zero, one, two, few, many or other a number takes in a language.

    plural_category(1, "en-US")    # "one"
    plural_category(1.5, "en-US")  # "other" (a visible fraction is never "one" in English)
    plural_category(3, "pl-PL")    # "few"

The operands follow CLDR: n is the absolute value, i the integer digits, v the count of visible fraction
digits, f those digits as an integer and t the same without trailing zeros. A float is read through its
shortest repr, so 1.50 written as the float 1.5 has v=1. Pass a string ("1.50") to keep trailing zeros.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, NamedTuple, Union

Number = Union[int, float, Decimal, str]

CATEGORIES = ("zero", "one", "two", "few", "many", "other")


class Operands(NamedTuple):
    n: float
    i: int
    v: int
    f: int
    t: int
    e: int


def operands(value: Number) -> Operands:
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        a = abs(value)
        return Operands(float(a), a, 0, 0, 0, 0)
    text = repr(float(value)) if isinstance(value, float) else str(value)
    try:
        d = abs(Decimal(text.strip()))
    except InvalidOperation:
        raise ValueError("not a number: %r" % (value,))
    if not d.is_finite():
        return Operands(float(d), 0, 0, 0, 0, 0)
    s = format(d, "f")
    whole, _, frac = s.partition(".")
    if isinstance(value, float) and frac == "0":
        frac = ""
    i = int(whole or "0")
    v = len(frac)
    f = int(frac) if frac else 0
    t_digits = frac.rstrip("0")
    t = int(t_digits) if t_digits else 0
    return Operands(float(d), i, v, f, t, 0)


Rule = Callable[[Operands], str]


def _other(o: Operands) -> str:
    return "other"


def _one_i1_v0(o: Operands) -> str:  # en, de, nl, sv, et, fi, ...
    return "one" if o.i == 1 and o.v == 0 else "other"


def _one_n1(o: Operands) -> str:  # el, hu, tr, nb, ...
    return "one" if o.n == 1 else "other"


def _million(o: Operands) -> bool:
    return o.i != 0 and o.i % 1000000 == 0 and o.v == 0


def _es(o: Operands) -> str:
    if o.n == 1:
        return "one"
    return "many" if _million(o) else "other"


def _it(o: Operands) -> str:
    if o.i == 1 and o.v == 0:
        return "one"
    return "many" if _million(o) else "other"


def _fr(o: Operands) -> str:  # also pt (Brazil)
    if o.i in (0, 1):
        return "one"
    return "many" if _million(o) else "other"


def _da(o: Operands) -> str:
    return "one" if o.n == 1 or (o.t != 0 and o.i in (0, 1)) else "other"


def _is(o: Operands) -> str:
    one = (o.t == 0 and o.i % 10 == 1 and o.i % 100 != 11) or (o.t % 10 == 1 and o.t % 100 != 11)
    return "one" if one else "other"


def _hi(o: Operands) -> str:
    return "one" if o.i == 0 or o.n == 1 else "other"


def _he(o: Operands) -> str:
    if (o.i == 1 and o.v == 0) or (o.i == 0 and o.v != 0):
        return "one"
    return "two" if o.i == 2 and o.v == 0 else "other"


def _ar(o: Operands) -> str:
    n, m = o.n, o.n % 100
    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    if n == int(n) and 3 <= m <= 10:
        return "few"
    if n == int(n) and 11 <= m <= 99:
        return "many"
    return "other"


def _cs(o: Operands) -> str:  # also sk
    if o.v != 0:
        return "many"
    if o.i == 1:
        return "one"
    return "few" if 2 <= o.i <= 4 else "other"


def _pl(o: Operands) -> str:
    if o.v != 0:
        return "other"
    i10, i100 = o.i % 10, o.i % 100
    if o.i == 1:
        return "one"
    if 2 <= i10 <= 4 and not 12 <= i100 <= 14:
        return "few"
    return "many"


def _slavic(o: Operands) -> str:  # ru, uk
    if o.v != 0:
        return "other"
    i10, i100 = o.i % 10, o.i % 100
    if i10 == 1 and i100 != 11:
        return "one"
    if 2 <= i10 <= 4 and not 12 <= i100 <= 14:
        return "few"
    return "many"


def _hr(o: Operands) -> str:  # also sr, bs
    i10, i100, f10, f100 = o.i % 10, o.i % 100, o.f % 10, o.f % 100
    if (o.v == 0 and i10 == 1 and i100 != 11) or (f10 == 1 and f100 != 11):
        return "one"
    if (o.v == 0 and 2 <= i10 <= 4 and not 12 <= i100 <= 14) or (2 <= f10 <= 4 and not 12 <= f100 <= 14):
        return "few"
    return "other"


def _lv(o: Operands) -> str:
    n10, n100, f10, f100 = o.n % 10, o.n % 100, o.f % 10, o.f % 100
    if n10 == 0 or 11 <= n100 <= 19 or (o.v == 2 and 11 <= f100 <= 19):
        return "zero"
    if (n10 == 1 and n100 != 11) or (o.v == 2 and f10 == 1 and f100 != 11) or (o.v != 2 and f10 == 1):
        return "one"
    return "other"


def _lt(o: Operands) -> str:
    if o.f != 0:
        return "many"
    n10, n100 = o.n % 10, o.n % 100
    if n10 == 1 and not 11 <= n100 <= 19:
        return "one"
    if 2 <= n10 <= 9 and not 11 <= n100 <= 19:
        return "few"
    return "other"


def _ro(o: Operands) -> str:
    if o.i == 1 and o.v == 0:
        return "one"
    if o.v != 0 or o.n == 0 or (o.n != 1 and 1 <= o.n % 100 <= 19):
        return "few"
    return "other"


def _sl(o: Operands) -> str:
    if o.v != 0:
        return "few"
    i100 = o.i % 100
    if i100 == 1:
        return "one"
    if i100 == 2:
        return "two"
    return "few" if i100 in (3, 4) else "other"


RULES: Dict[str, Rule] = {
    **{lang: _other for lang in ("ja", "zh", "ko", "th", "id", "ms", "vi", "yue")},
    **{lang: _one_i1_v0 for lang in ("en", "de", "nl", "sv", "et", "fi", "ca", "gl", "ur")},
    **{lang: _one_n1 for lang in ("el", "hu", "tr", "nb", "no", "nn", "bg", "sq", "az", "kk", "ka", "sw")},
    "es": _es, "it": _it, "fr": _fr, "pt": _fr, "da": _da, "is": _is, "hi": _hi, "bn": _hi, "gu": _hi,
    "he": _he, "iw": _he, "ar": _ar, "cs": _cs, "sk": _cs, "pl": _pl, "ru": _slavic, "uk": _slavic,
    "be": _slavic, "hr": _hr, "sr": _hr, "bs": _hr, "lv": _lv, "lt": _lt, "ro": _ro, "mo": _ro, "sl": _sl,
}


def _pt_pt(o: Operands) -> str:
    return _it(o)


def rule_for(locale: str) -> Rule:
    """The rule for a BCP 47 tag. Portugal follows the European rule (only exactly 1 is "one");
    a language with no table falls back to the English rule."""
    parts = (locale or "en").replace("_", "-").split("-")
    lang = parts[0].lower()
    if lang == "pt" and len(parts) > 1 and parts[-1].upper() == "PT":
        return _pt_pt
    return RULES.get(lang, _one_i1_v0)


def plural_category(value: Number, locale: str = "en") -> str:
    """The CLDR plural category of `value` in `locale`: "zero", "one", "two", "few", "many" or "other"."""
    return rule_for(locale)(operands(value))
