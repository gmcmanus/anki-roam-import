from setuptools import find_packages, setup

setup(
    name='anki-roam-import',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
    ],
    tests_require=['pytest~=5.3.5'],
)
