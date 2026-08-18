"""Transparent screening-LCA / Ecodesign scenario model.

This portfolio model is intentionally deterministic:
activity data × controlled factor = impact result.

It is not a certified ISO-compliant LCA and should not be used for external
environmental claims. The purpose is to demonstrate reproducible LCA-tool
engineering, scenario analysis, hotspot identification and sensitivity checks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


def load_factors(path: Path) -> pd.DataFrame:
    factors = pd.read_csv(path)
    required = {
        "factor_id", "activity", "unit", "factor", "impact_unit",
        "source", "source_year", "geography", "system_boundary", "quality_note"
    }
    missing = required.difference(factors.columns)
    if missing:
        raise ValueError(f"Factor file missing columns: {sorted(missing)}")
    return factors


def factor_for(factors: pd.DataFrame, activity: str) -> pd.Series:
    rows = factors.loc[factors["activity"] == activity]
    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one controlled factor for '{activity}', found {len(rows)}"
        )
    return rows.iloc[0]


def validate_scenario(s: Dict[str, float]) -> None:
    p = float(s["primary_aluminium_fraction"])
    r = float(s["recycled_aluminium_fraction"])
    if not abs((p + r) - 1.0) < 1e-9:
        raise ValueError("Primary + recycled aluminium fractions must equal 1.0.")
    for key in (
        "material_input_kg",
        "manufacturing_electricity_kwh",
        "supplier_transport_km",
        "end_of_life_recovery_rate",
    ):
        if float(s[key]) < 0:
            raise ValueError(f"{key} cannot be negative.")
    if not 0 <= float(s["end_of_life_recovery_rate"]) <= 1:
        raise ValueError("end_of_life_recovery_rate must be between 0 and 1.")


def calculate_scenario(name: str, s: Dict[str, float], factors: pd.DataFrame) -> Dict[str, float]:
    validate_scenario(s)

    primary = factor_for(factors, "primary_aluminium")
    recycled = factor_for(factors, "recycled_aluminium")
    electricity = factor_for(factors, "electricity")
    freight = factor_for(factors, "road_freight")

    mass = float(s["material_input_kg"])
    primary_mass = mass * float(s["primary_aluminium_fraction"])
    recycled_mass = mass * float(s["recycled_aluminium_fraction"])

    primary_impact = primary_mass * float(primary["factor"])
    recycled_impact = recycled_mass * float(recycled["factor"])
    electricity_impact = (
        float(s["manufacturing_electricity_kwh"]) * float(electricity["factor"])
    )

    tonne_km = (mass / 1000.0) * float(s["supplier_transport_km"])
    freight_impact = tonne_km * float(freight["factor"])

    # No avoided-burden credit is assigned. End-of-life is reported as a mass-flow
    # indicator because allocation/substitution choices would materially affect results.
    recovered_mass = mass * float(s["end_of_life_recovery_rate"])

    total = primary_impact + recycled_impact + electricity_impact + freight_impact

    return {
        "scenario": name,
        "material_input_kg": mass,
        "primary_material_impact": primary_impact,
        "recycled_material_impact": recycled_impact,
        "manufacturing_electricity_impact": electricity_impact,
        "road_freight_impact": freight_impact,
        "screening_climate_total": total,
        "recovered_mass_kg": recovered_mass,
        "recovery_rate": float(s["end_of_life_recovery_rate"]),
    }


def run_all(scenarios_path: Path, factors_path: Path) -> pd.DataFrame:
    config = json.loads(scenarios_path.read_text(encoding="utf-8"))
    factors = load_factors(factors_path)
    rows = [
        calculate_scenario(name, data, factors)
        for name, data in config["scenarios"].items()
    ]
    df = pd.DataFrame(rows)
    baseline = float(df.loc[df["scenario"] == "baseline", "screening_climate_total"].iloc[0])
    df["reduction_vs_baseline_pct"] = (
        (baseline - df["screening_climate_total"]) / baseline * 100
    )
    return df


def hotspot_table(row: pd.Series) -> pd.DataFrame:
    records = [
        ("Primary aluminium", row["primary_material_impact"]),
        ("Recycled aluminium", row["recycled_material_impact"]),
        ("Manufacturing electricity", row["manufacturing_electricity_impact"]),
        ("Road freight", row["road_freight_impact"]),
    ]
    df = pd.DataFrame(records, columns=["stage", "impact"])
    total = df["impact"].sum()
    df["share_pct"] = df["impact"] / total * 100
    return df.sort_values("impact", ascending=False)


def sensitivity_analysis(
    scenario: Dict[str, float],
    factors: pd.DataFrame,
    variation: float = 0.20,
) -> pd.DataFrame:
    """One-at-a-time sensitivity of the combined Ecodesign scenario."""
    base = calculate_scenario("base", scenario, factors)["screening_climate_total"]
    rows = []

    factor_activities = ["primary_aluminium", "recycled_aluminium", "electricity", "road_freight"]
    for activity in factor_activities:
        for direction, multiplier in [("low", 1 - variation), ("high", 1 + variation)]:
            changed = factors.copy()
            idx = changed.index[changed["activity"] == activity]
            changed.loc[idx, "factor"] = changed.loc[idx, "factor"] * multiplier
            result = calculate_scenario("sensitivity", scenario, changed)["screening_climate_total"]
            rows.append({
                "parameter": f"{activity}_factor",
                "direction": direction,
                "variation_pct": (multiplier - 1) * 100,
                "result": result,
                "change_vs_base_pct": (result - base) / base * 100,
            })

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run aerospace screening LCA scenarios.")
    parser.add_argument("--scenarios", type=Path, default=Path("data/scenarios.json"))
    parser.add_argument("--factors", type=Path, default=Path("data/emission_factors.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    results = run_all(args.scenarios, args.factors)
    results.to_csv(args.output_dir / "scenario_results.csv", index=False)

    baseline = results.loc[results["scenario"] == "baseline"].iloc[0]
    hotspot_table(baseline).to_csv(args.output_dir / "baseline_hotspots.csv", index=False)

    config = json.loads(args.scenarios.read_text(encoding="utf-8"))
    factors = load_factors(args.factors)
    sensitivity = sensitivity_analysis(config["scenarios"]["combined_ecodesign"], factors)
    sensitivity.to_csv(args.output_dir / "sensitivity_results.csv", index=False)

    evidence_cols = [
        "factor_id", "activity", "factor", "unit", "impact_unit", "source",
        "source_year", "geography", "system_boundary", "quality_note"
    ]
    factors[evidence_cols].to_csv(args.output_dir / "factor_evidence.csv", index=False)

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
