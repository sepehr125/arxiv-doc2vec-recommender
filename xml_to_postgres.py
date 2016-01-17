import psycopg2
import os
from xml.etree import ElementTree as ET
from datetime import datetime
import argparse

"""
HELPER FUNCTIONS
"""
def get_title(root):
    tag = '{http://purl.org/dc/elements/1.1/}title'
    els = root.findall(tag)
    return els.pop().text

def get_authors(root, sep='|'):
    tag = '{http://purl.org/dc/elements/1.1/}creator'
    els = root.findall(tag)
    authors = sep.join([el.text for el in els])
    return authors

def get_subject(root):
    tag = '{http://purl.org/dc/elements/1.1/}subject'
    subject = root.find(tag).text # just return the first one
    return subject

def get_abstract(root):
    tag = '{http://purl.org/dc/elements/1.1/}description'
    els = root.findall(tag)
    abstract = max([el.text for el in els], key=len) # shorter description is comment
    cleaned = abstract.replace('\n', ' ').strip()
    return cleaned

def get_arxivid(root):
    tag = '{http://purl.org/dc/elements/1.1/}identifier'
    els = root.findall(tag)
    for el in els:
        if el.text.startswith('http://arxiv.org/abs/'):
            return el.text
    return None

def get_date(root):
    tag = '{http://purl.org/dc/elements/1.1/}date'
    els = root.findall(tag)
    dates = [datetime.strptime(el.text, "%Y-%m-%d").date() for el in els]
    return (max(dates))


"""
This just combines the above helper functions
that fetch specific fields from xml.
Returns tuple of the needed fields
"""
def make_row(f_path):
    tree = ET.parse(f_path)
    root = tree.getroot()
    # get (title, authors, subject, abstract, date, arxiv_id)
    title = get_title(root)
    authors = get_authors(root)
    subject = get_subject(root)
    abstract = get_abstract(root)
    last_submitted = get_date(root)
    arxiv_id = get_arxivid(root)
    return (title, authors, subject, abstract, last_submitted, arxiv_id)



def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Parses xml files for fields and inserts into database')
    parser.add_argument('data_dir', help="Path to data folder")
    parser.add_argument('dbname', help="Name of **existing** postgres database.")
    args = parser.parse_args()

    """
    Make sure given data_dir and dbname exist
    """
    try:
        conn = psycopg2.connect(dbname=args.dbname)
    except:
        raise ValueError("Database not exists")

    try:
        filenames = os.listdir(args.data_dir)
    except:
        raise ValueError("Directory not found")

    """
    MAIN BLOCK:
    Create schema if it doesn't exist
    and perform inserts
    """
    with psycopg2.connect(dbname=args.dbname) as conn:
        with conn.cursor() as cur:
            
            sql_create = """CREATE TABLE IF NOT EXISTS articles (
                        index serial PRIMARY KEY,
                        title text,
                        authors text,
                        subject text,
                        abstract text,
                        last_submitted date,
                        arxiv_id text UNIQUE
                    )"""
            cur.execute(sql_create)
            conn.commit()

            """
            Prepare to insert rows in batches
            Using batches helps speed tremendously (~100x)
            """
            batch_size = 1000
            batch_num = 1
            query_template = """
                INSERT INTO articles 
                (title, authors, subject, abstract, last_submitted, arxiv_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            print("Processing %d files in batches of %d..."%(len(filenames), batch_size))
            for batch in chunker(filenames, batch_size):
                skips = 0
                for fname in batch:
                    f_path = os.path.join(args.data_dir, fname)
                    values = make_row(f_path)
                    try:
                        cur.execute(query_template, values)
                    except psycopg2.IntegrityError:
                        skips += 1
                        conn.rollback()
                        continue
                """Write the batch to disk in order to free memory"""
                conn.commit()
                print("batch %d, skipped %d"%(batch_num, skips))
                batch_num += 1
