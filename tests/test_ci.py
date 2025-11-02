import os
import subprocess
import pytest
from contextlib import contextmanager
import time

import requests

from dagster import file_relative_path

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

HOST_NAME = "localhost"
PORT = "3000"

@contextmanager
def docker_service_up(docker_compose_file):
    if IS_BUILDKITE:
        yield  # buildkite pipeline handles the service
        return

    try:
        subprocess.check_output(["docker", "compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker", "compose", "-f", docker_compose_file, "rm", "-f"])
    except subprocess.CalledProcessError:
        pass

    up_process = subprocess.Popen(["docker", "compose", "-f", docker_compose_file, "up", "--no-start"])
    up_process.wait()
    assert up_process.returncode == 0

    start_process = subprocess.Popen(["docker", "compose", "-f", docker_compose_file, "start"])
    start_process.wait()
    assert start_process.returncode == 0

    try:
        yield
    finally:
        subprocess.check_output(["docker", "compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker", "compose", "-f", docker_compose_file, "rm", "-f"])

@pytest.fixture
def compose_up():
    with docker_service_up(file_relative_path(__file__, "../docker-compose.yml")):
        # Wait for server to wake up
        # start_time = time.time()
        time.sleep(20)
        yield

def test_status(compose_up):
    response = requests.get(f"http://{HOST_NAME}:{PORT}/")
    assert response.status_code == 200