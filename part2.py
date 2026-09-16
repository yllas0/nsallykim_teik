import sqlite3
from pathlib import Path

DB_PATH = Path("cell_counts.db")

def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError("do load_data first")
    return sqlite3.connect(DB_PATH)

def freqcompute(conn: sqlite3.Connection) -> list[tuple]:
    # calculatin totals
    totals_curs = conn.execute("""
        SELECT sample, SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample
    """)

    totals = {sample: total for sample, total in totals_curs.fetchall()}

    # per pop
    counts_curs = conn.execute("""
        SELECT sample, population, count
        FROM cell_counts
        ORDER BY sample, population
    """)

    results=  []

    for sample, population, count in counts_curs.fetchall():
        total_count = totals[sample]
        percentage = (count / total_count) * 100 if total_count else 0
        results.append((sample, total_count, population, count, round(percentage, 2)))

    return results

def maketable(rows:list[tuple]) -> None:
    header = ("sample", "total_count", "population", "count", "percentage")
    print(f"{header[0]:<14}{header[1]:<14}{header[2]:<14}{header[3]:<10}{header[4]:<10}")
    for sample, total_count, population, count, percentage in rows:
        print(f"{sample:<14}{total_count:<14}{population:<14}{count:<10}{percentage:<10}")


def main():
    conn = get_connection()

    try:
        rows = freqcompute(conn)
        maketable(rows)
    finally:
        conn.close()
    

if __name__ == "__main__":
    main()