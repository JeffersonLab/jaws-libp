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
```
python -m build
```

## See Also
 - [Developer Notes](https://github.com/JeffersonLab/jaws-libp/wiki/Developer-Notes)
