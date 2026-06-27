"""Mock tests for OSF agent."""

from publication.agents.osf_eartharxiv import OSFEarthArxivAgent


def test_osf_mock_upload(sample_metadata, output_dir):
    agent = OSFEarthArxivAgent(mock_mode=True, output_dir=output_dir)
    result = agent.upload(sample_metadata)
    assert result["mock"] is True
    assert sample_metadata["osf_url"]
    assert sample_metadata["eartharxiv_url"]
