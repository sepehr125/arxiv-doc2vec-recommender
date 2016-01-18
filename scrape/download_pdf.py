import psycopg2
from psycopg2.extras import DictCursor
import requests
import os
import shutil
import time
import random
"""
While we can get PDFs this way,
the remaining pipeline for parsing 
PDF and storing to database is not yet set up.
"""


if __name__ == '__main__':

    os.system('mkdir -p pdf')
    os.system('mkdir -p text')

    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT arxiv_id FROM articles")
            numtot = 0
            numok = 0
            for arxiv_id in cur:
                
                numtot += 1
                pdf_path = os.path.join('pdf', arxiv_id) + '.pdf'
                
                # bail if file exists
                if os.path.isfile(pdf_path):
                    print("File exists")
                    continue
                # bail if bad URL or no PDF:
                pdf_url = "http://arxiv.org/pdf/%s.pdf"%article['arxiv_id']
                h = requests.head(pdf_url)
                if not any([h.status_code == 200, h.headers['Content-Type'] == 'application/pdf']):
                    print("Bad url on try %d"%numtot)
                    continue
                req = requests.get(pdf_url)
                with open(pdf_path, 'wb') as fp:
                    fp.write(req.content)
                    numok+=1

                # slightly hacky way to not get blocked:
                time.sleep(0.1 + random.uniform(0,0.2))
                
                # print some info
                if numtot%100==0:
                    print("Got %d of %d tries"%(numok, numtot))
