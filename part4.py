import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("cell_counts.db")


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError("do load_data first")
    return sqlite3.connect(DB_PATH)


def get_baseline_subset(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT sample, project, subject, condition, sex, response, treatment, sample_type
        FROM samples
        WHERE condition = 'melanoma'
          AND sample_type = 'PBMC'
          AND treatment = 'miraclib'
          AND time_from_treatment_start = 0
    """
    return pd.read_sql_query(query, conn)


def summarize_baseline_subset(df: pd.DataFrame) -> None:
    print("Baseline melanoma / PBMC / miraclib subset\n")

    print(f"Total samples: {len(df)}")
    print(f"Total distinct subjects: {df['subject'].nunique()}\n")

    print("Samples per project:")
    print(df.groupby("project")["sample"].count().to_string(), "\n")

    subjects = df.drop_duplicates(subset="subject")

    print("Subjects by response:")
    print(subjects["response"].value_counts().to_string(), "\n")

    print("Subjects by sex:")
    print(subjects["sex"].value_counts().to_string(), "\n")


def average_b_cells_melanoma_male_responders(conn: sqlite3.Connection) -> float:
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
        raise ValueError("no matching rows found for melanoma male responders at time=0")

    return round(df["count"].mean(), 2)


def main() -> None:
    conn = get_connection()
    try:
        baseline_df = get_baseline_subset(conn)
        summarize_baseline_subset(baseline_df)

        avg_b_cells = average_b_cells_melanoma_male_responders(conn)
        print(f"Average B cell count (melanoma, male, responders, time=0): {avg_b_cells:.2f}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()