from sqlalchemy import select
from queries.core import create_tables, insert_data
import sys
import os
from models import workers_table
from database import sync_engine
sys.path.insert(1, os.path.join(sys.path[0], '..'))

create_tables()
insert_data('Myroslav')
insert_data('Artem')
insert_data('Rostyslav')
insert_data('Angela')
insert_data('Ben')
insert_data('Yari')
insert_data('karina')

with sync_engine.connect() as conn:
    result = conn.execute(select(workers_table))
    for row in result:
        print(row)
