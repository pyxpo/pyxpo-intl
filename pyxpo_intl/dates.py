"""Locale date and time formatting, the subset of Intl.DateTimeFormat apps need.

    when = datetime(2026, 10, 30, 15, 4, tzinfo=timezone.utc)
    format_datetime(when, "en-US", dateStyle="medium")                     # "Oct 30, 2026"
    format_datetime(when, "en-GB", dateStyle="medium", timeStyle="short")  # "30 Oct 2026, 15:04"
    format_datetime(when, "es-ES", weekday="long", day="numeric", month="long")  # "viernes, 30 de octubre"
    format_datetime(when, "pt-BR", day="numeric", month="short")           # "30 de out."

Options use the JavaScript names (snake_case works too): dateStyle and timeStyle ("full", "long",
"medium", "short"), or the parts weekday ("long", "short"), year ("numeric", "2-digit"), month ("numeric",
"2-digit", "long", "short"), day, hour, minute, second ("numeric", "2-digit"), hour12, and timeZone (an IANA
name such as "Asia/Kolkata"; default: the device's zone). With no options it formats a numeric date, as
JavaScript does.

Month and weekday names ship for en, es, pt, de, fr, it, nl, ja, zh and ko. Other languages use their own
numeric date order and English names. Thai dates count Buddhist Era years, as the Thai calendar does.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone, tzinfo
from typing import Any, Dict, Optional, Tuple

_EN_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
              "October", "November", "December")
_EN_DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _names(months: str, months_short: str, days: str, days_short: str) -> Dict[str, Tuple[str, ...]]:
    return {"MMMM": tuple(months.split("|")), "MMM": tuple(months_short.split("|")),
            "EEEE": tuple(days.split("|")), "EEE": tuple(days_short.split("|"))}


NAMES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "en": {"MMMM": _EN_MONTHS, "MMM": tuple(m[:3] for m in _EN_MONTHS), "EEEE": _EN_DAYS,
           "EEE": tuple(d[:3] for d in _EN_DAYS)},
    "es": _names("enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre",
                 "ene|feb|mar|abr|may|jun|jul|ago|sept|oct|nov|dic",
                 "lunes|martes|miércoles|jueves|viernes|sábado|domingo", "lun|mar|mié|jue|vie|sáb|dom"),
    "pt": _names("janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro",
                 "jan.|fev.|mar.|abr.|mai.|jun.|jul.|ago.|set.|out.|nov.|dez.",
                 "segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|domingo",
                 "seg.|ter.|qua.|qui.|sex.|sáb.|dom."),
    "de": _names("Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember",
                 "Jan.|Feb.|März|Apr.|Mai|Juni|Juli|Aug.|Sept.|Okt.|Nov.|Dez.",
                 "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag", "Mo.|Di.|Mi.|Do.|Fr.|Sa.|So."),
    "fr": _names("janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre",
                 "janv.|févr.|mars|avr.|mai|juin|juil.|août|sept.|oct.|nov.|déc.",
                 "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche", "lun.|mar.|mer.|jeu.|ven.|sam.|dim."),
    "it": _names("gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre",
                 "gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic",
                 "lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica", "lun|mar|mer|gio|ven|sab|dom"),
    "nl": _names("januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december",
                 "jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec",
                 "maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag", "ma|di|wo|do|vr|za|zo"),
    "ja": _names("|".join("%d月" % m for m in range(1, 13)), "|".join("%d月" % m for m in range(1, 13)),
                 "月曜日|火曜日|水曜日|木曜日|金曜日|土曜日|日曜日", "月|火|水|木|金|土|日"),
    "zh": _names("|".join("%d月" % m for m in range(1, 13)), "|".join("%d月" % m for m in range(1, 13)),
                 "星期一|星期二|星期三|星期四|星期五|星期六|星期日", "周一|周二|周三|周四|周五|周六|周日"),
    "ko": _names("|".join("%d월" % m for m in range(1, 13)), "|".join("%d월" % m for m in range(1, 13)),
                 "월요일|화요일|수요일|목요일|금요일|토요일|일요일", "(월)|(화)|(수)|(목)|(금)|(토)|(일)"),
}
NAMES["zh-TW"] = dict(NAMES["zh"], EEE=tuple("週" + d for d in "一二三四五六日"))

_US = {"full": "EEEE, MMMM d, y", "long": "MMMM d, y", "medium": "MMM d, y", "short": "M/d/yy",
       "MMMMd": "MMMM d", "MMMd": "MMM d", "Md": "M/d", "yMd": "M/d/y", "MMMMy": "MMMM y", "MMMy": "MMM y",
       "EEEEMMMMd": "EEEE, MMMM d", "EEEMMMd": "EEE, MMM d", "at": " 'at' "}
_GB = {"full": "EEEE d MMMM y", "long": "d MMMM y", "medium": "d MMM y", "short": "dd/MM/y",
       "MMMMd": "d MMMM", "MMMd": "d MMM", "Md": "dd/MM", "yMd": "dd/MM/y", "MMMMy": "MMMM y", "MMMy": "MMM y",
       "EEEEMMMMd": "EEEE d MMMM", "EEEMMMd": "EEE d MMM", "at": " 'at' "}

PATTERNS: Dict[str, Dict[str, str]] = {
    "en": _GB,
    "en-US": _US, "en-PR": _US, "en-PH": dict(_US, short="M/d/yy"),
    "en-CA": dict(_US, short="y-MM-dd", yMd="y-MM-dd", Md="MM-dd"),
    "en-AU": dict(_GB, short="d/M/yy"), "en-IN": dict(_GB, short="dd/MM/yy", yMd="d/M/y", Md="d/M"),
    "es": {"full": "EEEE, d 'de' MMMM 'de' y", "long": "d 'de' MMMM 'de' y", "medium": "d MMM y", "short": "d/M/yy",
           "MMMMd": "d 'de' MMMM", "MMMd": "d MMM", "Md": "d/M", "yMd": "d/M/y", "MMMMy": "MMMM 'de' y",
           "MMMy": "MMM y", "EEEEMMMMd": "EEEE, d 'de' MMMM", "EEEMMMd": "EEE, d MMM", "at": ", "},
    "pt": {"full": "EEEE, d 'de' MMMM 'de' y", "long": "d 'de' MMMM 'de' y", "medium": "d 'de' MMM 'de' y",
           "short": "dd/MM/y", "MMMMd": "d 'de' MMMM", "MMMd": "d 'de' MMM", "Md": "dd/MM", "yMd": "dd/MM/y",
           "MMMMy": "MMMM 'de' y", "MMMy": "MMM 'de' y", "EEEEMMMMd": "EEEE, d 'de' MMMM",
           "EEEMMMd": "EEE, d 'de' MMM", "at": " 'às' "},
    "pt-PT": {"full": "EEEE, d 'de' MMMM 'de' y", "long": "d 'de' MMMM 'de' y", "medium": "dd/MM/y",
              "short": "dd/MM/yy", "MMMMd": "d 'de' MMMM", "MMMd": "d/MM", "Md": "dd/MM", "yMd": "dd/MM/y",
              "MMMMy": "MMMM 'de' y", "MMMy": "MM/y", "EEEEMMMMd": "EEEE, d 'de' MMMM", "EEEMMMd": "EEE, d/MM",
              "at": " 'às' "},
    "de": {"full": "EEEE, d. MMMM y", "long": "d. MMMM y", "medium": "dd.MM.y", "short": "dd.MM.yy",
           "MMMMd": "d. MMMM", "MMMd": "d. MMM", "Md": "d.M.", "yMd": "d.M.y", "MMMMy": "MMMM y", "MMMy": "MMM y",
           "EEEEMMMMd": "EEEE, d. MMMM", "EEEMMMd": "EEE, d. MMM", "at": " 'um' "},
    "fr": {"full": "EEEE d MMMM y", "long": "d MMMM y", "medium": "d MMM y", "short": "dd/MM/y",
           "MMMMd": "d MMMM", "MMMd": "d MMM", "Md": "dd/MM", "yMd": "dd/MM/y", "MMMMy": "MMMM y", "MMMy": "MMM y",
           "EEEEMMMMd": "EEEE d MMMM", "EEEMMMd": "EEE d MMM", "at": " 'à' "},
    "it": {"full": "EEEE d MMMM y", "long": "d MMMM y", "medium": "d MMM y", "short": "dd/MM/yy",
           "MMMMd": "d MMMM", "MMMd": "d MMM", "Md": "d/M", "yMd": "d/M/y", "MMMMy": "MMMM y", "MMMy": "MMM y",
           "EEEEMMMMd": "EEEE d MMMM", "EEEMMMd": "EEE d MMM", "at": " 'alle ore' "},
    "nl": {"full": "EEEE d MMMM y", "long": "d MMMM y", "medium": "d MMM y", "short": "dd-MM-y",
           "MMMMd": "d MMMM", "MMMd": "d MMM", "Md": "d-M", "yMd": "d-M-y", "MMMMy": "MMMM y", "MMMy": "MMM y",
           "EEEEMMMMd": "EEEE d MMMM", "EEEMMMd": "EEE d MMM", "at": " 'om' "},
    "ja": {"full": "y年M月d日EEEE", "long": "y年M月d日", "medium": "y/MM/dd", "short": "y/MM/dd",
           "MMMMd": "M月d日", "MMMd": "M月d日", "Md": "M/d", "yMd": "y/M/d", "MMMMy": "y年M月", "MMMy": "y年M月",
           "EEEEMMMMd": "M月d日EEEE", "EEEMMMd": "M月d日(EEE)", "at": " "},
    "zh": {"full": "y年M月d日EEEE", "long": "y年M月d日", "medium": "y年M月d日", "short": "y/M/d",
           "MMMMd": "M月d日", "MMMd": "M月d日", "Md": "M/d", "yMd": "y/M/d", "MMMMy": "y年M月", "MMMy": "y年M月",
           "EEEEMMMMd": "M月d日EEEE", "EEEMMMd": "M月d日EEE", "at": " "},
    "zh-HK": {"full": "y年M月d日EEEE", "long": "y年M月d日", "medium": "y年M月d日", "short": "d/M/y",
              "MMMMd": "M月d日", "MMMd": "M月d日", "Md": "d/M", "yMd": "d/M/y", "MMMMy": "y年M月", "MMMy": "y年M月",
              "EEEEMMMMd": "M月d日EEEE", "EEEMMMd": "M月d日EEE", "at": " "},
    "ko": {"full": "y년 MMMM d일 EEEE", "long": "y년 MMMM d일", "medium": "y. M. d.", "short": "yy. M. d.",
           "MMMMd": "MMMM d일", "MMMd": "MMM d일", "Md": "M. d.", "yMd": "y. M. d.", "MMMMy": "y년 MMMM",
           "MMMy": "y년 MMM", "EEEEMMMMd": "MMMM d일 EEEE", "EEEMMMd": "MMM d일 EEE", "at": " "},
}
PATTERNS["zh-MO"] = PATTERNS["zh-HK"]
PATTERNS["fr-CA"] = dict(PATTERNS["fr"], short="y-MM-dd", yMd="y-MM-dd", Md="MM-dd")
PATTERNS["fr-CH"] = dict(PATTERNS["fr"], short="dd.MM.yy", yMd="dd.MM.y", Md="dd.MM.")
PATTERNS["de-CH"] = PATTERNS["de-AT"] = PATTERNS["de-LU"] = PATTERNS["de"]
PATTERNS["es-MX"] = dict(PATTERNS["es"], short="dd/MM/yy")
PATTERNS["es-CO"] = PATTERNS["es-CL"] = dict(PATTERNS["es"], short="dd-MM-yy", yMd="d-M-y", Md="d-M")
PATTERNS["es-PR"] = PATTERNS["es-US"] = dict(PATTERNS["es"], short="MM/dd/yy", yMd="M/d/y", Md="M/d")

# Numeric date order for languages without name tables: (medium, short, Md).
NUMERIC = {
    "cs": ("d. M. y", "dd.MM.yy", "d. M."), "sk": ("d. M. y", "d. M. y", "d. M."),
    "sl": ("d. M. y", "d. M. yy", "d. M."), "hr": ("d. M. y.", "dd. MM. y.", "dd. MM."),
    "da": ("d. MMM y", "dd.MM.y", "d.M"), "nb": ("d. MMM y", "dd.MM.y", "d.M."),
    "pl": ("d MMM y", "d.MM.y", "d.MM"), "ro": ("d MMM y", "dd.MM.y", "dd.MM"),
    "fi": ("d.M.y", "d.M.y", "d.M."), "et": ("d. MMM y", "dd.MM.yy", "d.M"),
    "lv": ("y. 'gada' d. MMM", "dd.MM.yy", "dd.MM."), "lt": ("y-MM-dd", "y-MM-dd", "MM-d"),
    "is": ("d. MMM y", "d.M.y", "d.M."), "hu": ("y. MMM d.", "y. MM. dd.", "M. d."),
    "sv": ("d MMM y", "y-MM-dd", "d/M"), "tr": ("d MMM y", "d.MM.y", "dd/MM"),
    "el": ("d MMM y", "d/M/yy", "d/M"), "he": ("d MMM y", "d.M.y", "d.M"),
    "ar": ("dd/MM/y", "d/M/y", "d/M"), "hi": ("d MMM y", "d/M/yy", "d/M"), "th": ("d MMM y", "d/M/yy", "d/M"),
}

# Locales that use a 12 hour clock by default, and how they write the day period.
_12H = {"en-US": ("AM", "PM"), "en-CA": ("a.m.", "p.m."), "en-PR": ("AM", "PM"), "en-PH": ("AM", "PM"),
        "en-AU": ("am", "pm"), "en-NZ": ("am", "pm"), "en-IN": ("am", "pm"), "en-MY": ("am", "pm"),
        "en-SG": ("am", "pm"), "en-HK": ("am", "pm"), "en-MO": ("am", "pm"), "en-AE": ("AM", "PM"),
        "en-JO": ("AM", "PM"), "en-QA": ("AM", "PM"), "en-SA": ("AM", "PM"), "en-TH": ("AM", "PM"),
        "es-US": ("a.\u00a0m.", "p.\u00a0m."), "es-PR": ("a.\u00a0m.", "p.\u00a0m."),
        "es-CO": ("a.\u00a0m.", "p.\u00a0m."), "hi": ("am", "pm"), "ar": ("ص", "م"),
        "ko": ("오전", "오후"), "zh-TW": ("上午", "下午"), "zh-HK": ("上午", "下午"), "zh-MO": ("上午", "下午")}
_TIME_12 = {"ko": "a h:mm", "zh": "ah:mm"}
_TIME_24 = {"fi": "H.mm", "da": "HH.mm", "ja": "H:mm", "es": "H:mm", "fr-CA": "HH 'h' mm", "zh": "HH:mm"}

_DEFAULT_ZONE: Optional[str] = None


def set_default_time_zone(name: Optional[str]) -> None:
    """The zone a call without `timeZone` uses (the device's zone when None)."""
    global _DEFAULT_ZONE
    _DEFAULT_ZONE = name


def _split(locale: str) -> Tuple[str, str]:
    parts = (locale or "en-US").replace("_", "-").split("-")
    lang = parts[0].lower()
    region = next((p.upper() for p in parts[1:] if (len(p) == 2 and p.isalpha()) or p.isdigit()), "")
    return lang, ("%s-%s" % (lang, region) if region else lang)


def _lookup(table: Dict[str, Any], locale: str) -> Any:
    lang, tag = _split(locale)
    return table.get(tag, table.get(lang))


def zone(name: Optional[str]) -> tzinfo:
    """A tzinfo for an IANA name. Falls back to the device's local offset when the name is unknown or the
    platform ships no zone database (Android keeps it in a format zoneinfo cannot read)."""
    if name in ("UTC", "Etc/UTC", "GMT", "Z"):
        return timezone.utc
    if name:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except Exception:  # noqa: BLE001
            pass
    local = datetime.now().astimezone().tzinfo
    return local or timezone.utc


def to_datetime(value: Any) -> datetime:
    """A datetime from a datetime, a date, an ISO 8601 string ("2026-10-30T15:04:00Z") or epoch seconds.
    A naive datetime is taken as UTC, as an ISO string without an offset is in the API."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, timezone.utc)
    elif isinstance(value, str):
        s = value.strip()
        if s.endswith("Z") or s.endswith("z"):
            s = s[:-1] + "+00:00"
        m = re.match(r"^(.*T\d\d:\d\d:\d\d)\.(\d+)(.*)$", s)
        if m:  # Python 3.9 reads only 3 or 6 fraction digits
            s = "%s.%s%s" % (m.group(1), (m.group(2) + "000000")[:6], m.group(3))
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            raise ValueError("not an ISO 8601 date: %r" % (value,))
    else:
        raise TypeError("cannot format %r as a date" % (value,))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _opt(opts: Dict[str, Any], camel: str) -> Any:
    snake = "".join("_" + c.lower() if c.isupper() else c for c in camel)
    return opts.get(camel, opts.get(snake))


_TOKEN = re.compile(r"'[^']*'|y+|M+|d+|E+|h+|H+|m+|s+|a")


def _render(pattern: str, dt: datetime, locale: str, period: Tuple[str, str]) -> str:
    lang, _ = _split(locale)
    names = _lookup(NAMES, locale) or NAMES["en"]
    year = dt.year + (543 if lang == "th" else 0)

    def sub(m: "re.Match[str]") -> str:
        tok = m.group(0)
        c, n = tok[0], len(tok)
        if c == "'":
            return tok[1:-1]
        if c == "y":
            return "%02d" % (year % 100) if n == 2 else str(year)
        if c == "M":
            if n >= 3:
                return names["MMMM" if n == 4 else "MMM"][dt.month - 1]
            return "%02d" % dt.month if n == 2 else str(dt.month)
        if c == "d":
            return "%02d" % dt.day if n == 2 else str(dt.day)
        if c == "E":
            return names["EEEE" if n == 4 else "EEE"][dt.weekday()]
        if c == "h":
            h = dt.hour % 12 or 12
            return "%02d" % h if n == 2 else str(h)
        if c == "H":
            return "%02d" % dt.hour if n == 2 else str(dt.hour)
        if c == "m":
            return "%02d" % dt.minute
        if c == "s":
            return "%02d" % dt.second
        return period[0 if dt.hour < 12 else 1]
    return _TOKEN.sub(sub, pattern)


def _date_patterns(locale: str) -> Dict[str, str]:
    found = _lookup(PATTERNS, locale)
    if found:
        return found
    lang, _ = _split(locale)
    num = NUMERIC.get(lang)
    if not num:
        return _GB
    medium, short, md = num
    return dict(_GB, medium=medium, short=short, Md=md, yMd=short.replace("yy", "y") if "yy" in short else short,
                at=", ")


def _time_pattern(locale: str, seconds: bool, hour12: Optional[bool]) -> Tuple[str, Tuple[str, str]]:
    lang, tag = _split(locale)
    period = _12H.get(tag) or _12H.get(lang)
    twelve = bool(period) if hour12 is None else hour12
    if twelve:
        period = period or ("AM", "PM")
        pat = _TIME_12.get(lang, "h:mm\u202fa" if lang == "en" and tag in ("en-US", "en-CA", "en-PR", "en-PH")
                           else "h:mm a")
    else:
        period = period or ("AM", "PM")
        pat = _TIME_24.get(tag) or _TIME_24.get(lang) or "HH:mm"
    if seconds:
        pat = pat.replace("mm", "mm:ss", 1).replace("H.mm:ss", "H.mm.ss").replace("HH.mm:ss", "HH.mm.ss")
    return pat, period


def _date_key(month: Optional[str], day: bool, year: bool, weekday: Optional[str]) -> Optional[str]:
    if month in ("long", "short", "narrow"):
        m = "MMMM" if month == "long" else "MMM"
        if day and year:
            return ("full" if weekday else "long") if m == "MMMM" else "medium"
        if day:
            return ("EEEE" if weekday == "long" else "EEE") + "MMMMd" if weekday and m == "MMMM" else \
                ("EEEMMMd" if weekday else m + "d")
        if year:
            return m + "y"
        return m
    if month:
        if day:
            return "yMd" if year else "Md"
        return "yM" if year else "M"
    if day:
        return "d"
    if year:
        return "y"
    return None


def format_datetime(value: Any, locale: str = "en-US", **opts: Any) -> str:
    """Formats a datetime, date, ISO string or epoch seconds for `locale`. See the module doc for options."""
    dt = to_datetime(value)
    tz_name = _opt(opts, "timeZone") or _DEFAULT_ZONE
    if not isinstance(value, date) or isinstance(value, datetime) or tz_name:
        dt = dt.astimezone(zone(tz_name))
    pats = _date_patterns(locale)
    date_style, time_style = _opt(opts, "dateStyle"), _opt(opts, "timeStyle")
    hour12 = _opt(opts, "hour12")
    _, period = _time_pattern(locale, False, hour12)
    date_pat = time_pat = None
    if date_style or time_style:
        if date_style:
            if date_style not in ("full", "long", "medium", "short"):
                raise ValueError("dateStyle must be full, long, medium or short")
            date_pat = pats[date_style]
        if time_style:
            if time_style not in ("full", "long", "medium", "short"):
                raise ValueError("timeStyle must be full, long, medium or short")
            time_pat, period = _time_pattern(locale, time_style != "short", hour12)
        joiner = pats.get("at", ", ") if date_style in ("full", "long") else ", "
    else:
        weekday, month = _opt(opts, "weekday"), _opt(opts, "month")
        day, year = _opt(opts, "day"), _opt(opts, "year")
        hour, minute, second = _opt(opts, "hour"), _opt(opts, "minute"), _opt(opts, "second")
        if not any((weekday, month, day, year, hour, minute, second)):
            year = month = day = "numeric"
        key = _date_key(month, bool(day), bool(year), weekday)
        if key in ("yM", "M", "d", "y", "MMMM", "MMM"):
            date_pat = {"yM": pats["yMd"].replace("d", "").strip("/.- "), "M": "M", "d": "d", "y": "y",
                        "MMMM": "MMMM", "MMM": "MMM"}[key]
            if key == "yM":
                date_pat = re.sub(r"([/.\-])\1+", r"\1", date_pat)
        elif key:
            date_pat = pats[key]
            if month == "2-digit":
                date_pat = date_pat.replace("M", "MM") if "MM" not in date_pat else date_pat
            if day == "2-digit":
                date_pat = re.sub(r"(?<!d)d(?!d)", "dd", date_pat)
            if weekday and key in ("full",) and weekday == "short":
                date_pat = date_pat.replace("EEEE", "EEE")
        if weekday and not key:
            date_pat = "EEEE" if weekday == "long" else "EEE"
        if weekday and key in ("Md", "yMd"):
            date_pat = ("EEEE" if weekday == "long" else "EEE") + ", " + date_pat
        if hour or minute or second:
            time_pat, period = _time_pattern(locale, bool(second), hour12)
            if hour and not minute:
                time_pat = re.sub(r"[:.]mm(:ss|\.ss)?", "", time_pat).replace(" 'h' ", "")
            if hour == "2-digit":
                time_pat = time_pat.replace("h:", "hh:").replace("H:", "HH:")
        joiner = ", "
    parts = [p for p in (date_pat, time_pat) if p]
    pattern = joiner.join(parts) if len(parts) == 2 else parts[0]
    return _render(pattern, dt, locale, period)


def format_date_range(start: Any, end: Any, locale: str = "en-US", **opts: Any) -> str:
    """Two dates joined with an en dash, each formatted with the same options."""
    return "%s\u2009\u2013\u2009%s" % (format_datetime(start, locale, **opts), format_datetime(end, locale, **opts))


def days_between(a: Any, b: Any) -> int:
    """Whole days from `a` to `b` (negative when `b` is earlier), by UTC calendar date."""
    da, db = to_datetime(a).astimezone(timezone.utc).date(), to_datetime(b).astimezone(timezone.utc).date()
    return (db - da) // timedelta(days=1)
