# pyxpo-intl

[![CI](https://github.com/pyxpo/pyxpo-intl/actions/workflows/ci.yml/badge.svg)](https://github.com/pyxpo/pyxpo-intl/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/pyxpo-intl)](https://pypi.org/project/pyxpo-intl/) [![Python](https://img.shields.io/pypi/pyversions/pyxpo-intl)](https://pypi.org/project/pyxpo-intl/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Translations and locale formatting for [pyxpo](https://github.com/pyxpo/pyxpo) apps, written in pure Python:
[ICU MessageFormat](https://unicode-org.github.io/icu/userguide/format_parse/messages/) messages with plurals,
selects and rich-text tags, the CLDR plural rules, and the parts of JavaScript's `Intl.NumberFormat` and
`Intl.DateTimeFormat` that apps use. It reads the same message catalogs as
[next-intl](https://next-intl.dev) and [use-intl](https://www.npmjs.com/package/use-intl), so a web app and a pyxpo
app can share one set of JSON files.

<p align="center">
  <img src="https://raw.githubusercontent.com/pyxpo/pyxpo-intl/main/docs/images/hero.png" width="820" alt="The same screen in English, Spanish and German on Android and iOS: plurals, numbers and dates in each language">
</p>

```python
from pyxpo_intl import create_translator, format_number

t = create_translator({"posts": {"count": "{n, plural, =0 {No posts} one {# post} other {# posts}}"}}, "posts")
t("count", {"n": 3})               # "3 posts"
format_number(1234.5, "de-DE")     # "1.234,5"
```

## Features

- **ICU messages:** `{name}` placeholders, `plural` (with `=0`, `=-1`, `offset:` and `#`), `selectordinal`,
  `select`, `{n, number}`, `{n, number, percent}`, `{n, number, ::currency/EUR}`, `{d, date, medium}` and
  `{t, time, short}`.
- **Rich text:** `<b>bold</b>` and `<link>terms</link>` tags call a function you pass, which can return any
  object, such as a pyxpo `Text`.
- **CLDR plural rules** for about 60 languages, including Arabic, Polish, Czech, Russian and Hebrew.
- **Numbers:** grouping and decimal marks, Indian grouping (`12,34,567`), percent, currency, compact (`15K`),
  fraction and integer digits, sign display, and Arabic-Indic digits.
- **Dates:** `dateStyle`/`timeStyle`, or parts (`weekday`, `day`, `month`, `year`, `hour`, `minute`), in any IANA
  time zone. Month and weekday names for English, Spanish, Portuguese, German, French, Italian, Dutch, Japanese,
  Chinese and Korean.
- **Catalogs:** nested JSON, dotted keys, deep merge for fallbacks (`with_fallback`), and missing keys that show
  their path instead of crashing.
- **Hooks:** `IntlProvider`, `use_translations()`, `use_formatter()` and `use_locale()`.
- **No native code, no data download, no dependencies** besides pyxpo. Works the same on Android, iOS, web and
  desktop, and in plain Python tests.
- **Typed:** ships `py.typed`.

## Contents

| If you are... | Start here |
| --- | --- |
| Translating an app | [Quick start](#quick-start) → [Messages](#messages) |
| Showing "1 post" and "2 posts" right in every language | [Plurals](#plurals) |
| Formatting money, percents or counts | [Numbers](#numbers) |
| Showing dates in the user's style and time zone | [Dates](#dates) |
| Putting links or bold text inside a sentence | [Rich text](#rich-text) |
| Looking for exact signatures | [API reference](#api-reference) · [Errors](#errors) |
| Seeing it in a real app | [Recipe: a language picker](#recipe-a-language-picker) |
| Stuck | [Testing](#testing) · [Troubleshooting](#troubleshooting) · [FAQ](#faq) |

## Platform support

| Target | What works |
| --- | --- |
| Android, API 24+ | Everything. Named time zones fall back to the device's offset, because Android's zone database is not in the format Python reads. |
| iOS 15+ | Everything. |
| Web page and desktop window (`pyxpo run web` / `pyxpo run desktop`) | Everything. |

Requires Python 3.9+ and `pyxpo>=0.1.0a2`.

## Install

```sh
pip install pyxpo-intl
```

Add the module to your app's `pyproject.toml`, so the build bundles its Python files:

```toml
[tool.pyxpo]
modules = ["intl"]
```

The module has no native code and no config plugin. Rebuild once after adding it (`pyxpo run android` or
`pyxpo run ios`); after that, hot reload picks up message changes.

## Quick start

```python
import json
from pathlib import Path

from pyxpo import Text, View, component, use_state
from pyxpo_intl import IntlProvider, use_formatter, use_translations

MESSAGES = {
    "en": {"home": {"greeting": "Hello {name}", "posts": "{n, plural, one {# post} other {# posts}}"}},
    "es": {"home": {"greeting": "Hola {name}", "posts": "{n, plural, one {# artículo} other {# artículos}}"}},
}


@component
def Home():
    t = use_translations("home")
    fmt = use_formatter()
    return View(
        Text(t("greeting", {"name": "Ana"})),
        Text(t("posts", {"n": 1234})),
        Text(fmt.date_time("2026-10-30T15:04:00Z", dateStyle="medium")),
    )


@component
def App():
    locale, set_locale = use_state("es-ES")
    return IntlProvider(Home(), locale=locale, messages=MESSAGES[locale[:2]], time_zone="Europe/Madrid")
```

With `es-ES` this shows "Hola Ana", "1234 artículos" (Spain does not group four-digit numbers) and "30 oct 2026".

## Messages

Messages live in nested dicts, usually loaded from one JSON file per language. A translator reads one namespace:

```python
from pyxpo_intl import create_translator

messages = {"settings": {"title": "Settings", "language": {"label": "Language: {name}"}}}
t = create_translator(messages, "settings", locale="en-US")
t("title")                              # "Settings"
t("language.label", {"name": "English"})  # "Language: English"
t("nope")                               # "settings.nope"
t.has("title"), t.raw("language")       # True, {"label": "Language: {name}"}
```

| Syntax | Example | Result |
| --- | --- | --- |
| Placeholder | `Hello {name}` | `Hello Ana` |
| Number | `{n, number}` | `1,234.5` |
| Percent | `{n, number, percent}` | `25%` |
| Skeleton | `{n, number, ::currency/EUR}`, `::percent`, `::compact-short`, `::.00` | `€3.00` |
| Date / time | `{d, date, medium}`, `{d, time, short}` | `Oct 30, 2026`, `3:04 PM` |
| Plural | `{n, plural, =0 {none} one {# item} other {# items}}` | `3 items` |
| Ordinal | `{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}` | `22nd` |
| Select | `{role, select, owner {Owner} other {Member}}` | `Member` |
| Tag | `Read <b>this</b>` | see [Rich text](#rich-text) |

Quoting follows ICU's optional-apostrophe rule: `''` is a literal apostrophe, and a single `'` quotes text only
right before `{`, `}`, `#`, `<` or `>`. So `Don't` needs no escaping, and `'{name}'` prints `{name}`.

A missing value stays as its placeholder (`Hello {name}`), so a mistake shows on screen instead of crashing.

## Plurals

`plural` picks the option for the number's CLDR category in the translator's locale. `=N` options match an exact
number first. `#` prints the number formatted for the locale.

```python
from pyxpo_intl import format_message, plural_category

plural_category(1, "en"), plural_category(0, "fr"), plural_category(3, "pl")   # "one", "one", "few"
msg = "{n, plural, one {# plik} few {# pliki} many {# plików} other {# pliku}}"
format_message(msg, {"n": 5}, "pl-PL")                                         # "5 plików"
```

Pass a string to keep trailing zeros (`"1.0"` is "other" in English, `1` is "one").

## Numbers

```python
from pyxpo_intl import format_number

format_number(1234567, "en-IN")                                       # "12,34,567"
format_number(0.2567, "fr-FR", style="percent", maximumFractionDigits=1)  # "25,7 %"
format_number(12.5, "de-DE", style="currency", currency="EUR")        # "12,50 €"
format_number(15300, "en-US", notation="compact")                     # "15K"
```

| Option | Values | Default |
| --- | --- | --- |
| `style` | `"decimal"`, `"percent"`, `"currency"` | `"decimal"` |
| `currency` | ISO code, needed for `"currency"` | |
| `notation` | `"standard"`, `"compact"` | `"standard"` |
| `minimumFractionDigits`, `maximumFractionDigits` | 0 to 100 | 0 and 3; percent 0 and 0; currency 2 and 2 |
| `minimumIntegerDigits` | 1+ | 1 |
| `useGrouping` | `True`, `False` | `True` |
| `signDisplay` | `"auto"`, `"always"`, `"exceptZero"`, `"never"` | `"auto"` |

Options use the JavaScript names; the snake_case names (`maximum_fraction_digits`) work too. Rounding is half away
from zero, as in JavaScript. The separators follow CLDR as browsers ship it, so the output matches
`Intl.NumberFormat` byte for byte, including the no-break spaces in French and German.

## Dates

```python
from pyxpo_intl import format_datetime

when = "2026-10-30T15:04:00Z"
format_datetime(when, "en-US", dateStyle="medium", timeStyle="short", timeZone="UTC")  # "Oct 30, 2026, 3:04 PM"
format_datetime(when, "pt-BR", weekday="long", day="numeric", month="long")           # "sexta-feira, 30 de outubro"
format_datetime(when, "de-DE", day="numeric", month="short")                          # "30. Okt."
```

The value can be a `datetime`, a `date`, an ISO 8601 string (with `Z` or an offset) or epoch seconds. A naive
value is UTC.

| Option | Values |
| --- | --- |
| `dateStyle`, `timeStyle` | `"full"`, `"long"`, `"medium"`, `"short"` |
| `weekday` | `"long"`, `"short"` |
| `year`, `day`, `hour`, `minute`, `second` | `"numeric"`, `"2-digit"` |
| `month` | `"numeric"`, `"2-digit"`, `"long"`, `"short"` |
| `hour12` | `True`, `False` (default: the locale's clock) |
| `timeZone` | IANA name, such as `"Asia/Kolkata"` (default: `set_default_time_zone()`, then the device) |

`format_date_range(start, end, locale, **opts)` joins two dates with an en dash. `days_between(a, b)` counts UTC
calendar days.

## Rich text

A tag calls the value with the same name, passing its formatted children as a list. Use `t.rich` (or
`format_rich`) to get a list of parts instead of a string, so the callback can return components:

```python
from pyxpo import Text, component
from pyxpo_intl import use_translations


@component
def Consent(open_terms):
    t = use_translations("signup")   # "consent": "I agree to the <terms>terms</terms>."
    parts = t.rich("consent", {"terms": lambda kids: Text(*kids, on_press=open_terms, style={"color": "#2563eb"})})
    return Text(*parts)
```

A tag with no callback keeps its text. Self-closing tags (`<br/>`) are allowed.

## Errors

| Error | When | What to do |
| --- | --- | --- |
| `MessageError` | A message does not parse: an unclosed `{`, a `plural` with no `other`, a closing tag with no opening tag | Fix the message. The error names the position. |
| `ValueError` | `style="currency"` without `currency`, impossible fraction digits, an unknown `dateStyle`, a string that is not ISO 8601 | Fix the arguments. |
| `TypeError` | A date value that is not a date, string or number | Convert it first. |

A missing key or value never raises: the key path or the `{placeholder}` shows instead. Pass
`on_missing=callback` to `create_translator` to log them.

## Web and desktop

The same code runs on every target, because nothing calls the platform. The default time zone comes from the
system; set it with `set_default_time_zone("Asia/Kolkata")` or the `time_zone` prop on `IntlProvider`.

## Recipe: a language picker

Pair it with [pyxpo-localization](https://github.com/pyxpo/pyxpo-localization) to start in the device's language
and let the user change it:

```python
import json
from pathlib import Path

from pyxpo import Pressable, Text, View, component, use_memo, use_state
import pyxpo_localization as Localization
from pyxpo_intl import IntlProvider, use_translations, with_fallback

HERE = Path(__file__).parent
EN = json.loads((HERE / "messages" / "en.json").read_text())


def load(language):
    path = HERE / "messages" / ("%s.json" % language)
    return with_fallback(EN, json.loads(path.read_text())) if path.exists() else EN


@component
def Picker(on_pick):
    t = use_translations("settings")
    return View(
        Text(t("language")),
        *[Pressable(Text(name), key=tag, on_press=lambda tag=tag: on_pick(tag))
          for tag, name in [("en-US", "English"), ("es-ES", "Español"), ("de-DE", "Deutsch")]],
    )


@component
def App():
    device = Localization.get_locales()[0].language_tag
    locale, set_locale = use_state(device)
    messages = use_memo(lambda: load(locale.split("-")[0]), [locale])
    return IntlProvider(Picker(set_locale), locale=locale, messages=messages)
```

`with_fallback` fills keys a translation has not done yet from English.

## Production checklist

- Keep one JSON file per language and merge each over English with `with_fallback`.
- Pass `on_missing` in debug builds and log the paths.
- Give `IntlProvider` the user's time zone when dates matter (the server's UTC is rarely what users expect).
- Test plurals with 0, 1, 2, 5 and 21: those cover the categories of most languages.
- For right-to-left languages, flip layout with `I18nManager` as well; this module only formats text.

## Testing

Everything is plain Python, so unit tests need no fake:

```python
from pyxpo_intl import create_translator


def test_plan_limit():
    t = create_translator({"ai": {"limit": "{n, plural, one {# post} other {# posts}}"}}, "ai", "en-US")
    assert t("limit", {"n": 1}) == "1 post"
```

For components, render them under an `IntlProvider` with the mock renderer.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| The screen shows `home.title` | The key is missing from the catalog, or the namespace is wrong. |
| The screen shows `{name}` | The value was not passed, or its name is spelled differently. |
| A time is off by hours on Android | Android has no zone database Python can read; the device's offset is used. Format in `"UTC"` or pass times already in local time. |
| `MessageError: expected '}'` | An apostrophe before `{` quotes it. Write `''` for a literal apostrophe there. |
| A space looks different from what you typed | French, German and others use no-break spaces, as browsers do. Compare against `" "` and `" "` in tests. |

## FAQ

**Is this the full ICU?** No. It covers the message syntax and the number and date options apps use. Exotic
calendars, `spellout`, and number skeletons beyond currency, percent, compact and fraction digits are not there.

**Which languages have month names?** English, Spanish, Portuguese, German, French, Italian, Dutch, Japanese,
Chinese and Korean. Other languages get their own numeric order and English names for `month="long"`.

**Can I use my next-intl JSON files?** Yes. The syntax and the nested layout are the same.

## API reference

| Name | Purpose |
| --- | --- |
| `format_message(msg, values=None, locale="en-US", time_zone=None) -> str` | Formats one ICU message. |
| `format_rich(msg, values=None, locale="en-US", time_zone=None) -> list` | Same, as a list of parts with tag results. |
| `parse(msg) -> list` | The cached parsed form. |
| `plural_category(value, locale="en") -> str` | `"zero"`, `"one"`, `"two"`, `"few"`, `"many"` or `"other"`. |
| `format_number(value, locale="en-US", **opts) -> str` | See [Numbers](#numbers). |
| `symbols_for(locale) -> Symbols` | Decimal and group marks, percent and currency patterns. |
| `format_datetime(value, locale="en-US", **opts) -> str` | See [Dates](#dates). |
| `format_date_range(start, end, locale="en-US", **opts) -> str` | Two dates joined with an en dash. |
| `days_between(a, b) -> int` | Whole UTC days from `a` to `b`. |
| `to_datetime(value) -> datetime` | An aware datetime from any accepted input. |
| `set_default_time_zone(name)` | The zone for calls without `timeZone`. |
| `create_translator(messages, namespace=None, locale="en-US", time_zone=None, on_missing=None) -> Translator` | A translator. |
| `Translator(key, values)`, `.rich`, `.has`, `.raw`, `.namespaced` | Format, parts, check, read, narrow. |
| `Formatter(locale, time_zone)`, `.number`, `.date_time` (`.dateTime`) | Formatting bound to one locale. |
| `lookup(messages, path)` | The value at a dotted path. |
| `with_fallback(base, over) -> dict` | Deep merge; lists replace whole. |
| `IntlProvider(*children, locale, messages, time_zone)` | Puts the locale in context. |
| `use_translations(namespace=None)`, `use_formatter()`, `use_locale()`, `use_intl()` | Read it in components. |

## License

MIT. See [LICENSE](LICENSE).
