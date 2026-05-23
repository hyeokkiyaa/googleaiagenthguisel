import pytest


@pytest.fixture(autouse=True)
def default_to_mock_ai_provider(monkeypatch):
    monkeypatch.setenv("CONTEXTGUARD_AI_PROVIDER", "mock")

