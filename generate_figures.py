"""Generate portfolio figures from the deterministic LCA result CSV files."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")


def scenario_comparison(results: pd.DataFrame) -> None:
    labels = {
        "baseline": "Baseline",
        "high_recycled_content": "High recycled",
        "lightweight_design": "Lightweight",
        "combined_ecodesign": "Combined Ecodesign",
    }
    plot_data = results.copy()
    plot_data["label"] = plot_data["scenario"].map(labels)

    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.bar(plot_data["label"], plot_data["screening_climate_total"])
    ax.set_ylabel("Screening climate indicator")
    ax.set_title("Ecodesign scenario comparison")
    ax.tick_params(axis="x", rotation=15)
    for bar, value in zip(bars, plot_data["screening_climate_total"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "scenario_comparison.svg")
    plt.close(fig)


def baseline_hotspots(hotspots: pd.DataFrame) -> None:
    plot_data = hotspots.sort_values("impact")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.barh(plot_data["stage"], plot_data["impact"])
    ax.set_xlabel("Impact contribution")
    ax.set_title("Baseline hotspot analysis")
    for bar, value in zip(bars, plot_data["impact"]):
        ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f" {value:.2f}",
            va="center",
        )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "baseline_hotspots.svg")
    plt.close(fig)


def sensitivity_chart(sensitivity: pd.DataFrame) -> None:
    data = sensitivity.copy()
    data["parameter"] = data["parameter"].str.replace("_factor", "", regex=False)
    magnitudes = (
        data.groupby("parameter")["change_vs_base_pct"]
        .apply(lambda values: values.abs().max())
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.barh(magnitudes.index, magnitudes.values)
    ax.set_xlabel("Maximum absolute result change (%) for ±20% factor variation")
    ax.set_title("Sensitivity of combined Ecodesign scenario")
    for bar, value in zip(bars, magnitudes.values):
        ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f" {value:.2f}%",
            va="center",
        )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "sensitivity.svg")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(RESULTS_DIR / "scenario_results.csv")
    hotspots = pd.read_csv(RESULTS_DIR / "baseline_hotspots.csv")
    sensitivity = pd.read_csv(RESULTS_DIR / "sensitivity_results.csv")

    scenario_comparison(results)
    baseline_hotspots(hotspots)
    sensitivity_chart(sensitivity)

    print(f"Figures written to {FIGURES_DIR.resolve()}")


if __name__ == "__main__":
    main()
