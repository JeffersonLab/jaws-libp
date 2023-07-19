# jaws-libp [![CI](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yml/badge.svg)](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/jaws-libp)](https://pypi.org/project/jaws-libp/) [![Docker](https://img.shields.io/docker/v/jeffersonlab/jaws-libp?sort=semver&label=DockerHub)](https://hub.docker.com/r/jeffersonlab/jaws-libp)
Reusable Python Classes for [JAWS](https://github.com/JeffersonLab/jaws).

---
- [Install](https://github.com/JeffersonLab/jaws-libp#install) 
- [API](https://github.com/JeffersonLab/jaws-libp#api)
- [Configure](https://github.com/JeffersonLab/jaws-libp#configure) 
- [Build](https://github.com/JeffersonLab/jaws-libp#build)
- [Develop](https://github.com/JeffersonLab/jaws-libp#develop)
- [Test](https://github.com/JeffersonLab/jaws-libp#test)
- [Release](https://github.com/JeffersonLab/jaws-libp#release) 
- [See Also](https://github.com/JeffersonLab/jaws-libp#see-also)
---

## Install
Requires [Python 3.9+](https://www.python.org/)

```
pip install jaws-libp
```

**Note**: Using newer versions of Python may be problematic because the dependency `confluent-kafka` uses librdkafka, which often does not have a wheel file prepared for later versions of Python, meaning setuptools will attempt to compile it for you, and that often doesn't work (especially on Windows).   Python 3.9 does have a wheel file for confluent-kafka so that's your safest bet.  Wheel files also generally only are prepared for Windows, MacOS, and Linux.  Plus only for architectures x86_64 and arm64, also only for glibc.  If you use with musl libc or linux-aarch64 then you'll likely have to compile librdkafka yourself from source.

## API
[Sphinx Docs](https://jeffersonlab.github.io/jaws-libp/)

## Configure
Environment variables are used to configure jaws-libp:

| Name             | Description                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------|
| BOOTSTRAP_SERVER | Host and port pair pointing to a Kafka server to bootstrap the client connection to a Kafka Cluster; example: `kafka:9092` |
| SCHEMA_REGISTRY  | URL to Confluent Schema Registry; example: `http://registry:8081`                                                          |

The Docker container can optionally handle the following environment variables as well:

| Name             | Description                                                                                                                                                                                                                                                                                                                                                                                                         |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ALARM_LOCATIONS  | Path to an alarm locations file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/locations)), else an https URL to a file, else a comma separated list of location definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|parent`                                                                                                                  |
| ALARM_CATEGORIES | Path to an alarm categories file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/categories)), else an https URL to a file, else a comma separated list of catgory definitions with fields.  Example Inline CSV: `name`                                                                                                                                                      |
| ALARM_CLASSES    | Path to an alarm classes file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/classes)), else an https URL to a file, else a comma separated list of class definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|category\|priority\|rationale\|correctiveaction\|pointofcontactusername\|latching\|filterable\|ondelayseconds\|offdelayseconds` |
| ALARM_INSTANCES  | Path to an alarm instances file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/instances)), else an https URL to a file, else a comma separated list of instance definitions with fields separated by the pipe symbol.  Leave epicspv field empty for SimpleProducer. Example Inline CSV: `name\|class\|epicspv\|location\|maskedby\|screencommand`                         |

## Build
This [Python 3.9+](https://www.python.org/) project is built with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html) and may be run using the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.

```
git clone https://github.com/JeffersonLab/jaws-libp
cd jaws-libp
python -m venv .venv_dev --upgrade-deps
```

Activate the virtual env using your [shell specific command](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1#activate-dev-virtual-environment), then install in editable mode with dev deps and run build:
```
pip install -e .[dev]
python -m build
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Python Development Notes](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1)

## Develop
Set up the build environment following the [Build](https://github.com/JeffersonLab/jaws-libp#build) instructions.

In order to iterate rapidly when making changes it's often useful to run the Python scripts directly on the local workstation, perhaps leveraging an IDE.  In this scenario run the service dependencies with Docker Compose:
```
docker compose -f deps.yml up
```

**Note**: The environment variable defaults work in this scenario and are defined as:
`BOOTSTRAP_SERVERS=localhost:9094` and `SCHEMA_REGISTRY=http://localhost:8081`

## Test
The integration tests depend on a running Kafka instance, generally in Docker.  The tests run automatically via the [CI](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yml) GitHub Action on every commit (unless `[no ci]` is included in the commit message).  The tests can be run locally during development.  Set up the development environment following the [Develop](https://github.com/JeffersonLab/jaws-libp#develop) instructions.  Then with the `deps.yml` Docker containers running and the build virtual environment activated run:
```
pytest
```

## Release
1. Bump the version number in pyproject.toml and commit and push to GitHub (using [Semantic Versioning](https://semver.org/)).   
1. Create a new release on the GitHub [Releases](https://github.com/JeffersonLab/jaws-libp/releases) page corresponding to same version in pyproject.toml (Enumerate changes and link issues).
1. [Publish to PyPi](https://github.com/JeffersonLab/jaws-libp/actions/workflows/pypi-publish.yml) GitHub Action should run automatically.
1. [Publish to gh-pages](https://github.com/JeffersonLab/jaws-libp/actions/workflows/gh-pages-publish.yml) GitHub Action should run automatically.

## See Also
 - [jaws-libj (Java)](https://github.com/JeffersonLab/jaws-libj)
 - [Developer Notes](https://github.com/JeffersonLab/jaws-libp/wiki/Developer-Notes)
