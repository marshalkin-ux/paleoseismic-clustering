"""Mock tests for Figshare agent."""

from publication.agents.figshare import FigshareAgent


def test_figshare_mock_upload(sample_metadata, output_dir):
    agent = FigshareAgent(mock_mode=True, output_dir=output_dir)
    result = agent.upload(sample_metadata)
    assert result["mock"] is True
    assert sample_metadata["figshare_doi"].startswith("10.6084/")
