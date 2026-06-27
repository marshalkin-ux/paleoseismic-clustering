"""Mock tests for PANGAEA/GFZ/Dryad agents."""

from publication.agents.data_repos import DataReposAgent


def test_data_repos_mock(sample_metadata, output_dir):
    agent = DataReposAgent(mock_mode=True, output_dir=output_dir)
    results = agent.upload_all(sample_metadata)
    assert "pangaea" in results
    assert sample_metadata["pangaea_doi"].startswith("10.1594/")
    assert sample_metadata["gfz_doi"].startswith("10.5880/")
    assert sample_metadata["dryad_doi"].startswith("10.5061/")
