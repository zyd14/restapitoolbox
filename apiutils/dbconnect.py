"""

Project: ApiToolbox

File Name: dbconnect

Author: Zachary Romer, zach@scharp.org

Creation Date: 8/12/19

Version: 1.0

Purpose:

Special Notes:

"""

import attr
import logging
from typing import List, Union

import psycopg2
import psycopg2.extras


@attr.s(slots=True, frozen=True)
class BaseDBConnect:
    """
    Provides low-level connection interface to a postgres database.

    Attributes
        user: the username which will be used to for authentication.
        password: password for user connecting to database.
        host: IP or DNS where database resides.
        database: database to connect to.
        autocommit [Optional - default=False]: determines whether to automatically commit each time .query() is called. If
                    set to False, each call to .query() will be recorded as part of a transaction,
                    requiring the user to call DBconnect.connection.commit() in order for the
                    transaction to be committed and written to the database.  This is important
                    to consider for INSERT / UPDATE / DELETE statements as their effects will
                    not persist if auto_commit=False and the user does not manually commit their
                    transaction.
        connection: a psycopg2 connection to the user-provided database

    """
    logger = attr.ib(default=logging.getLogger('db_logger'))  # type: logging.Logger
    user = attr.ib(default=None)  # type: str
    password = attr.ib(default=None)  # type: str
    host = attr.ib(default=None)  # type: str
    database = attr.ib(default=None)  # type: str
    autocommit = attr.ib(default=False)  # type: bool
    timeout = attr.ib(default=60)  # type: int
    connection = attr.ib(init=False)  # type: psycopg2

    def _attrs_post_init__(self):
        object.__setattr__(self, 'connection', self._get_connection())
        if self.autocommit:
            self.connection.autocommit = True

    def _get_connection(self):
        """ Obtain a connection to the given database at given host with provided user credentials

        Args:
            user: username to connect with.  Must be a user which has a role in the postgres database being connected to,
                    and that role must have login abilities in the database.
            password: password of user logging in.
            host: IP/DNS where database is located
            database: postgres database to connect to

        Returns:
            pyscopg2 connection
        """
        self.logger.info(f'Connecting to {self.database} at host {self.host} as user {self.user}')

        try:
            connection = psycopg2.connect(user=self.user,
                                          password=self.password,
                                          host=self.host,
                                          database=self.database,
                                          connect_timeout=self.timeout)
        except Exception as exc:
            # TODO: catch authorization errors and provide custom error handling
            error_msg = f'Error when connecting to database {self.database} at host {self.host} as user {self.user}.  Exception: {exc}'
            self.logger.exception(error_msg)
            raise
        self.logger.info('Successfully connected')
        return connection

    def query(self, sql: str, params: tuple=None, commit: bool=True, fetch: bool=False) -> Union[List[dict], None]:
        """ Execute an arbitrary SQL query with provided parameters using.

        Args:
            sql: query string to be executed.  Parameters expected to be filled by params tuple should be substituted appropriately with %s.
            params: any parameters required to parameterize the sql query string being executed.
            commit: specifies whether queries should be committed automatically after executing. Overrides autocommit
                    if set at connection level.
            fetch: specifies whether to fetch results from the query.  A psyocpg2.ProgrammingError will be raised
                    if fetch=True for a query which does not return any results (e.g. INSERT/UPDATE/DELETE).
        Returns:
            List of rows from query result if fetch=True.  None if fetch=False

        Raises:
            NothingToFetch
        """
        # TODO: Should queries with nothing to fetch have their psycopg2 exception caught and passed? Or just provide
        # custom error handling for user?

        cursor = self._get_cursor()

        if params:
            executed_sql = sql % params
        else:
            executed_sql = sql

        # Execute query
        try:
            if params:
                # Use DBAPI parameterized query for safety against SQL injection
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
        except Exception as exc:
            self.logger.exception(f'Error while executing query: {executed_sql}\n. Exception: {exc}')
            self.connection.rollback()
            raise exc

        if commit:
            self.connection.commit()

        # Return results of query if requested
        if fetch:
            rows = self._fetch_results(cursor, executed_sql)
            cursor.close()
            return [dict(r) for r in rows]

        cursor.close()

    def _get_cursor(self):
        return self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def _fetch_results(self, cursor, executed_sql: str)->list:
        try:
            rows = cursor.fetchall()
        except psycopg2.ProgrammingError as exc:
            error_msg = 'ProgrammingError: Unable to fetch any results.  This could be the result of a malformed query' \
                        ' referencing nonexistent schemas/tables. Properly formed queries with no results should successfully' \
                f' return an empty collection.  This could also be the result of executing the query with "fetch=True" for an' \
                f'INSERT or UPDATE query. \n Executed query: {executed_sql}'
            self.logger.error(error_msg)
            raise exc

        return rows

    @staticmethod
    def _results_to_dict(rows: list, col_names: list) -> dict:
        results = {}
        for name in col_names:
            results[name] = []
        for row in rows:
            for key, value in row.items():
                results[key].append(value)
        return results
