import sqlite3
import os

def dump_all_tables_with_count(database_path):
    """
    Connect to the SQLite database and dump all rows from all tables, including row counts.
    Excludes 'context_snippet' column for the 'CrawlResults' table.
    :param database_path: Path to the SQLite database file.
    """
    if not os.path.exists(database_path):
        print(f"Database file {database_path} does not exist.")
        return

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Fetch all table names in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        # Iterate through each table and dump its contents with row count
        for table in tables:
            table_name = table[0]
            print(f"\n--- Dumping Table: {table_name} ---\n")

            # Query to count the rows in the table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"Row Count: {row_count}")

            if table_name == "CrawlResults":
                # Exclude 'context_snippet' column for 'CrawlResults'
                cursor.execute("PRAGMA table_info(CrawlResults)")
                columns_info = cursor.fetchall()
                column_names = [col[1] for col in columns_info if col[1] != "context_snippet"]

                # Query to fetch all rows excluding 'context_snippet'
                columns_to_select = ", ".join(column_names)
                cursor.execute(f"SELECT {columns_to_select} FROM {table_name}")
            else:
                # Query to fetch all rows from the table
                cursor.execute(f"SELECT * FROM {table_name}")
                column_names = [description[0] for description in cursor.description]

            # Fetch rows and print results
            rows = cursor.fetchall()
            print(f"Columns: {', '.join(column_names)}")

            # Print each row
            for row in rows:
                print(row)

        # Close the database connection
        cursor.close()
        conn.close()

    except sqlite3.Error as e:
        print(f"Error reading data from SQLite database: {e}")

if __name__ == "__main__":
    # Path to the SQLite database file
    database_file = "results.sqlite3"
    dump_all_tables_with_count(database_file)
