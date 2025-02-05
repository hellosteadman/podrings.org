from time import time, sleep
import os
import logging
import dj_database_url
import psycopg2


pg_config = dj_database_url.config()
check_timeout = os.getenv('POSTGRES_CHECK_TIMEOUT', 30)
check_interval = os.getenv('POSTGRES_CHECK_INTERVAL', 1)
config = {
    'host': pg_config['HOST'],
    'dbname': pg_config['NAME'],
    'user': pg_config['USER'],
    'password': pg_config['PASSWORD']
}

start_time = time()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def pg_isready(host, user, password, dbname):
    while time() - start_time < check_timeout:
        try:
            conn = psycopg2.connect(**vars())
            logger.info('Postgres is ready! ✨💅')
            conn.close()
            return True
        except psycopg2.OperationalError:
            sleep(check_interval)

    logger.error(
        f'We could not connect to Postgres within {check_timeout} seconds.'
    )

    return False


pg_isready(**config)
