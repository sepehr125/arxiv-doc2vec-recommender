"""
Harvest metadata of ArXiv articles (including abstract)
for given subject or date range
from Open Archives Initiative (OAI).
More information: http://arxiv.org/help/oa/index

make sure you have installed oaiharvest already:
https://pypi.python.org/pypi/oaiharvest

oaiharvest 'plays nice' with the API,
adhering to rate limitation guidelines.
"""

import os

start_date = '2015-01-15'
end_date = '2016-01-15'
output_dir = './data'
# run the following at the terminal, (altering the dates to suit your needs)
cmd = "oai-harvest --from %s --until %s -d %s http://export.arxiv.org/oai2"%(start_date, end_date, output_dir)
os.system(cmd)