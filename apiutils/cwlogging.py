import datetime
import logging
import os

import boto3
import watchtower
from botocore.client import BaseClient

STAGE = os.getenv('REGISTRAR_STAGE')

class WatchTowerWrapper:

    log_names = []
    created_log_groups = []
    created_log_streams = []

    @classmethod
    def create_cloudwatch_logger(cls, logger_name: str='', log_group: str='', log_level: str='INFO', log_stream: str=''):
        """ Create new logger with a cloudwatch handler"""
        lambda_func = os.getenv('AWS_LAMBDA_FUNCTION_NAME', 'Local-logging')
        new_log_name = f'{lambda_func}.{logger_name}'
        if new_log_name in cls.log_names:
            return logging.getLogger(new_log_name)
        else:
            cls.log_names.append(new_log_name)

        logger = logging.getLogger(new_log_name)
        logger.setLevel(log_level)
        logger.propagate = False

        if not log_group:
            log_group = os.getenv('AWS_LOG_GROUP_NAME', f'/testing')

        if not log_stream:
            log_stream = datetime.datetime.now().isoformat()[:10]

        os.environ.update(AWS_EXECUTION_ENV='uest')
        if os.getenv('AWS_EXECUTION_ENV'):
            cls.create_cw_resources(log_group, log_stream)
            logger = cls.add_cw_handler(logger, log_level=log_level, log_group=log_group, log_stream=log_stream)
        else:
            logger.info('No CloudWatch handler was added as this execution is not occurring within AWS.')
        return logger

    @classmethod
    def add_cloudwatch_stream_logger(cls, existing_logger: logging.Logger, log_group: str=f'/aws/lambda/fastq-registrar-{STAGE}',
                                     log_stream: str='', log_level: str='INFO') -> logging.Logger:
        """ Add a cloudwatch logger to an existing logger"""

        logger = existing_logger

        if not log_stream:
            log_stream = datetime.datetime.now().isoformat()[:10]
        os.environ.update(AWS_EXECUTION_ENV='uest')
        if os.getenv('AWS_EXECUTION_ENV'):
            logger = cls.handle_cw_creation(logger, log_group, log_stream, log_level)

        return logger

    @classmethod
    def handle_cw_creation(cls, logger: logging.Logger, log_group: str, log_stream: str, log_level: str):
        if not cls.cloudwatch_handler_exists(logger, log_group, log_stream):
            cls.create_cw_resources(log_group, log_stream)
            logger = cls.add_cw_handler(logger, log_level=log_level, log_group=log_group, log_stream=log_stream)
        else:
            logger.info('No CloudWatch handler was added as this execution is not occurring within AWS.')
        return logger

    @staticmethod
    def cloudwatch_handler_exists(logger: logging.Logger, log_group: str, log_stream: str) -> bool:
        if len(logger.handlers) > 0:
            for h in logger.handlers:
                if isinstance(h, watchtower.CloudWatchLogHandler) and h.log_group == log_group and h.stream_name == log_stream:
                    return True
        return False

    @classmethod
    def create_cw_resources(cls, log_group: str, log_stream: str):
        cloudwatch_client = boto3.client('logs', region_name='us-west-2')

        if log_group not in cls.created_log_groups and not cls.cloudwatch_group_exists(cloudwatch_client, log_group=log_group):
            cloudwatch_client.create_log_group(logGroupName=log_group)
            cls.created_log_groups.append(log_group)

        log_group_stream = f'{log_group}-{log_stream}'
        if log_group_stream not in cls.created_log_streams:
            if not cls.cloudwatch_stream_exists(cloudwatch_client, log_group, log_stream):
                cloudwatch_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
                cls.created_log_streams.append(log_group_stream)

    @staticmethod
    def cloudwatch_group_exists(cloudwatch_client: BaseClient, log_group: str) -> bool:
        resp = cloudwatch_client.describe_log_groups(logGroupNamePrefix=log_group)
        for group in resp['logGroups']:
            if log_group == group['logGroupName']:
                return True
        return False

    @staticmethod
    def cloudwatch_stream_exists(cloudwatch_client: BaseClient, log_group: str, log_stream: str) -> bool:

        resp = cloudwatch_client.describe_log_streams(logGroupName=log_group,
                                                      logStreamNamePrefix=log_stream)
        for log in resp['logStreams']:
            if log_stream in log['logStreamName']:
                return True
        return False

    @staticmethod
    def handler_exists(logger: logging.Logger, log_group: str, log_stream: str) -> bool:
        for h in logger.handlers:
            if h.log_group == log_group and h.log_stream ==log_stream:
                return True
        return False

    @staticmethod
    def add_cw_handler(logger: logging.Logger, log_level: str, log_group: str, log_stream: str) -> logging.Logger:
        handler = watchtower.CloudWatchLogHandler(log_group=log_group,
                                                  stream_name=log_stream,
                                                  create_log_stream=False,
                                                  create_log_group=False,
                                                  send_interval=1)

        formatter = logging.Formatter(
            f'[%(levelname)s] | %(asctime)s | %(message)s | Logger: {logger.name} | Function: %(funcName)s | LineNumber: %(lineno)s | ')
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        return logger