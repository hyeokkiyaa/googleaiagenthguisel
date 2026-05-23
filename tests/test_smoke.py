from agent.app import __version__
from agent.app.main import get_app_metadata


def test_agent_package_is_importable() -> None:
    assert __version__


def test_app_metadata_shape() -> None:
    metadata = get_app_metadata()

    assert metadata["name"] == "ContextGuard Local Agent"
    assert metadata["status"] == "ready"
    assert metadata["version"] == __version__

