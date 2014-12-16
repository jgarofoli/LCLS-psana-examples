import logging

from job import *
from event_process import *
from output_html import *
from event_process_lib import *

logger = logging.getLogger('data_summary')
logger.setLevel(logging.INFO)

fh = logging.FileHandler('data_summary.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

