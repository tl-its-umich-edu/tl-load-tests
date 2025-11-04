#!/bin/bash

# Initial parameters for locust

# Peak users to load test
PEAK_USERS=30
# How many users a second to add
SPAWN_RATE=0.5
# Host should have a trailing slash
HOST="https://ccm-dev.tl.it.umich.edu/"
# Log Level
LOG_LEVEL=INFO

# Run MyLA Locust Test
locust -f ccm_locust_test.py -H "${HOST}" -r "${SPAWN_RATE}" -u "${PEAK_USERS}" -L "${LOG_LEVEL}"
