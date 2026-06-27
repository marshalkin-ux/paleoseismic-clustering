"""Mock tests for arXiv agent."""

from publication.agents.arxiv import ArxivAgent


def test_arxiv_mock_upload(sample_metadata, output_dir):
    agent = ArxivAgent(mock_mode=True, output_dir=output_dir)
    result = agent.upload(sample_metadata)
    assert result["mock"] is True
    assert sample_metadata["arxiv_id"]
