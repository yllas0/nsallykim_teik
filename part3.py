import sqlite3
from pathlib import Path

import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt

DB_PATH = Path("cell_counts.db")


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError("do load_data first")
    return sqlite3.connect(DB_PATH)


def load_responder_frequencies(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            cc.sample,
            s.response,
            cc.population,
            cc.count,
            totals.total_count
        FROM cell_counts cc
        JOIN samples s ON cc.sample = s.sample
        JOIN (
            SELECT sample, SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample
        ) totals ON cc.sample = totals.sample
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND s.sample_type = 'PBMC'
          AND s.response IN ('yes', 'no')
    """
    df = pd.read_sql_query(query, conn)
    df["percentage"] = (df["count"] / df["total_count"]) * 100
    return df


def plot_boxplots(df: pd.DataFrame, output_path: str = "boxplot_responder_vs_non_responder.png") -> None:
    populations = sorted(df["population"].unique())
    fig, axes = plt.subplots(1, len(populations), figsize=(4 * len(populations), 5), sharey=False)

    if len(populations) == 1:
        axes = [axes]

    for ax, population in zip(axes, populations):
        subset = df[df["population"] == population]
        responders = subset[subset["response"] == "yes"]["percentage"]
        non_responders = subset[subset["response"] == "no"]["percentage"]

        ax.boxplot([responders, non_responders], tick_labels=["Responder", "Non-responder"])
        ax.set_title(population)
        ax.set_ylabel("Relative frequency (%)")

    fig.suptitle("Cell Population Frequencies: Responders vs Non-Responders (Melanoma, PBMC, miraclib)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    print(f"Saved boxplot to {output_path}")


def run_significance_tests(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for population in sorted(df["population"].unique()):
        subset = df[df["population"] == population]
        responders = subset[subset["response"] == "yes"]["percentage"]
        non_responders = subset[subset["response"] == "no"]["percentage"]

        stat, p_value = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")

        results.append({
            "population": population,
            "n_responders": len(responders),
            "n_non_responders": len(non_responders),
            "median_responder_pct": round(responders.median(), 2),
            "median_non_responder_pct": round(non_responders.median(), 2),
            "p_value": round(p_value, 4),
            "significant_p<0.05": p_value < 0.05,
        })

    return pd.DataFrame(results)


def main() -> None:
    conn = get_connection()
    try:
        df = load_responder_frequencies(conn)
    finally:
        conn.close()

    if df.empty:
        return

    plot_boxplots(df)

    results = run_significance_tests(df)
    print(results.to_string(index=False))

    results.to_csv("response_significance_results.csv", index=False)
    print("\nSaved results table to response_significance_results.csv")


if __name__ == "__main__":
    main()