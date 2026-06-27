"""Tests for metadata extraction."""

from publication.utils.metadata import build_metadata


def test_build_metadata_from_repo(repo_root, output_dir):
    meta = build_metadata(repo_root, output_dir / "master_metadata.json")
    assert "Global Seismic Series" in meta["title_en"]
    assert "сейсмические серии" in meta["title_ru"].lower()
    assert len(meta["abstract_en"]) > 100
    assert len(meta["abstract_ru"]) > 100
    assert meta["authors"][0]["email"] == "marshalkin@gmail.com"
    assert "earthquake clustering" in meta["keywords_en"] or len(meta["keywords_en"]) > 0
    assert meta["github_url"].endswith("paleoseismic-clustering")
