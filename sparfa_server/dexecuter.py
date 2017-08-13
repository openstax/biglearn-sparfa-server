from functools import wraps

from sqlalchemy import create_engine


class Dexecuter(object):
    """The :class: `Dexecuter` acts both as a context manager and a
       decorator.

       An instance of the dexecuter can be created by passing in
       the SQL Alchemy connection uri. ::

           dexecuter = Dexecuter('<sqlalchemy uri>')

           # in a flask app, for example:
           dexecuter = Dexecuter(app.config['sqlalchemy.url'], debug=app.debug)


       To use the dexecuter as a context manager::

           def insert_into(table, values):
               with dexecuter as connection:
                   statement = table.insert().values(**values)
                   result = connection.execute(statement)
               return result

       The same can be done using the :class: `Dexecuter` as a decorator::

           @dexecuter
           def insert_into(table, values):
               return table.insert().values(**values)

       As a decorator, the dexecuter expects the decorated function to
       return a SQL Alchemy statement that can be passed on to the SQL
       Alchemy connection for execution.

       :param connection_string:  The DB connection string.
    """

    def __init__(self, connection_string):
        self.connection_string = connection_string
        self._conn = None

    def __enter__(self):
        if not self._conn:
          self.connect()

        return self._conn

    def __call__(self, *args, **kwargs):
        """
        :param fetch_all:  Calls fetch_all on the statement instead of
        returning the :class: `ResultProxy`.
        """
        fetch_all = False

        def deco(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                with self as connection:
                    result = connection.execute(fn(*args, **kwargs))
                    if fetch_all:
                        singleton = len(result.keys()) == 1
                        result = result.fetchall()
                        if singleton:
                            result = [v[0] for v in result]
                return result

            return wrapped

        if len(args) == 1 and callable(args[0]):
            fetch_all = False
            return deco(args[0])

        if 'fetch_all' in kwargs:
            fetch_all = kwargs['fetch_all']
        elif len(args) == 1:
            fetch_all = args[0]

        return deco


    def connect(self):
        if self._conn:
            raise RuntimeError('This dexecuter is already open.')

        engine = create_engine(self.connection_string,
                               convert_unicode=True)
        self._conn = engine.connect()
        return self._conn


    def close(self):
        if not self._conn:
            raise RuntimeError('This dexecuter is not open.')
        self._conn.close()
        self._conn = None

