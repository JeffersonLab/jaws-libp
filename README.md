# jaws-libp [![Python lint and test](https://github.com/JeffersonLab/jaws-libp/actions/workflows/python.yml/badge.svg)](https://github.com/JeffersonLab/jaws-libp/actions/workflows/python.yml) [![PyPI](https://img.shields.io/pypi/v/jaws-libp)](https://pypi.org/project/jaws-libp/)
Reusable Python Classes for [JAWS](https://github.com/JeffersonLab/jaws).

---
- [Install](https://github.com/JeffersonLab/jaws-libp#install) 
- [API](https://github.com/JeffersonLab/jaws-libp#api)
- [Build](https://github.com/JeffersonLab/jaws-libp#build) 
- [See Also](https://github.com/JeffersonLab/jaws-libp#see-also)
---

## Install
Requires [Python 3.9+](https://www.python.org/)

```
pip install jaws-libp
```

**Note**: Using newer versions of Python may be problematic because the depenency `confluent-kafka` uses librdkafka, which often does not have a wheel file prepared for later versions of Python, meaning setuptools will attempt to compile it for you, and that often doesn't work (especially on Windows).   Python 3.9 DOES have a wheel file for confluent-kafka so that's your safest bet. 

## API
[Sphinx Docs](https://jeffersonlab.github.io/jaws-libp/)

## Build
This [Python 3.9+](https://www.python.org/) project is built with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html) and may be run using either the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature or a dedicated Docker container to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.

```
git clone https://github.com/JeffersonLab/jaws-libp
cd jaws-libp
python -m build
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Python Development Notes](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1) and [Docker Development Quick Reference](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c#development-quick-reference)

## See Also
 - [Developer Notes](https://github.com/JeffersonLab/jaws-libp/wiki/Developer-Notes)
