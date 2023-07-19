# jaws-libp [![CI](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yml/badge.svg)](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/jaws-libp)](https://pypi.org/project/jaws-libp/)
Reusable Python Classes for [JAWS](https://github.com/JeffersonLab/jaws).

---
- [Install](https://github.com/JeffersonLab/jaws-libp#install) 
- [API](https://github.com/JeffersonLab/jaws-libp#api)
- [Build](https://github.com/JeffersonLab/jaws-libp#build) 
- [Release](https://github.com/JeffersonLab/jaws-libp#release) 
- [See Also](https://github.com/JeffersonLab/jaws-libp#see-also)
---

## Install
Requires [Python 3.9+](https://www.python.org/)

```
pip install jaws-libp
```

**Note**: Using newer versions of Python may be problematic because the dependency `confluent-kafka` uses librdkafka, which often does not have a wheel file prepared for later versions of Python, meaning setuptools will attempt to compile it for you, and that often doesn't work (especially on Windows).   Python 3.9 DOES have a wheel file for confluent-kafka so that's your safest bet. 

## API
[Sphinx Docs](https://jeffersonlab.github.io/jaws-libp/)

## Build
This [Python 3.9+](https://www.python.org/) project is built with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html) and may be run using the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.

```
git clone https://github.com/JeffersonLab/jaws-libp
cd jaws-libp
python -m build
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Python Development Notes](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1)

## Release
1. Bump the version number in pyproject.toml and commit and push to GitHub (using [Semantic Versioning](https://semver.org/)).   
1. Create a new release on the GitHub [Releases](https://github.com/JeffersonLab/jaws-libp/releases) page corresponding to same version in setup.cfg (Enumerate changes and link issues)
1. [Publish to PyPi](https://github.com/JeffersonLab/jaws-libp/actions/workflows/pypi-publish.yml) GitHub Action should run automatically.  Else:
    1. Clean build by removing `build`, `dist`, and `docsrc/source/_autosummary` directories
    1. Activate [virtual env](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1#activate-dev-virtual-environment)
    1. From venv build package, build docs, lint, test, and publish new artifact to PyPi with:
```
python -m build
sphinx-build -b html docsrc/source build/docs
pylint src/jaws_libp
pytest
python -m twine upload --repository pypi dist/*
```
 4. [Publish to gh-pages](https://github.com/JeffersonLab/jaws-libp/actions/workflows/gh-pages-publish.yml) GitHub Action should run automatically.

## See Also
 - [jaws-libj (Java)](https://github.com/JeffersonLab/jaws-libj)
 - [Developer Notes](https://github.com/JeffersonLab/jaws-libp/wiki/Developer-Notes)
