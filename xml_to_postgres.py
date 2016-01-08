
# coding: utf-8

# In[250]:

import psycopg2
import os
from xml.etree import ElementTree as ET
from datetime import datetime


# In[228]:

def get_title(xmlroot):
    tag = '{http://purl.org/dc/elements/1.1/}title'
    els = root.findall(tag)
    return els.pop().text


# In[229]:

def get_authors(xmlroot, sep='|'):
    tag = '{http://purl.org/dc/elements/1.1/}creator'
    els = root.findall(tag)
    authors = sep.join([el.text for el in els])
    return authors


# In[241]:

def get_subject(xmlroot):
    tag = '{http://purl.org/dc/elements/1.1/}subject'
    subject = root.find(tag).text # just return the first one
    return subject


# In[300]:

def get_abstract(xmlroot):
    tag = '{http://purl.org/dc/elements/1.1/}description'
    els = root.findall(tag)
    abstract = max([el.text for el in els], key=len) # shorter description is comment
    cleaned = abstract.replace('\n', ' ').strip()
    return cleaned


# In[239]:

def get_arxivid(xmlroot):
    tag = '{http://purl.org/dc/elements/1.1/}identifier'
    els = root.findall(tag)
    for el in els:
        if el.text.startswith('http://arxiv.org/abs/'):
            return el.text.split('/').pop()
    return None


# In[274]:

def get_date(xmlroot):
    tag = '{http://purl.org/dc/elements/1.1/}date'
    els = root.findall(tag)
    dates = [datetime.strptime(el.text, "%Y-%m-%d").date() for el in els]
    return (max(dates))


# In[314]:

data_dir = '/Users/Sepehr/dev/data-projects/arxiv-doc2vec-recommender/data/'
filenames = os.listdir(data_dir)
path_to_xml_file = data_dir + filenames[120]
# test xml unpacking on a sample file
tree = ET.parse(path_to_xml_file)
root = tree.getroot()


# In[181]:

# see fields in sample xml file:
for child in root:
    print(child.tag)


# In[271]:

print(get_title(root))
print(get_arxivid(root))
print(get_subjects(root))
print(get_abstract(root))
print(get_authors(root))


# In[272]:

def create_schema(dbname='arxiv'):
    conn = psycopg2.connect(dbname=dbname)
    cur = conn.cursor()
    
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
    conn.close()


# In[273]:

create_schema()


# In[301]:

def get_fields_from_xml(path_to_xml_file):
    tree = ET.parse(path_to_xml_file)
    root = tree.getroot()
    # get (title, authors, subject, abstract, date, arxiv_id)
    title = get_title(root)
    authors = get_authors(root)
    subject = get_subject(root)
    abstract = get_abstract(root)
    last_submitted = get_date(root)
    arxiv_id = get_arxivid(root)
    return (title, authors, subject, abstract, last_submitted, arxiv_id)


# In[312]:

def insert_xml_into_postgres(path_to_xml_file):
    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor() as cur:
            query_template = "INSERT INTO articles (title, authors, subject, abstract, last_submitted, arxiv_id) VALUES (%s, %s, %s, %s, %s, %s)"
            values = get_fields_from_xml(path_to_xml_file)
            insert_query = cur.mogrify(query_template, values)
            cur.execute(insert_query)
            conn.commit()


# In[315]:

insert_xml_into_postgres(path_to_xml_file)


# In[ ]:



