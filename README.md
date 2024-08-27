# jaws-libp [![CI](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yaml/badge.svg)](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yaml) [![PyPI](https://img.shields.io/pypi/v/jaws-libp)](https://pypi.org/project/jaws-libp/) [![Docker](https://img.shields.io/docker/v/jeffersonlab/jaws-libp?sort=semver&label=DockerHub)](https://hub.docker.com/r/jeffersonlab/jaws-libp)
Reusable Python classes for [JAWS](https://github.com/JeffersonLab/jaws) plus admin scripts to setup and manage a deployment.

---
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws-libp#quick-start-with-compose)
- [Install](https://github.com/JeffersonLab/jaws-libp#install) 
- [API](https://github.com/JeffersonLab/jaws-libp#api)
- [Configure](https://github.com/JeffersonLab/jaws-libp#configure) 
- [Build](https://github.com/JeffersonLab/jaws-libp#build)
- [Develop](https://github.com/JeffersonLab/jaws-libp#develop)
- [Test](https://github.com/JeffersonLab/jaws-libp#test)
- [Release](https://github.com/JeffersonLab/jaws-libp#release) 
- [See Also](https://github.com/JeffersonLab/jaws-libp#see-also)
---

## Quick Start with Compose
1. Grab project
```
git clone https://github.com/JeffersonLab/jaws-libp
cd jaws-libp
```
2. Launch [Compose](https://github.com/docker/compose)
```
docker compose up
```
3. Monitor active alarms
```
docker exec -it cli list_activations --monitor
```
4. Trip an alarm
```
docker exec cli set_activation alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

**See**: [Docker Compose Strategy](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c)

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

| Name            | Description                                                                                                                                                                                                                                                                                                                                                                                                              |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ALARM_LOCATIONS | Path to an alarm locations file to import ([example file](https://github.com/JeffersonLab/jaws-libp/blob/main/container/app/example-data/locations)), else an https URL to a file, else a comma separated list of location definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|parent`                                                                                                     |
| ALARM_SYSTEMS   | Path to an alarm categories file to import ([example file](https://github.com/JeffersonLab/jaws-libp/blob/main/container/app/example-data/systems)), else an https URL to a file, else a comma separated list of system definitions with fields.  Example Inline CSV: `name`                                                                                                                                             |
| ALARM_ACTIONS   | Path to an alarm classes file to import ([example file](https://github.com/JeffersonLab/jaws-libp/blob/main/container/app/example-data/actions)), else an https URL to a file, else a comma separated list of class definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|category\|priority\|rationale\|correctiveaction\|latching\|filterable\|ondelayseconds\|offdelayseconds`            |
| ALARMS          | Path to an alarm registration instances file to import ([example file](https://github.com/JeffersonLab/jaws-libp/blob/main/container/app/example-data/alarms)), else an https URL to a file, else a comma separated list of instance definitions with fields separated by the pipe symbol.  Leave epicspv field empty for SimpleProducer. Example Inline CSV: `name\|action\|epicspv\|location\|maskedby\|screencommand` |
| ALARMS_URL_CSV  | If provided, is a comma separated list of file names to append to ALARMS; ignored if ALARMS doesn't start with `https`; [Example](https://github.com/JeffersonLab/jaws-libp/blob/cc56789a68009f71988ba98f5f55d822c240cd9d/build.yml#L25-L26).                                                                                                                                                                            |
| ALARM_OVERRIDES | Path to an alarm overrides file to import ([example file](https://github.com/JeffersonLab/jaws-libp/blob/main/container/app/example-data/overrides)), else an https URL to a file.                                                                                                                                                                                                                                       |

## Build
This [Python 3.9+](https://www.python.org/) project is built with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html) and may be run using the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.

```
git clone https://github.com/JeffersonLab/jaws-libp
cd jaws-libp
python -m venv .venv_dev --upgrade-deps
```

Activate the virtual env using your [shell specific command](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1#activate-dev-virtual-environment), then install in editable mode with dev deps and run build:
```
# Windows
.venv_dev\Scripts\activate.bat
# UNIX (SH Shell)
source .venv_dev/bin/activate
# UNIX (CSH Shell)
source .venv_dev/bin/activate.csh


pip install -e ."[dev]"
python -m build
pylint --recursive=y src/*
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Python Development Notes](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1)

## Develop
Set up the build environment following the [Build](https://github.com/JeffersonLab/jaws-libp#build) instructions.

In order to iterate rapidly when making changes it's often useful to run the Python scripts directly on the local workstation, perhaps leveraging an IDE.  In this scenario run the service dependencies with Docker Compose:
```
docker compose -f deps.yaml up
```

**Note**: The environment variable defaults work in this scenario and are defined as:
`BOOTSTRAP_SERVERS=localhost:9094` and `SCHEMA_REGISTRY=http://localhost:8081`

## Test
The integration tests depend on a running Kafka instance, generally in Docker.  The tests run automatically via the [CI](https://github.com/JeffersonLab/jaws-libp/actions/workflows/ci.yaml) GitHub Action on every commit (unless `[no ci]` is included in the commit message).  The tests can be run locally during development.  Set up the development environment following the [Develop](https://github.com/JeffersonLab/jaws-libp#develop) instructions.  Then with the `deps.yaml` Docker containers running and the build virtual environment activated run:
```
pytest
```

## Release
1. Bump the version number in the VERSION file and commit and push to GitHub (using [Semantic Versioning](https://semver.org/)).
2. The [CD](https://github.com/JeffersonLab/jaws-libp/blob/main/.github/workflows/cd.yaml) GitHub Action should run automatically invoking:
    - The [Create release](https://github.com/JeffersonLab/python-workflows/blob/main/.github/workflows/gh-release.yaml) GitHub Action to tag the source and create release notes summarizing any pull requests.   Edit the release notes to add any missing details.
    - The [Publish artifact](https://github.com/JeffersonLab/python-workflows/blob/main/.github/workflows/pypi-publish.yaml) GitHub Action to create a deployment artifact on PyPi.
    - The [Publish docs](https://github.com/JeffersonLab/python-workflows/blob/main/.github/workflows/gh-pages-publish.yaml) GitHub Action to create Sphinx docs.
    - The [Publish docker image](https://github.com/JeffersonLab/container-workflows/blob/main/.github/workflows/docker-publish.yaml) GitHub Action to create a new demo Docker image.

## See Also
 - [jaws-libj (Java)](https://github.com/JeffersonLab/jaws-libj)
 - [Developer Notes](https://github.com/JeffersonLab/jaws-libp/wiki/Developer-Notes)
