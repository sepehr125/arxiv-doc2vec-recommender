import psycopg2
import argparse

if __name__ == '__main__':

    # make a table of distinct subjects 
    # and add a column to the articles table
    # that references the subject by ID
    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor() as cur:

            make_table = """CREATE TABLE IF NOT EXISTS 
                subjects 
                AS SELECT 
                    DISTINCT subject FROM articles;
                """
            cur.execute(make_table)

            add_index = "ALTER TABLE subjects ADD COLUMN subject_id serial PRIMARY KEY"
            cur.execute(add_index)

            add_col = "ALTER TABLE articles ADD COLUMN subject_id int"
            cur.execute(add_col)

            fill_col = """
            UPDATE articles a
            SET subject_id = s.index 
            FROM subjects s
            where s.subject = a.subject"""
            cur.execute(fill_col)
