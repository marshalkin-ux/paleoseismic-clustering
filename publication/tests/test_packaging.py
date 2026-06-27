"""Tests for packaging utilities."""

from publication.utils.packaging import create_packages, render_data_descriptions


def test_render_data_descriptions(output_dir, sample_metadata):
    paths = render_data_descriptions(output_dir, sample_metadata)
    assert paths["en"].exists()
    assert paths["ru"].exists()
    assert "Test Title EN" in paths["en"].read_text(encoding="utf-8")


def test_create_packages(output_dir, sample_metadata, repo_root):
    manifest = create_packages(sample_metadata, output_dir, repo_root)
    assert "code.zip" in manifest
    assert (output_dir / "master_metadata.json").exists()
    assert (output_dir / "zenodo").is_dir()
