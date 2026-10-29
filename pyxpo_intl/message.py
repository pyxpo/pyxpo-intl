"""ICU MessageFormat: placeholders, plural, selectordinal, select, number and date arguments, and rich-text tags.

    format_message("Hello {name}", {"name": "Ana"})                               # "Hello Ana"
    format_message("{count, plural, =0 {No posts} one {# post} other {# posts}}", {"count": 3})  # "3 posts"
    format_message("{n, number, percent}", {"n": 0.25}, "de-DE")                   # "25 %"
    format_message("Read the <link>terms</link>", {"link": lambda kids: "[" + "".join(kids) + "]"})

Quoting follows ICU's optional-apostrophe rule: '' is a literal apostrophe, and a single apostrophe starts
quoted text only right before { } # < or >. So "don't" needs no escaping.

`format_rich` returns a list of parts instead of a string, so a tag callback can return any object (a Text
node, for example). `format_message` joins the parts with str().
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, Union

from .dates import format_datetime
from .number import format_number
from .plural import plural_category

Node = Union[str, Tuple[Any, ...]]


class MessageError(ValueError):
    """A message that does not parse."""


_SPECIAL = "{}#<>"


class _Parser:
    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0

    def error(self, why: str) -> MessageError:
        return MessageError("%s at %d in %r" % (why, self.i, self.s))

    def parse(self) -> List[Node]:
        nodes = self.nodes(in_plural=False, until_tag=None)
        if self.i < len(self.s):
            raise self.error("unexpected %r" % self.s[self.i])
        return nodes

    def nodes(self, in_plural: bool, until_tag: Optional[str]) -> List[Node]:
        out: List[Node] = []
        buf: List[str] = []

        def flush() -> None:
            if buf:
                out.append("".join(buf))
                buf.clear()
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c == "'":
                nxt = s[self.i + 1] if self.i + 1 < len(s) else ""
                if nxt == "'":
                    buf.append("'")
                    self.i += 2
                elif nxt and nxt in _SPECIAL:
                    end = self.i + 1
                    chunk: List[str] = []
                    while end < len(s):
                        if s[end] == "'":
                            if end + 1 < len(s) and s[end + 1] == "'":
                                chunk.append("'")
                                end += 2
                                continue
                            break
                        chunk.append(s[end])
                        end += 1
                    buf.append("".join(chunk))
                    self.i = end + 1
                else:
                    buf.append("'")
                    self.i += 1
            elif c == "{":
                flush()
                out.append(self.argument(in_plural))
            elif c == "}":
                break
            elif c == "#" and in_plural:
                flush()
                out.append(("pound",))
                self.i += 1
            elif c == "<" and self._tag_ahead():
                if s.startswith("</", self.i):
                    if until_tag is None:
                        raise self.error("closing tag without an opening tag")
                    break
                flush()
                out.append(self.tag(in_plural))
            else:
                buf.append(c)
                self.i += 1
        flush()
        return out

    def _tag_ahead(self) -> bool:
        j = self.i + 1
        if j < len(self.s) and self.s[j] == "/":
            j += 1
        return j < len(self.s) and (self.s[j].isalpha() or self.s[j] == "_")

    def tag(self, in_plural: bool) -> Node:
        self.i += 1
        name = self.ident()
        self.space()
        if self.s.startswith("/>", self.i):
            self.i += 2
            return ("tag", name, [])
        if not self.s.startswith(">", self.i):
            raise self.error("expected > after <%s" % name)
        self.i += 1
        kids = self.nodes(in_plural, until_tag=name)
        close = "</%s>" % name
        if not self.s.startswith(close, self.i):
            raise self.error("expected %s" % close)
        self.i += len(close)
        return ("tag", name, kids)

    def space(self) -> None:
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def ident(self) -> str:
        start = self.i
        while self.i < len(self.s) and (self.s[self.i].isalnum() or self.s[self.i] in "_-."):
            self.i += 1
        if start == self.i:
            raise self.error("expected a name")
        return self.s[start:self.i]

    def expect(self, ch: str) -> None:
        self.space()
        if not self.s.startswith(ch, self.i):
            raise self.error("expected %r" % ch)
        self.i += 1

    def argument(self, in_plural: bool) -> Node:
        self.i += 1
        self.space()
        name = self.ident()
        self.space()
        if self.s.startswith("}", self.i):
            self.i += 1
            return ("arg", name)
        self.expect(",")
        self.space()
        kind = self.ident()
        self.space()
        if kind in ("number", "date", "time"):
            style = None
            if self.s.startswith(",", self.i):
                self.i += 1
                self.space()
                start = self.i
                depth = 0
                while self.i < len(self.s) and (self.s[self.i] != "}" or depth):
                    depth += {"{": 1, "}": -1}.get(self.s[self.i], 0)
                    self.i += 1
                style = self.s[start:self.i].strip()
            self.expect("}")
            return (kind, name, style)
        if kind in ("plural", "selectordinal", "select"):
            self.expect(",")
            offset = 0
            self.space()
            if kind != "select" and self.s.startswith("offset:", self.i):
                self.i += len("offset:")
                self.space()
                start = self.i
                while self.i < len(self.s) and (self.s[self.i].isdigit() or self.s[self.i] == "-"):
                    self.i += 1
                offset = int(self.s[start:self.i])
            options: Dict[str, List[Node]] = {}
            while True:
                self.space()
                if self.s.startswith("}", self.i):
                    self.i += 1
                    break
                key = self.selector()
                self.expect("{")
                options[key] = self.nodes(in_plural=kind != "select" or in_plural, until_tag=None)
                self.expect("}")
            if "other" not in options:
                raise self.error("%s for %r has no 'other' option" % (kind, name))
            return (kind, name, offset, options)
        raise self.error("unknown argument type %r" % kind)

    def selector(self) -> str:
        start = self.i
        if self.i < len(self.s) and self.s[self.i] == "=":
            self.i += 1
            if self.i < len(self.s) and self.s[self.i] == "-":
                self.i += 1
        while self.i < len(self.s) and not self.s[self.i].isspace() and self.s[self.i] not in "{}":
            self.i += 1
        if start == self.i:
            raise self.error("expected a selector")
        return self.s[start:self.i]


_CACHE: Dict[str, List[Node]] = {}


def parse(message: str) -> List[Node]:
    """The parsed form of `message`, cached."""
    nodes = _CACHE.get(message)
    if nodes is None:
        nodes = _Parser(message).parse()
        if len(_CACHE) > 4096:
            _CACHE.clear()
        _CACHE[message] = nodes
    return nodes


_NUMBER_STYLES = {"integer": {"maximumFractionDigits": 0}, "percent": {"style": "percent"}}
_DATE_STYLES = ("full", "long", "medium", "short")


def _ordinal_en(n: float) -> str:
    i = int(abs(n))
    if i % 10 == 1 and i % 100 != 11:
        return "one"
    if i % 10 == 2 and i % 100 != 12:
        return "two"
    if i % 10 == 3 and i % 100 != 13:
        return "few"
    return "other"


def _format_parts(nodes: List[Node], values: Mapping[str, Any], locale: str, time_zone: Optional[str],
                  pound: Optional[Tuple[float, str]], out: List[Any]) -> None:
    for node in nodes:
        if isinstance(node, str):
            out.append(node)
            continue
        kind = node[0]
        if kind == "pound":
            out.append(format_number(pound[0], locale) if pound else "#")
        elif kind == "arg":
            value = values.get(node[1])
            if value is None:
                out.append("{%s}" % node[1])
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                out.append(format_number(value, locale))
            else:
                out.append(value)
        elif kind == "number":
            value = values.get(node[1])
            if value is None:
                out.append("{%s}" % node[1])
                continue
            style = node[2]
            opts: Dict[str, Any] = dict(_NUMBER_STYLES.get(style or "", {}))
            if style and style.startswith("::"):
                for word in style[2:].split():
                    if word == "percent":
                        opts["style"] = "percent"
                    elif word.startswith("currency/"):
                        opts.update(style="currency", currency=word.split("/", 1)[1])
                    elif word == "compact-short":
                        opts["notation"] = "compact"
                    elif word.startswith(".") and set(word[1:]) <= set("0#"):
                        opts["minimumFractionDigits"] = word.count("0")
                        opts["maximumFractionDigits"] = len(word) - 1
            out.append(format_number(value, locale, **opts))
        elif kind in ("date", "time"):
            value = values.get(node[1])
            if value is None:
                out.append("{%s}" % node[1])
                continue
            style = node[2] if node[2] in _DATE_STYLES else ("medium" if kind == "date" else "short")
            key = "dateStyle" if kind == "date" else "timeStyle"
            out.append(format_datetime(value, locale, **{key: style, "timeZone": time_zone}))
        elif kind == "select":
            value = values.get(node[1])
            options = node[3]
            chosen = options.get(str(value) if value is not None else "other", options["other"])
            _format_parts(chosen, values, locale, time_zone, pound, out)
        elif kind in ("plural", "selectordinal"):
            raw = values.get(node[1])
            try:
                n = float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                n = 0.0
            offset, options = node[2], node[3]
            exact = "=%s" % (int(n) if n == int(n) else n)
            if exact in options:
                chosen = options[exact]
            else:
                shifted = n - offset
                num: Any = raw if offset == 0 and raw is not None else shifted
                if kind == "plural":
                    category = plural_category(num, locale)
                else:
                    category = _ordinal_en(shifted) if locale.split("-")[0].lower() == "en" else "other"
                chosen = options.get(category, options["other"])
            shown: Any = raw if offset == 0 and isinstance(raw, (int, float)) else n - offset
            _format_parts(chosen, values, locale, time_zone, (shown, locale), out)
        elif kind == "tag":
            kids: List[Any] = []
            _format_parts(node[2], values, locale, time_zone, pound, kids)
            handler = values.get(node[1])
            if callable(handler):
                result = handler(kids)
                if isinstance(result, list):
                    out.extend(result)
                elif result is not None:
                    out.append(result)
            else:
                out.extend(kids)


def _merge(parts: List[Any]) -> List[Any]:
    merged: List[Any] = []
    for p in parts:
        if isinstance(p, str) and merged and isinstance(merged[-1], str):
            merged[-1] += p
        elif p != "":
            merged.append(p)
    return merged


def format_rich(message: str, values: Optional[Mapping[str, Any]] = None, locale: str = "en-US",
                time_zone: Optional[str] = None) -> List[Any]:
    """Formats `message` into a list of parts: strings, with whatever tag callbacks returned between them.
    A tag without a callback keeps its text and drops the markup."""
    out: List[Any] = []
    _format_parts(parse(message), values or {}, locale, time_zone, None, out)
    return _merge(out)


def format_message(message: str, values: Optional[Mapping[str, Any]] = None, locale: str = "en-US",
                   time_zone: Optional[str] = None) -> str:
    """Formats `message` to a string. A missing value stays as its {placeholder}."""
    return "".join(str(p) for p in format_rich(message, values, locale, time_zone))


Callback = Callable[[List[Any]], Any]
