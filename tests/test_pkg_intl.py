"""pyxpo-intl: plural rules, number and date formatting, ICU messages, translators and the pyxpo provider."""
from datetime import datetime, timezone

import pytest

from pyxpo_intl import (Formatter, MessageError, create_translator, days_between, format_datetime, format_message,
                        format_number, format_rich, plural_category, with_fallback)

WHEN = datetime(2026, 10, 30, 15, 4, tzinfo=timezone.utc)


@pytest.mark.parametrize("value,locale,want", [
    (1, "en-US", "one"), (1.5, "en-US", "other"), (0, "en", "other"), ("1.0", "en", "other"),
    (1, "es-ES", "one"), (1000000, "es", "many"), (0, "pt-BR", "one"), (0, "pt-PT", "other"),
    (1, "fr", "one"), (1.5, "fr", "one"), (2, "fr", "other"),
    (3, "pl", "few"), (5, "pl", "many"), (22, "pl", "few"), (12, "pl", "many"),
    (0, "ar", "zero"), (2, "ar", "two"), (5, "ar", "few"), (11, "ar", "many"), (100, "ar", "other"),
    (2, "cs", "few"), (1.5, "cs", "many"), (21, "ru", "one"), (11, "ru", "many"),
    (1, "ja", "other"), (1, "xx", "one"), (2, "he", "two"), (0, "hi", "one"),
])
def test_plural(value, locale, want):
    assert plural_category(value, locale) == want


@pytest.mark.parametrize("value,locale,opts,want", [
    (1234.5, "en-US", {}, "1,234.5"),
    (1234.5, "de-DE", {}, "1.234,5"),
    (1234, "es-ES", {}, "1234"),
    (12345, "es-ES", {}, "12.345"),
    (1234567, "en-IN", {}, "12,34,567"),
    (1234.5, "fr-FR", {}, "1 234,5"),
    (1234.5, "de-CH", {}, "1’234.5"),
    (0.256, "en-US", {"style": "percent"}, "26%"),
    (0.2567, "de-DE", {"style": "percent", "maximumFractionDigits": 1}, "25,7 %"),
    (12.5, "en-US", {"style": "currency", "currency": "USD"}, "$12.50"),
    (12.5, "de-DE", {"style": "currency", "currency": "EUR"}, "12,50 €"),
    (1500, "ja-JP", {"style": "currency", "currency": "JPY"}, "¥1,500"),
    (15300, "en-US", {"notation": "compact"}, "15K"),
    (1530, "en-US", {"notation": "compact"}, "1.5K"),
    (2.5, "en-US", {"maximumFractionDigits": 0}, "3"),
    (-2.5, "en-US", {"maximumFractionDigits": 0}, "-3"),
    (5, "en-US", {"minimumIntegerDigits": 2}, "05"),
    (3, "en-US", {"signDisplay": "always"}, "+3"),
    (0, "en-US", {"signDisplay": "exceptZero"}, "0"),
    (1234, "en-US", {"use_grouping": False}, "1234"),
    (1234.5, "ar-SA", {}, "١٬٢٣٤٫٥"),
    (1234.5, "ar-AE", {}, "1,234.5"),
])
def test_number(value, locale, opts, want):
    assert format_number(value, locale, **opts) == want


def test_number_errors():
    with pytest.raises(ValueError):
        format_number(1, style="currency")
    assert format_number(float("nan")) == "NaN"


@pytest.mark.parametrize("locale,opts,want", [
    ("en-US", {"dateStyle": "medium"}, "Oct 30, 2026"),
    ("en-GB", {"dateStyle": "medium"}, "30 Oct 2026"),
    ("es-ES", {"dateStyle": "medium"}, "30 oct 2026"),
    ("pt-BR", {"dateStyle": "medium"}, "30 de out. de 2026"),
    ("de-DE", {"dateStyle": "medium"}, "30.10.2026"),
    ("en-US", {"dateStyle": "medium", "timeStyle": "short"}, "Oct 30, 2026, 3:04 PM"),
    ("en-GB", {"dateStyle": "medium", "timeStyle": "short"}, "30 Oct 2026, 15:04"),
    ("en-US", {"weekday": "long", "day": "numeric", "month": "long"}, "Friday, October 30"),
    ("en-GB", {"weekday": "long", "day": "numeric", "month": "long"}, "Friday 30 October"),
    ("es-ES", {"weekday": "long", "day": "numeric", "month": "long"}, "viernes, 30 de octubre"),
    ("pt-BR", {"weekday": "long", "day": "numeric", "month": "long"}, "sexta-feira, 30 de outubro"),
    ("de-DE", {"weekday": "long", "day": "numeric", "month": "long"}, "Freitag, 30. Oktober"),
    ("en-US", {"day": "numeric", "month": "short"}, "Oct 30"),
    ("en-GB", {"day": "numeric", "month": "short"}, "30 Oct"),
    ("es-ES", {"day": "numeric", "month": "short"}, "30 oct"),
    ("pt-BR", {"day": "numeric", "month": "short"}, "30 de out."),
    ("de-DE", {"day": "numeric", "month": "short"}, "30. Okt."),
    ("en-US", {}, "10/30/2026"),
    ("en-US", {"dateStyle": "short"}, "10/30/26"),
    ("ja-JP", {"dateStyle": "long"}, "2026年10月30日"),
    ("th-TH", {"year": "numeric"}, "2569"),
    ("en-US", {"hour": "numeric", "minute": "2-digit"}, "3:04 PM"),
    ("en-US", {"month": "long", "year": "numeric"}, "October 2026"),
])
def test_dates(locale, opts, want):
    assert format_datetime(WHEN, locale, timeZone="UTC", **opts) == want


def test_date_inputs_and_zone():
    assert format_datetime("2026-10-30T15:04:00.123456789Z", "en-GB", timeZone="UTC", timeStyle="short") == "15:04"
    assert format_datetime(WHEN.timestamp(), "en-GB", timeZone="UTC", dateStyle="medium") == "30 Oct 2026"
    try:
        got = format_datetime(WHEN, "en-GB", timeZone="Asia/Kolkata", timeStyle="short")
    except Exception:  # noqa: BLE001
        pytest.skip("no zone database")
    assert got in ("20:34", format_datetime(WHEN.astimezone(), "en-GB", timeStyle="short"))
    assert days_between("2026-10-28T23:00:00Z", WHEN) == 2
    with pytest.raises(ValueError):
        format_datetime("yesterday")


PLURAL = "{count, plural, =0 {No posts} one {# post} other {# posts}}"


@pytest.mark.parametrize("msg,values,locale,want", [
    ("Hello {name}", {"name": "Ana"}, "en-US", "Hello Ana"),
    (PLURAL, {"count": 0}, "en-US", "No posts"),
    (PLURAL, {"count": 1}, "en-US", "1 post"),
    (PLURAL, {"count": 1234}, "de-DE", "1.234 posts"),
    ("{n, plural, =-1 {Unlimited} other {# left}}", {"n": -1}, "en", "Unlimited"),
    ("{g, select, female {She} male {He} other {They}} wrote", {"g": "x"}, "en", "They wrote"),
    ("{n, number, percent}", {"n": 0.25}, "de-DE", "25 %"),
    ("{n, number}", {"n": 1234.5}, "de-DE", "1.234,5"),
    ("{n, number, ::currency/USD}", {"n": 3}, "en-US", "$3.00"),
    ("{d, date, medium}", {"d": WHEN}, "en-GB", "30 Oct 2026"),
    ("{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}", {"n": 22}, "en", "22nd"),
    ("{n, plural, offset:1 =0 {nobody} =1 {you} one {you and # other} other {you and # others}}", {"n": 3}, "en",
     "you and 2 others"),
    ("Don't stop", {}, "en", "Don't stop"),
    ("It''s '{literal}' #", {}, "en", "It's {literal} #"),
    ("{n, plural, other {'#' is #}}", {"n": 5}, "en", "# is 5"),
    ("Missing {x}", {}, "en", "Missing {x}"),
    ("Read <b>this</b> and <terms>terms</terms>", {"b": lambda k: "*" + "".join(k) + "*"}, "en",
     "Read *this* and terms"),
    ("{n, plural, one {<b>#</b> item} other {<b>#</b> items}}", {"n": 2, "b": lambda k: "[%s]" % k[0]}, "en",
     "[2] items"),
])
def test_message(msg, values, locale, want):
    assert format_message(msg, values, locale) == want


def test_rich_keeps_objects():
    parts = format_rich("Accept <terms>the terms</terms>.", {"terms": lambda kids: ("Link", kids)})
    assert parts == ["Accept ", ("Link", ["the terms"]), "."]


@pytest.mark.parametrize("bad", ["{", "{n, plural, one {x}}", "</b>", "<b>x", "{n, bogus}"])
def test_message_errors(bad):
    with pytest.raises(MessageError):
        format_message(bad, {"n": 1})


ES = {"ai": {"writer": {"planLimit": "{count, plural, one {# artículo con IA al mes en tu plan} "
                                     "other {# artículos con IA al mes en tu plan}}"}},
      "dash": {"tabs": ["a", "b"]}}


def test_translator():
    t = create_translator(ES, "ai.writer", "es-ES")
    assert t("planLimit", {"count": 1}) == "1 artículo con IA al mes en tu plan"
    assert t("planLimit", {"count": 3}) == "3 artículos con IA al mes en tu plan"
    assert t("nope") == "ai.writer.nope"
    assert t.has("planLimit") and not t.has("nope")
    missing = []
    t2 = create_translator(ES, None, "es", on_missing=missing.append)
    assert t2.raw("dash.tabs") == ["a", "b"]
    t2("x.y")
    assert missing == ["x.y"]
    assert t2.namespaced("ai")("writer.planLimit", {"count": 1}).startswith("1 artículo")


def test_with_fallback():
    base = {"a": {"x": "1", "y": "2"}, "list": [1, 2, 3], "z": "base"}
    got = with_fallback(base, {"a": {"y": "two"}, "list": [9]})
    assert got == {"a": {"x": "1", "y": "two"}, "list": [9], "z": "base"}
    assert base["a"]["y"] == "2"


def test_formatter():
    fmt = Formatter("de-DE", "UTC")
    assert fmt.number(1234.5) == "1.234,5"
    assert fmt.dateTime("2026-10-30T15:04:00Z", dateStyle="medium") == "30.10.2026"


def test_provider():
    from pyxpo import LocalChannel, Text, component, create_app
    from pyxpo.renderers.mock import MockRenderer

    from pyxpo_intl import IntlProvider, use_formatter, use_locale, use_translations

    @component
    def Body():
        t = use_translations("ai.writer")
        return Text("%s|%s|%s" % (use_locale(), t("planLimit", {"count": 3}), use_formatter().number(1234.5)))

    @component
    def App():
        return IntlProvider(Body(), locale="es-ES", messages=ES)
    ch = LocalChannel()
    r = MockRenderer(ch)
    create_app(App, ch)
    assert r.texts() == ["es-ES|3 artículos con IA al mes en tu plan|1234,5"]
