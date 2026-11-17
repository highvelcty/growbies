#!/usr/bin/env python3
from enum import StrEnum
from packaging.version import Version
from pathlib import Path
import re
import sys

PATH_TO_SOURCE_SCRIPTS = Path(__file__).resolve().parent
PATH_TO_SOURCE = PATH_TO_SOURCE_SCRIPTS / '..'
PATH_TO_ROOT = PATH_TO_SOURCE / '..'
PATH_TO_BUILD = Path(sys.argv[1]) if len(sys.argv) > 1 else PATH_TO_ROOT / 'build'
PATH_TO_BUILD_DOCS = PATH_TO_BUILD / 'docs'

DOC_PATTERN = re.compile(r'^(?P<document_type>.+)-(?P<version>\d+(?:\.\d+)*(?:[a-zA-Z0-9.+!-]*)?)$')

class DocumentType(StrEnum):
    GATEWAY = 'gateway'
    FIRMWARE = 'firmware'
    MANUAL = 'manual'

def try_parse_document_type_and_revision(a_str: str) -> tuple[DocumentType, Version] | None:
    match = DOC_PATTERN.fullmatch(a_str)

    if match:
        try:
            document_type = DocumentType(match.group('document_type'))
            version = Version(match.group('version'))
        except ValueError:
            return None
        return document_type, version
    return None

class VersionedDocumentation:
    def __init__(self, version: Version, directory: str):
        self._version = version
        self._directory = directory

    @property
    def directory(self):
        return self._directory

    def __eq__(self, other):
        if not isinstance(other, VersionedDocumentation):
            return NotImplemented
        return self._version == other._version

    def __lt__(self, other):
        if not isinstance(other, VersionedDocumentation):
            return NotImplemented
        return self._version < other._version


class VersionedDocumentations:
    def __init__(self):
        self._documentations = list()

    def add_documentation(self, version: Version, directory: str):
        documentation = VersionedDocumentation(version, directory)
        if documentation not in self._documentations:
            self._documentations.append(documentation)

    def latest(self) -> VersionedDocumentation:
        self._documentations.sort(reverse=True)
        return self._documentations[0]


class TopLevelIndexRst:
    top_level_index_rst_template = f"""\
Growbies Documentation
======================

- `Owner's Manual <{{{DocumentType.MANUAL}}}/index.html>`_
- `Gateway Documentation <{{{DocumentType.GATEWAY}}}/index.html>`_
- `Firmware Documentation <{{{DocumentType.FIRMWARE}}}/index.html>`_

"""
    def __init__(self, documentation_sets: dict[DocumentType, VersionedDocumentations]):
        self._documentation_sets = documentation_sets

    def __str__(self):
        return self.top_level_index_rst_template.format(
            **{
                document_type.value: documentations.latest().directory
                for document_type, documentations in self._documentation_sets.items()
            }
        )

    def save(self):
        with open(PATH_TO_SOURCE / 'index.rst', 'w') as outf:
            outf.write(str(self))

def generate_top_index_rst():
    documentation_sets = {
        document_type: VersionedDocumentations()
        for document_type in DocumentType
    }

    for path in PATH_TO_BUILD_DOCS.iterdir():
        if path.is_dir():
            parsed = try_parse_document_type_and_revision(path.name)
            if parsed:
                document_type, version = parsed
                if document_type in documentation_sets:
                    documentation_sets[document_type].add_documentation(version, path.name)

    TopLevelIndexRst(documentation_sets).save()

if __name__ == '__main__':
    generate_top_index_rst()