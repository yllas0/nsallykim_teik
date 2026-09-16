import json
import sqlite3
from pathlib import Path

import pandas as pd
from flask import Flask, render_template
from scipy import stats

DB_PATH = Path("cell_counts.db")

app = Flask(__name__)


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} not found — run `python load_data.py` first.")
    return sqlite3.connect(DB_PATH)


# Part 2: freq table
def freqcompute(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            cc.sample,
            totals.total_count,
            cc.population,
            cc.count
        FROM cell_counts cc
        JOIN (
            SELECT sample, SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample
        ) totals ON cc.sample = totals.sample
        ORDER BY cc.sample, cc.population
    """
    df = pd.read_sql_query(query, conn)
    df["percentage"] = round((df["count"] / df["total_count"]) * 100, 2)
    return df


# Part 3: responder vs non-responder 
def compute_response_analysis(conn: sqlite3.Connection) -> dict:
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
    if df.empty:
        return {"raw": [], "stats": []}

    df["percentage"] = (df["count"] / df["total_count"]) * 100

    stats_rows = []
    boxplot_data = {}
    for population in sorted(df["population"].unique()):
        subset = df[df["population"] == population]
        responders = subset[subset["response"] == "yes"]["percentage"]
        non_responders = subset[subset["response"] == "no"]["percentage"]

        _, p_value = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")

        stats_rows.append({
            "population": population,
            "n_responders": int(len(responders)),
            "n_non_responders": int(len(non_responders)),
            "median_responder_pct": round(float(responders.median()), 2),
            "median_non_responder_pct": round(float(non_responders.median()), 2),
            "p_value": round(float(p_value), 4),
            "significant": bool(p_value < 0.05),
        })

        boxplot_data[population] = {
            "responder": [round(v, 2) for v in responders.tolist()],
            "non_responder": [round(v, 2) for v in non_responders.tolist()],
        }

    return {"stats": stats_rows, "boxplot": boxplot_data}


# Part 4: baseline subset 
def compute_baseline_subset(conn: sqlite3.Connection) -> dict:
    query = """
        SELECT sample, project, subject, sex, response
        FROM samples
        WHERE condition = 'melanoma'
          AND sample_type = 'PBMC'
          AND treatment = 'miraclib'
          AND time_from_treatment_start = 0
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        return {
            "total_samples": 0, "total_subjects": 0,
            "by_project": {}, "by_response": {}, "by_sex": {},
        }

    subjects = df.drop_duplicates(subset="subject")

    return {
        "total_samples": int(len(df)),
        "total_subjects": int(df["subject"].nunique()),
        "by_project": df.groupby("project")["sample"].count().to_dict(),
        "by_response": subjects["response"].value_counts().to_dict(),
        "by_sex": subjects["sex"].value_counts().to_dict(),
    }


def compute_avg_b_cells_male_responders(conn: sqlite3.Connection) -> float | None:
    query = """
        SELECT cc.count
        FROM cell_counts cc
        JOIN samples s ON cc.sample = s.sample
        WHERE s.condition = 'melanoma'
          AND s.sex = 'M'
          AND s.response = 'yes'
          AND s.time_from_treatment_start = 0
          AND cc.population = 'b_cell'
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        return None
    return round(float(df["count"].mean()), 2)


def build_dashboard_payload() -> dict:
    conn = get_connection()
    try:
        freq_df = freqcompute(conn)
        response = compute_response_analysis(conn)
        baseline = compute_baseline_subset(conn)
        avg_b_cells = compute_avg_b_cells_male_responders(conn)
    finally:
        conn.close()

    return {
        "frequency": freq_df.to_dict(orient="records"),
        "response_stats": response["stats"],
        "response_boxplot": response.get("boxplot", {}),
        "baseline": baseline,
        "avg_b_cells_male_responders": avg_b_cells,
    }


@app.route("/")
def index():
    payload = build_dashboard_payload()
    return render_template("dashboard.html", data_json=json.dumps(payload))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)