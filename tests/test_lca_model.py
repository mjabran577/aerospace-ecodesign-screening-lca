from pathlib import Path

import pytest

from lca_model import run_all, validate_scenario


def test_scenario_fractions_must_sum_to_one():
    bad = {
        "material_input_kg": 10,
        "primary_aluminium_fraction": 0.8,
        "recycled_aluminium_fraction": 0.3,
        "manufacturing_electricity_kwh": 10,
        "supplier_transport_km": 100,
        "end_of_life_recovery_rate": 0.9,
    }
    with pytest.raises(ValueError, match="fractions must equal 1.0"):
        validate_scenario(bad)


def test_baseline_is_higher_than_combined_ecodesign():
    df = run_all(Path("data/scenarios.json"), Path("data/emission_factors.csv"))
    base = df.loc[df["scenario"] == "baseline", "screening_climate_total"].iloc[0]
    eco = df.loc[df["scenario"] == "combined_ecodesign", "screening_climate_total"].iloc[0]
    assert eco < base


def test_reduction_vs_baseline_is_zero_for_baseline():
    df = run_all(Path("data/scenarios.json"), Path("data/emission_factors.csv"))
    value = df.loc[df["scenario"] == "baseline", "reduction_vs_baseline_pct"].iloc[0]
    assert abs(value) < 1e-9
