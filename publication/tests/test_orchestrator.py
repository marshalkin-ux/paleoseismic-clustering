"""Tests for orchestrator workflow."""

from publication.agents.orchestrator import Orchestrator


def test_prepare_only(output_dir):
    orch = Orchestrator(dry_run=True, prepare_only=True, output_dir=output_dir)
    meta = orch.run()
    assert meta["title_en"]
    assert (output_dir / "master_metadata.json").exists()
    assert (output_dir / "report.html").exists()


def test_dry_run_full_flow(output_dir):
    orch = Orchestrator(
        dry_run=True,
        output_dir=output_dir,
        platforms=["zenodo", "figshare", "arxiv"],
        skip_social=True,
    )
    meta = orch.run()
    assert meta["doi"].startswith("10.5281/")
    assert meta["figshare_doi"]
    assert meta["arxiv_id"]
