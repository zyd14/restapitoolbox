import attr
from typing import List, Tuple

from apiutils.dbconnect import BaseDBConnect


@attr.s(slots=True, frozen=True)
class UnexepctedQueryArgs(Exception):
    error_msg = attr.ib()


class ViewPresenter:

    @classmethod
    def view_contents(cls, connection: BaseDBConnect, matching_args: List[str], view: str, query_args: dict):

        # Parse through provided query arguments and validate that we're only receiving arguments we expect
        cls.validate_args(matching_args, query_args)

        match_string, params = cls.get_match_string(**query_args)

        # Dynamically generate SQL query based on what URL query string arguments we received
        base_query = f'SELECT * FROM {view}'
        sql = cls.generate_sql_string(base_query, match_string)

        # Perform query
        results = connection.query(sql, params, fetch=True, result_type='listdicts')
        return results

    @staticmethod
    def validate_args(matching_args: List[str], kwargs: dict):
        unexpected_args = []
        for key, value in kwargs.items():
            if key not in matching_args:
                unexpected_args.append(f'{key}={value}')

        if unexpected_args:
            error_msg = f'Received unexpected query args {unexpected_args}'
            raise UnexepctedQueryArgs(error_msg)

    @staticmethod
    def generate_sql_string(base_sql: str, match_string: str = '') -> str:
        if match_string:
            sql = f"{base_sql} WHERE {match_string}"
        else:
            sql = f"{base_sql}"
        if not sql.endswith(';'):
            sql += ';'
        return sql

    @staticmethod
    def get_match_string(**kwargs) -> Tuple[str, tuple]:
        direct_matches = []
        params = tuple()
        for key, value in kwargs.items():
            if value:
                direct_matches.append(f'{key}=%s')
                params += (value,)
        direct_match_string = ' AND '.join(direct_matches)
        return direct_match_string, params
