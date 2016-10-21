import logging

# the seed user to extend
seed = '3503249'

# number of workers
profile_workers = 18
relation_workers = 0

# relation task queue maximum size
max_size_relation_task = 100000

# request interval in second
request_interval = .1

# statistic report interval in second
stat_report_interval = 60 * 1

# Storage: MongoDB
db_uri = 'mongodb://localhost:12345/'
db_database = 'nemusic'

# Log
log_file = 'profiles.log'
log_level = logging.DEBUG
log_format = '[PID:%(process)d][%(asctime)s]%(levelname)s: %(message)s'


del logging
