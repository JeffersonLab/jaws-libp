#!/bin/bash

test -f /home/jaws/initialized && test $(list_schemas | wc -l) -gt 20