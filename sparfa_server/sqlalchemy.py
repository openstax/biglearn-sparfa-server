import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as Base
from sqlalchemy.dialects.postgresql import insert

from .config import PY_ENV, PG_URL

class BiglearnSession(Base):
    def upsert(self, model, values, conflict_index_elements=None, conflict_update_columns=None):
        """
        The upsert will first attempt to insert the given values into this table.
        If a conflict with the unique index specified by conflict_index_elements happens,
        then only the conflict_update_columns will be updated instead.
        :param model:                   Model that is being upserted
        :param values:                  List of row values to upsert
        :param conflict_index_elements: List of columns used to determine uniqueness
        :param conflict_update_columns: List of columns to update on uniqueness conflict
        :return:                        ResultProxy containing the result of the upsert
        """
        insert_stmt = insert(model).values(values)

        if conflict_index_elements is None:
            conflict_index_elements = model.default_conflict_index_elements

        if conflict_update_columns is None:
            conflict_update_columns = model.default_conflict_update_columns

        if conflict_update_columns is None or len(conflict_update_columns) == 0:
            if conflict_index_elements is None or len(conflict_index_elements) == 0:
                stmt = insert_stmt.on_conflict_do_nothing()
            else:
                stmt = insert_stmt.on_conflict_do_nothing(index_elements=conflict_index_elements)
        else:
            if conflict_index_elements is None or len(conflict_index_elements) == 0:
                raise TypeError(
                    'conflict_index_elements must also be provided '
                    'when conflict_update_columns is provided'
                )

            stmt = insert_stmt.on_conflict_do_update(
                index_elements=conflict_index_elements,
                set_={key: getattr(insert_stmt.excluded, key) for key in conflict_update_columns}
            )

        return self.execute(stmt)

engine = create_engine(PG_URL)
Session = sessionmaker(bind=engine, class_=BiglearnSession)

# https://docs.sqlalchemy.org/en/latest/orm/session_basics.html
@contextmanager
def transaction():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

if PY_ENV == 'development':
    # Enable query logging:
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # To enable query and result logging:
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
