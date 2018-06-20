import json
import os
import logging
import MySQLdb

BASE_PATH = os.path.dirname(os.path.realpath(__file__))  # gets base path of the project


def __get_config_data():
    """ Returns dictionary from config file
    """
    data = json.load(open(os.path.join(BASE_PATH, 'config.json')))
    return data


def get_db_settings():
    """ Returns dictionary with database details
    """
    return __get_config_data()['db']


def get_tables():
    """ Returns dictionary with all table details
    """
    return __get_config_data()['tables']


def get_db():
    """ Returns a database connection object
    """
    db_settings = get_db_settings()
    db = MySQLdb.connect(host=db_settings.get('host'), user=db_settings.get('user'), passwd=db_settings.get('password'),
                         db=db_settings.get('db'))
    return db


class Logger:

    """ Logs
    """
    def __init__(self):
        data = json.load(open(os.path.join(BASE_PATH, 'config.json')))
        filename = os.path.join(BASE_PATH, '{}.log'.format(data['logfile_name']))
        logging.basicConfig(level=logging.INFO, filename=filename, format='%(asctime)s %(levelname)-8s %(message)s')

    @staticmethod
    def log(level, message):
        """ Static method to create log
        """
        if level == 'info':
            logging.info(message)
        elif level == 'error':
            logging.error(message)
        elif level == 'warning':
            logging.warning(message)
        else:
            logging.log(message)
