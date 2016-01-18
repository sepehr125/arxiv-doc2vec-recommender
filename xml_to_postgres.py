# -*- coding: utf-8 -*-
import psycopg2
import os
from xml.etree import ElementTree as ET
from datetime import datetime
import argparse

"""
Example:

    $ python xml_to_postgres.py path/to/xml_dir arxiv_db

Parse XML files in a given directory for the following fields:
- title
- authors
- subject
- abstract
- last_submitted
- arxiv_id
and insert into a PostgreSQL database. 

Note: The database must already exist!
See harvest.py for more information on how XML files were retrieved.

Below is a sample XML file. 

<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.openarchives.org/OAI/2.0/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
 <dc:title>Dimensionality and dynamics in the behavior of C. elegans</dc:title>
 <dc:creator>Stephens, Greg J</dc:creator>
 <dc:creator>Johnson-Kerner, Bethany</dc:creator>
 <dc:creator>Bialek, William</dc:creator>
 <dc:creator>Ryu, William S</dc:creator>
 <dc:subject>Quantitative Biology - Other Quantitative Biology</dc:subject>
 <dc:description>  A major challenge in analyzing animal behavior is to discover some underlying
simplicity in complex motor actions. Here we show that the space of shapes
adopted by the nematode C. elegans is surprisingly low dimensional, with just
four dimensions accounting for 95% of the shape variance, and we partially
reconstruct "equations of motion" for the dynamics in this space. These
dynamics have multiple attractors, and we find that the worm visits these in a
rapid and almost completely deterministic response to weak thermal stimuli.
Stimulus-dependent correlations among the different modes suggest that one can
generate more reliable behaviors by synchronizing stimuli to the state of the
worm in shape space. We confirm this prediction, effectively "steering" the
worm in real time.
</dc:description>
 <dc:description>Comment: 9 pages, 6 figures, minor corrections</dc:description>
 <dc:date>2007-05-11</dc:date>
 <dc:date>2007-05-16</dc:date>
 <dc:type>text</dc:type>
 <dc:identifier>http://arxiv.org/abs/0705.1548</dc:identifier>
 <dc:identifier>PLoS Comput Biol 4(4): e1000028 (2008)</dc:identifier>
 <dc:identifier>doi:10.1371/journal.pcbi.1000028</dc:identifier>
 </oai_dc:dc>
"""


def get_fields(file_path):
    """
    Calls helper functions below to 
    gather fields into a tuple. 
    This tuple is used as input to 
    PostgreSQL INSERT command later,
    which will take of any missing value problems.
    We do, however, prevent error being raised
    by exiting early if file is not XML.

    Args:
        file_path (str): Path to XML file
    
    Returns:
        tuple: (title, authors, subject, 
                abstract, last_submitted, arxiv_id)
        bool: False if file is not xml
    """

    if not file_path.endswith('.xml'):
        return False
    tree = ET.parse(file_path)
    root = tree.getroot()
    title = get_title(root)
    authors = get_authors(root)
    subject = get_subject(root)
    abstract = get_abstract(root)
    last_submitted = get_date(root)
    arxiv_id = get_arxivid(root)
    return (title, authors, subject, abstract, last_submitted, arxiv_id)


def get_title(root):
    """
    Args:
        root (Element): ElementTree root element
    
    Returns:
        str: title
        None: if no match is found
    """
    tag = '{http://purl.org/dc/elements/1.1/}title'
    title = root.find(tag)
    if title:
        # calling .text on None raises error
        return title.text


def get_authors(root, sep='|'):
    """
    Args:
        root (Element): ElementTree root element
        sep (str): character to separate authors
    
    Returns:
        str: authors ('creator' field in XML), 
            separated by given separator
        None: if no match is found
    """
    tag = '{http://purl.org/dc/elements/1.1/}creator'
    authors = root.findall(tag)
    if authors:
        # calling .text on None raises error
        authors = sep.join([el.text for el in authors])
        return authors


def get_subject(root):
    """
    Args:
        root (Element): ElementTree root element
    
    Returns:
        str: The first subject tag (not sure if some have more)
        None: if no match is found
    """
    tag = '{http://purl.org/dc/elements/1.1/}subject'
    subject = root.find(tag)
    if subject:
        # calling .text on None raises error
        return subject.text


def get_abstract(root):
    """
    There are two elements with the `description` tag name.
    The longer one is the abstract.

    Args:
        root (Element): ElementTree root element
    
    Returns:
        str: The longer field named "description"
        bool: False if file is not xml
    """
    tag = '{http://purl.org/dc/elements/1.1/}description'
    descriptions = root.findall(tag)
    if descriptions:
        abstract = max([el.text for el in descriptions], key=len) 
        return abstract


def get_arxivid(root):
    """
    The arxiv id is hidden among several fields all
    with the tag name "identifier".
    Fortunately, the arxiv id is the full URL at arxiv.org
    for the abstract, so we can identify them checking
    if they contain 'arxiv.org'

    Args:
        root (Element): ElementTree root element
    
    Returns:
        str: URL of abstract on arxiv.org
        None: if no identifier looking like an arxiv URL exists
    """
    tag = '{http://purl.org/dc/elements/1.1/}identifier'
    ids = root.findall(tag)
    if ids:
        for el in ids:
            if el.text.startswith('http://arxiv.org/abs/'):
                return el.text


def get_date(root):
    """
    Submission dates are all recorded as strings
    We parse them as datetime, and return the latest one.

    Args:
        root (Element): ElementTree root element
    
    Returns:
        datetime: last submitted date
        None: if no match is found
    """

    tag = '{http://purl.org/dc/elements/1.1/}date'
    date_list = root.findall(tag)
    if date_list:
        dates = [datetime.strptime(el.text, "%Y-%m-%d").date() for el in date_list]
        return (max(dates))


def chunker(seq, size):
    """
    Split up a list into chunks. 
    This is good for processing files in batches
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=
        'Parses xml files for fields and inserts into database')
    parser.add_argument('data_dir', help="Path to data folder")
    parser.add_argument('dbname', help="Name of **existing** postgres database.")
    args = parser.parse_args()

    """
    Make sure given database (dbname) exists
    """
    try:
        conn = psycopg2.connect(dbname=args.dbname)
    except:
        raise ValueError("Database not exists")

    """
    Make sure given directory (data_dir) exists
    """
    try:
        filenames = os.listdir(args.data_dir)
    except:
        raise ValueError("Directory not found")


    """
    No errors!?
    Connect to database,
    Make table if it doesn't exist,
    Loop over files in batches,
    and perform inserts.
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
            # I think there's a way to make this faster
            # by making one long statement, if 
            query_template = """
                INSERT INTO articles 
                (title, authors, subject, abstract, last_submitted, arxiv_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            print("Processing %d files in batches of %d..."%(len(filenames), batch_size))
            for batch in chunker(filenames, batch_size):
                skips = 0
                for fname in batch:
                    file_path = os.path.join(args.data_dir, fname)
                    values = get_fields(file_path)
                    # try and except should be fast enough for most cases, 
                    # unless there are a lot duplicates to skip.
                    try:
                        cur.execute(query_template, values)
                    except psycopg2.IntegrityError:
                        # record already exists
                        skips += 1
                        conn.rollback()
                        continue
                """Write the batch to disk in order to free memory"""
                conn.commit()
                print("batch %d, skipped %d"%(batch_num, skips))
                batch_num += 1
