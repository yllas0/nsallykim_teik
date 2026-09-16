import csv
import sqlite3
from pathlib import Path

CSV_PATH = Path("cell-count.csv")
DB_PATH = Path("cell_counts.db")

# There are five populations: b_cell, cd8_t_cell, cd4_t_cell, nk_cell, and monocyte. Each row in the file corresponds to a biological sample.
POP = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            sample TEXT PRIMARY KEY,
            project TEXT,
            condition TEXT,
            age INTEGER,
            sex TEXT,
            treatment TEXT,
            response TEXT,
            subject TEXT,
            sample_type TEXT,
            time_from_treatment_start INTEGER
            )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cell_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT NOT NULL,
            population TEXT NOT NULL,
            count INTEGER NOT NULL,
            FOREIGN KEY (sample) REFERENCES samples(sample)
        );
    """)

def load_csv(conn: sqlite3.Connection, csv_path: Path) -> None:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        sample_rows = []
        count_rows = []

        for row in reader:
            sample_rows.append((
                row["sample"],
                row.get("project"),
                row.get("condition"),
                row.get("age"),
                row.get("sex"),
                row.get("treatment"),
                row.get("response"),
                row.get("subject"),
                row.get("sample_type"),
                row.get("time_from_treatment_start"),
            ))

            for population in POP:
                if population in fieldnames:
                    count_rows.append((
                        row["sample"],
                        population,
                        int(row[population]),
                    ))

    conn.executemany(
        """
        INSERT OR REPLACE INTO samples
            (sample, project, condition, age, sex, treatment,
            response, subject, sample_type, time_from_treatment_start)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample_rows,
    )

    conn.executemany(
        """
        INSERT INTO cell_counts
            (sample, population, count)
        VALUES(?, ?, ?)
        """,
        count_rows,
    )

def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError();

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    try:
        create_schema(conn)
        load_csv(conn, CSV_PATH)
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

