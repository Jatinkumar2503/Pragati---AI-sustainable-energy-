"""Unit tests verifying provenance labels, truth-in-advertising disclaimers, and evidence integrity."""

import os
import pytest
from backend.engine.digital_twin import DigitalTwinEngine, TAX_REGIMES, CEA_GRID_EMISSION_FACTORS
from backend.engine.demo_runner import DEMO_BENCHMARK_FIXTURE_V1, IndustrialDemoRunner


def test_documentation_and_registers_exist():
    """Verify that METHODOLOGY_AND_LIMITATIONS.md and EVIDENCE_REGISTER.md exist and contain core sections."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    meth_path = os.path.join(root_dir, "METHODOLOGY_AND_LIMITATIONS.md")
    evid_path = os.path.join(root_dir, "EVIDENCE_REGISTER.md")
    subm_path = os.path.join(root_dir, "HACKATHON_SUBMISSION.md")

    assert os.path.exists(meth_path), "METHODOLOGY_AND_LIMITATIONS.md must exist in root"
    assert os.path.exists(evid_path), "EVIDENCE_REGISTER.md must exist in root"
    assert os.path.exists(subm_path), "HACKATHON_SUBMISSION.md must exist in root"

    with open(meth_path, "r", encoding="utf-8") as f:
        meth_content = f.read()
    with open(evid_path, "r", encoding="utf-8") as f:
        evid_content = f.read()
    with open(subm_path, "r", encoding="utf-8") as f:
        subm_content = f.read()

    # Verify key provenance identifiers
    assert "STEEL_BENCHMARK_FIXTURE_V1" in meth_content
    assert "STEEL_BENCHMARK_FIXTURE_V1" in evid_content
    assert "STEEL_BENCHMARK_FIXTURE_V1" in subm_content

    # Verify CEA emission factor provenance
    assert "0.716" in meth_content or "0.71" in meth_content
    assert "Central Electricity Authority" in meth_content
    assert "0.716" in evid_content or "CEA" in evid_content

    # Verify Section 32 tax disclaimer
    assert "Section 32" in meth_content
    assert "Not formal tax or legal advice" in meth_content
    assert "Section 32" in evid_content

    # Verify truth-in-advertising disclaimers
    assert "No Live Hardware Telemetry Claimed" in meth_content
    assert "synthetic" in subm_content.lower()


def test_cea_emission_factor_provenance_in_engine():
    """Verify that CEA baseline emission factor dictionary exists in the Digital Twin engine."""
    assert "Northern" in CEA_GRID_EMISSION_FACTORS
    assert "Western" in CEA_GRID_EMISSION_FACTORS
    assert "National Average" in CEA_GRID_EMISSION_FACTORS
    engine = DigitalTwinEngine(region="Northern")
    assert abs(engine.grid_factor - 0.71) < 1e-4


def test_tax_regime_defaults_and_wdv_rates():
    """Verify statutory WDV rate assumptions in TAX_REGIMES dictionary."""
    assert "SECTION_32_RENEWABLE_40_WDV" in TAX_REGIMES
    sec32 = TAX_REGIMES["SECTION_32_RENEWABLE_40_WDV"]
    assert abs(sec32["depreciation_rate_pct"] - 40.0) < 1e-4
    assert abs(sec32["corporate_tax_rate_pct"] - 25.17) < 1e-4
    assert "Section 32(1)" in sec32["statutory_reference"]


def test_demo_fixture_labeled_synthetic():
    """Verify that the demo runner and fixture explicitly label the scenario as synthetic benchmark."""
    assert DEMO_BENCHMARK_FIXTURE_V1["fixture_id"] == "STEEL_BENCHMARK_FIXTURE_V1"
    assert "synthetic" in DEMO_BENCHMARK_FIXTURE_V1["disclaimer"].lower()

    runner = IndustrialDemoRunner()
    summary = runner.run_full_sequence()
    assert summary["status"] == "COMPLETE_AND_VERIFIED"
    assert "synthetic" in DEMO_BENCHMARK_FIXTURE_V1["disclaimer"].lower()
    assert "No live unverified plant telemetry" in summary["provenance_statement"]
