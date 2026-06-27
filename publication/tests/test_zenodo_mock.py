"""Mock tests for Zenodo agent."""

from publication.agents.zenodo import ZenodoAgent


def test_zenodo_mock_upload(sample_metadata, output_dir):
    agent = ZenodoAgent(mock_mode=True, output_dir=output_dir)
    result = agent.upload(sample_metadata)
    assert result["mock"] is True
    assert sample_metadata["doi"].startswith("10.5281/")
    assert "zenodo.org" in sample_metadata["zenodo_url"]
