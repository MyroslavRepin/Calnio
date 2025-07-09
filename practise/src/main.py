from sqlalchemy import select
from models import WorkersOrm
from database import sync_engine
from queries.orm import insert_data, create_tables

import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

create_tables()

insert_data()
