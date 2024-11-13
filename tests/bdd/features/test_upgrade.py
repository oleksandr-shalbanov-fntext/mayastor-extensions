"""Upgrade feature tests."""

import logging

from common.environment import get_env
from common.helm import ChartSource, HelmReleaseClient, latest_chart_so_far
from common.kubectl_mayastor import kubectl_mayastor
from common.repo import run_script
from kubernetes import client, config
from pytest_bdd import given, scenario, then, when
from retrying import retry

logger = logging.getLogger(__name__)

helm = HelmReleaseClient()


@scenario("upgrade.feature", "upgrade command is issued")
def test_upgrade_command_is_issued():
    """upgrade command is issued."""


@given("an installed mayastor helm chart")
def an_installed_mayastor_helm_chart():
    """an installed mayastor helm chart."""
    assert helm.install_mayastor(ChartSource.HOSTED, latest_chart_so_far()) is not None


@when("a kubectl mayastor upgrade command is issued")
def a_kubectl_mayastor_upgrade_command_is_issued():
    """a kubectl mayastor upgrade command is issued."""
    assert kubectl_mayastor(["upgrade"]) is not None


@then("the installed chart should be upgraded to the kubectl mayastor plugin's version")
def the_installed_chart_should_be_upgraded_to_the_kubectl_mayastor_plugins_version():
    """the installed chart should be upgraded to the kubectl mayastor plugin's version."""

    upgrade_target_version = get_env("UPGRADE_TARGET_VERSION")
    if upgrade_target_version is None:
        upgrade_target_version = run_script("scripts/python/generate-test-tag.sh")
    upgrade_target_version = upgrade_target_version.lstrip("v")
    logger.info(f"Value of upgrade_target_version={upgrade_target_version}")

    @retry(
        stop_max_attempt_number=450,
        wait_fixed=2000,
    )
    def helm_upgrade_succeeded():
        logger.info("Checking if helm upgrade succeeded...")
        metadata = helm.get_metadata_mayastor()
        logger.debug(f"helm get metadata output={metadata}")
        logger.debug(f"upgrade_target_version={upgrade_target_version}")
        if metadata:
            assert metadata["version"] == upgrade_target_version
            return
        raise ValueError("helm get metadata returned a None")

    @retry(
        stop_max_attempt_number=600,
        wait_fixed=2000,
    )
    def data_plane_upgrade_succeeded():
        logger.info("Checking if data-plane upgrade succeeded...")
        config.load_kube_config()
        v1 = client.CoreV1Api()
        label_selector = "app=io-engine"
        pods = v1.list_namespaced_pod(
            namespace="mayastor", label_selector=label_selector
        )
        switch = True
        for pod in pods.items:
            for i, container in enumerate(pod.spec.containers):
                if container.name == "io-engine":
                    logger.info(
                        f"pod.metadata.name={pod.metadata.name}, pod.spec.containers[{i}].image={container.image}"
                    )
                    switch = switch and container.image.endswith(":develop")
                    logger.info(f"Value of 'switch' after the AND={switch}")
                    break
        assert switch

    helm_upgrade_succeeded()
    data_plane_upgrade_succeeded()
