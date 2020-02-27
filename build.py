#!/usr/bin/env python3
import os
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    with ZipFile('anki_roam_import.ankiaddon', mode='w', compression=ZIP_DEFLATED) as zip_file:
        for path in '__init__.py', 'anki_roam_import', 'config.json', 'config.md', 'manifest.json':
            add_to_zip(zip_file, path)


def add_to_zip(zip_file: ZipFile, path: str) -> None:
    if '__pycache__' in path:
        return

    zip_file.write(path)

    if os.path.isdir(path):
        for child_path in os.listdir(path):
            add_to_zip(zip_file, os.path.join(path, child_path))


main()
