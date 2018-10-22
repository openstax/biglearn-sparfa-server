from uuid import UUID
from contextlib import contextmanager, closing

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.dialects.postgresql import insert

from ..config import PG_URL, PY_ENV


class BiglearnSession(Session):

    def upsert_values(self, cls, values,
                      conflict_index_elements=None,
                      conflict_update_columns=None):
        """
        The upsert will first attempt to insert the given values into this table.
        If a conflict with the unique index specified by conflict_index_elements happens,
        then only the conflict_update_columns will be updated instead.
        :param cls:                     Class that is being upserted
        :param values:                  List of row values to upsert
        :param conflict_index_elements: List of columns used to determine uniqueness
        :param conflict_update_columns: List of columns to update on uniqueness conflict
        :return:                        ResultProxy containing the result of the upsert
        """
        if not values:
            return

        # NOTE: UUID objects fail to insert properly unless stringified
        insert_stmt = insert(cls).values(values)

        if conflict_index_elements is None:
            conflict_index_elements = cls.default_conflict_index_elements

        if conflict_update_columns is None:
            conflict_update_columns = cls.default_conflict_update_columns

        if conflict_update_columns:
            if not conflict_index_elements:
                raise TypeError(
                    'when conflict_update_columns is provided, then '
                    'conflict_index_elements must also be provided'
                )

            stmt = insert_stmt.on_conflict_do_update(
                index_elements=conflict_index_elements,
                set_={key: getattr(insert_stmt.excluded, key) for key in conflict_update_columns}
            )
        elif conflict_index_elements:
            stmt = insert_stmt.on_conflict_do_nothing(index_elements=conflict_index_elements)
        else:
            stmt = insert_stmt.on_conflict_do_nothing()

        return self.execute(stmt)

    def upsert_models(self, cls, models,
                      conflict_index_elements=None,
                      conflict_update_columns=None):
        """
        The upsert will first attempt to insert the given models into this table.
        If a conflict with the unique index specified by conflict_index_elements happens,
        then only the conflict_update_columns will be updated instead.
        :param cls:                     Class that is being upserted
        :param models:                  List of models to upsert
        :param conflict_index_elements: List of columns used to determine uniqueness
        :param conflict_update_columns: List of columns to update on uniqueness conflict
        :return:                        ResultProxy containing the result of the upsert
        """
        return self.upsert_values(cls, [model.dict for model in models],
                                  conflict_index_elements=conflict_index_elements,
                                  conflict_update_columns=conflict_update_columns)


ENGINE = create_engine(PG_URL)
Session = sessionmaker(bind=ENGINE, class_=BiglearnSession)


# https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#session-begin-nested
@contextmanager
def transaction():
    """Provide a transactional scope around a series of operations."""
    with closing(Session()) as session:
        try:
            yield session
        except BaseException:
            session.rollback()
            raise
        else:
            session.commit()
