#!/bin/bash

# Initial parameters for locust
# Initial users to load test
INITIAL_USERS=50
# How many users a second to add
SPAWN_RATE=5
# Host should have a trailing slash
HOST=https://test-myla.tl.it.umich.edu/
# Log Level
LOG_LEVEL=INFO

# Run MyLA Locust Test
locust -f myla_locust_test.py -H "${HOST}" -r "${SPAWN_RATE}" -u "${INITIAL_USERS}" -L "${LOG_LEVEL}"
