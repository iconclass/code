import os, re, json
from typing import Any
from pathlib import Path
from zipfile import ZipFile
import logging
import urllib.request

__version__ = "0.26"

WITH_NAME_MATCH = re.compile(r"\((?!\.\.\.)[^+]+\)")
BRACKETS = re.compile(r"\([\w ]+?\)")
WIKIDATA_QNUM = re.compile(r"\(wd\:(Q[0-9]+?)\)")


def split_on_colon(s):
    s = re.sub(r"\(([^)]*):([^)]*)\)", r"(\1__COLON__\2)", s)
    parts = s.split(":")
    parts = [part.replace("__COLON__", ":") for part in parts]
    return parts


class NotationNotFound(Exception):
    pass


def make_data_zip(filepath):
    data_zip = ZipFile(filepath, "w")
    data_zip.writestr(
        "notations.txt",
        urllib.request.urlopen(
            "https://raw.githubusercontent.com/iconclass/data/main/notations.txt"
        ).read(),
    )
    data_zip.writestr(
        "keys.txt",
        urllib.request.urlopen(
            "https://raw.githubusercontent.com/iconclass/data/main/keys.txt"
        ).read(),
    )
    for lang in ("en", "de", "fr", "it", "pt", "jp"):
        buf = []
        for filename in (
            f"txt_{lang}_0_1.txt",
            f"txt_{lang}_2_3.txt",
            f"txt_{lang}_4.txt",
            f"txt_{lang}_5_6_7_8.txt",
            f"txt_{lang}_9.txt",
        ):
            buf.append(
                urllib.request.urlopen(
                    f"https://raw.githubusercontent.com/iconclass/data/main/txt/{lang}/{filename}"
                ).read()
            )
        data_zip.writestr(f"txt_{lang}.txt", b"\n".join(buf))
    for lang in ("en", "de", "fr", "it", "pt", "jp"):
        buf = []
        for filename in (
            f"kw_{lang}_0_1.txt",
            f"kw_{lang}_2_3.txt",
            f"kw_{lang}_4.txt",
            f"kw_{lang}_5_6_7_8.txt",
            f"kw_{lang}_9.txt",
            f"kw_{lang}_keys.txt",
        ):
            try:
                buf.append(
                    urllib.request.urlopen(
                        f"https://raw.githubusercontent.com/iconclass/data/main/kw/{lang}/{filename}"
                    ).read()
                )
            except urllib.error.HTTPError:
                pass
        data_zip.writestr(f"kw_{lang}.txt", b"\n".join(buf))


class Iconclass:
    def __init__(self):
        data_path = current_dir = Path(__file__).parent / "data.zip"
        if not data_path.exists():
            make_data_zip(data_path)

        data_file = ZipFile(data_path)

        self._D = {
            None: {"c": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "n": ""}
        }
        self.texts = {}
        self.keywords = {}
        keys = {}

        for o in data_file.read("keys.txt").decode("utf8").split("\n$"):
            obj = {}
            for line in o.split("\n"):
                tmp = line.split(" ")
                if len(tmp) < 2:
                    continue
                field = tmp[0]
                val = " ".join(tmp[1:])
                if field == "K":
                    obj["k"] = val
                elif field == "S":
                    obj["s"] = [val]
                elif field == ";":
                    obj["s"].append(val)
            suffixes = [s for s in obj.get("s", []) if s.find("q") < 0]
            if suffixes:
                obj["s"] = suffixes
                keys[obj["k"]] = obj

        for o in data_file.read("notations.txt").decode("utf8").split("\n$"):
            obj = {}
            for line in o.split("\n"):
                tmp = line.split(" ")
                if len(tmp) < 2:
                    continue
                field = tmp[0].lower()
                val = " ".join(tmp[1:])
                val = val.strip(" ")
                if field in ("r", "c", "p"):
                    obj[field] = [val]
                    last_field = field
                elif field == ";":
                    obj[last_field].append(val)
                else:
                    obj[field] = val
            if obj:
                k = obj.get("k")
                if k:
                    kk = keys.get(k)
                    if kk:
                        obj["k"] = kk
                    else:
                        del obj["k"]
                self._D[obj["n"]] = obj
        self.pad(self._D[None])

    def get(self, notation):
        raise Exception()  # not yet implemented

    def obj(self, notation):
        if notation == "ICONCLASS" or notation == "":
            return {
                "c": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                "n": "ICONCLASS",
            }

        tmp = notation.split("(+")
        if len(tmp) == 2:
            base, key = tmp
            if key.endswith(")"):
                key = key[:-1]
        else:
            base = tmp[0]
            key = ""

        obj = self._D.get(base)
        if not obj and WITH_NAME_MATCH.search(base):
            notation_with_name = WITH_NAME_MATCH.sub("(...)", base)
            obj = self._D.get(notation_with_name)
            if obj:
                obj = obj.copy()
                base = notation_with_name
                bracketed_text = WITH_NAME_MATCH.search(notation).group()
                obj["notation_with_name"] = notation_with_name
                obj["bracketed_text"] = bracketed_text
                if "c" in obj:
                    obj["c"] = [
                        child.replace("(...)", bracketed_text)
                        for child in obj.get("c", [])
                    ]
        if not obj:
            raise NotationNotFound(notation)

        obj = obj.copy()
        obj["b"] = base.strip(" \t\n")  # in case of typo in source
        obj["n"] = notation  # in case there was a key, this sets it again

        obj_key = obj.get("k", {})
        if key and key not in obj_key["s"]:
            raise NotationNotFound(notation)
        if key:
            keys = [
                f'{obj_key["k"]}{k}'
                for k in obj_key.get("s", [])
                if k.startswith(key) and k != key and len(k) == (len(key) + 1)
            ]
            obj["l"] = keys
            obj["k"] = f'{obj_key["k"]}{key}'
            new_path = [f"{obj['p'][-1]}(+{key[: ki + 1]})" for ki in range(len(key))]
            obj["p"] = obj["p"] + new_path
        else:
            keys = [f'{obj_key["k"]}{k}' for k in obj_key.get("s", []) if len(k) == 1]
            obj["l"] = keys
            if "k" in obj:
                del obj["k"]

        return obj

    def text_(self, notation, language="en"):
        obj = self.obj(notation)
        if "b" not in obj:
            return ""
        base_t = self.texts[language].get(obj["b"], "")
        if "bracketed_text" in obj:
            base_t = BRACKETS.sub(obj["bracketed_text"], base_t)

            find_qnum = WIKIDATA_QNUM.search(notation)
            if find_qnum:
                qnum = find_qnum.groups()[0]
                # Fetch the label for this qnum from wikidata
                uri = f"https://www.wikidata.org/wiki/Special:EntityData/{qnum}.json"
                try:
                    qnum_data = urllib.request.urlopen(uri).read()
                    qnum_data = json.loads(qnum_data)
                    base_t = (
                        qnum_data.get("entities", {})
                        .get(qnum)
                        .get("labels", {})
                        .get(language, {})
                        .get("value", base_t)
                    )
                except urllib.error.HTTPError:
                    logging.debug(f"Wikidata {uri} gave an error")
        if "k" in obj:
            t2 = self.texts[language].get(obj["k"], "")
            if t2:
                base_t = f"{base_t} (+ {t2})"
        return base_t

    def txt(self, notation, language="en"):
        if language not in self.texts:
            self.load(language)
        parts = split_on_colon(notation)
        return " : ".join([self.text_(p, language) for p in parts])

    def kw(self, notation, language="en"):
        if language not in self.texts:
            self.load(language)
        obj = self.obj(notation)
        if "b" not in obj:
            return []
        base_kw = self.keywords[language].get(obj["b"], []).copy()
        if "k" in obj:
            base_kw.extend(self.keywords[language].get(obj["k"], []))
        return base_kw

    def load(self, language):
        data_path = current_dir = Path(__file__).parent / f"data.zip"
        if not data_path.exists():
            raise Exception(f"{data_path} not found")
        data_file = ZipFile(data_path)

        self.texts[language] = {}
        lines = data_file.read(f"txt_{language}.txt").decode("utf8").split("\n")
        for line in lines:
            tmp = line.strip().split("|")
            if len(tmp) != 2:
                continue
            notation, txt = tmp
            self.texts[language][notation] = txt

        self.keywords[language] = {}
        try:
            lines = data_file.read(f"kw_{language}.txt").decode("utf8").split("\n")
            for line in lines:
                tmp = line.strip().split("|")
                if len(tmp) != 2:
                    continue
                notation, kw = tmp
                self.keywords[language].setdefault(notation, []).append(kw)
        except KeyError:
            logging.error(f"kw_{language} not found")

    def pad(self, n):
        p = n.get("p", [])
        if n["n"]:
            p.append(n["n"])
        for c in n.get("c", []):
            if c not in self._D:
                print(f"Child {c} not found in {n['n']}")
                continue
            kind = self._D[c]
            kind["p"] = p.copy()
            self.pad(kind)


class Notation:
    @staticmethod
    def init():
        obj = {
            "c": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            "n": "ICONCLASS",
        }
        return Notation(obj, Iconclass())

    def __init__(self, obj: dict, source: Iconclass):
        self.obj = obj
        self.source = source

    def __repr__(self) -> str:
        t = self.source.txt(self.obj["n"])
        n = self.obj["n"].strip(" \t\n")
        return f"{n} {t}"

    def __str__(self) -> str:
        return self.obj["n"].strip(" \t\n")  # in case there were invisible typos

    def __call__(self, language="en") -> str:
        return self.source.txt(self.obj["n"], language)

    def __iter__(self):
        if self.obj["n"].find("(+") < 0:
            for c in self.obj.get("c", []):
                yield Notation(self.source.obj(c), self.source)

        for l in self.obj.get("l", []):
            ll = re.split("[kmn]", l)[-1]
            try:
                key_notation = f"{self.obj['b']}(+{ll})"
                tmp = self.source.obj(key_notation)
                yield Notation(tmp, self.source)
            except NotationNotFound:
                logging.debug(f"Notation key {key_notation} not found")

    def __getitem__(self, name: str) -> Any:
        return Notation(self.source.obj(name), self.source)

    def related(self):
        for r in self.obj.get("r", []):
            yield Notation(self.source.obj(r), self.source)

    def keywords(self, language="en"):
        return self.source.kw(self.obj["n"], language=language)

    def path(self):
        for p in self.obj.get("p", []):
            try:
                yield Notation(self.source.obj(p), self.source)
            except NotationNotFound:
                ...


def init() -> Notation:
    return Notation.init()
