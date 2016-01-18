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


# run the following at the terminal, (altering the dates to suit your needs)
# oai-harvest -from 2016-01-01 -until 2016-01-07 http://export.arxiv.org/oai2