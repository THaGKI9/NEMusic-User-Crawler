# coding:utf-8
import logging
import multiprocessing
import os
import Queue
import time
import nemusic
import signal
import sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError

exit_flag = False
config = __import__(sys.argv[1])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(config.log_format)

stream_hdlr = logging.StreamHandler()
stream_hdlr.setLevel(logging.DEBUG)
stream_hdlr.setFormatter(formatter)
logger.addHandler(stream_hdlr)

file_hdlr = logging.FileHandler(config.log_file)
file_hdlr.setLevel(config.log_level)
file_hdlr.setFormatter(formatter)
logger.addHandler(file_hdlr)


def relation_worker(relation_task_queue, update_queue, new_user_queue):
    logger.info('relation worker is in. PID:%d' % os.getpid())

    handlers = {
        1: nemusic.get_fans,
        2: nemusic.get_follows,
    }

    while True:
        try:
            uid, offset, hdlr_id = relation_task_queue.get(True, 1)
        except Queue.Empty:
            continue

        try:
            status, is_more, user_set = handlers[hdlr_id](uid, offset)
        except nemusic.ConnectionError:
            logger.warning('relation worker: '
                           'anti-spider seem to work, hold for 60s.')
            time.sleep(60)
            continue

        if not status:
            continue

        if is_more:
            relation_task_queue.put((uid, offset + 100, hdlr_id))
        else:
            profiles.update({'_id': uid}, {'$inc': {'extend': hdlr_id}})

        if len(user_set) == 0:
            logger.warning('relation worker get a empty set. '
                           'uid: %s, offset: %d, handler: %s.',
                           uid, offset, handlers[hdlr_id].__name__)
            continue

        exist_user_set = {doc['_id'] for doc in profiles.aggregate([
            {'$match': {'_id': {'$in': list(user_set)}}},
            {'$project': {'_id': 1}}
        ])}

        user_set = user_set - exist_user_set
        if len(user_set):
            logger.debug('add %d new users from user %s.', len(user_set), uid)
            profiles.insert_many([
                {'_id': user, 'status': 0, 'extend': 0}
                for user in user_set
            ])

        time.sleep(config.request_interval)


def profile_worker(profile_task_queue, update_queue):
    logger.info('profile worker is in. PID:%d' % os.getpid())

    exit_reason = 'none'
    while True:
        try:
            user = profile_task_queue.get(True, 1)
        except Queue.Empty:
            continue

        got_nothing = True
        if user is not None:
            uid = user['_id']

            try:
                profile = nemusic.get_profile(uid)
            except nemusic.ConnectionError:
                logger.warning('profile worker: '
                               'anti-spider seem to work, hold for 60s.')
                time.sleep(60)
                continue

            if profile is not None:
                got_nothing = False
                update_queue.put(profile)

        if got_nothing:
            logger.warning(
                'worker tries to get profile of %s but got nothing.', uid)

        time.sleep(config.request_interval)

    logger.info('profile worker is out. reason: ' + exit_reason)


def profile_task_distribution_worker(profile_task_queue):
    logger.info('profile task distribution worker is in. PID:%d' % os.getpid())


def update_database_worker(update_queue):
    logger.info('update database worker is in. PID:%d' % os.getpid())


def stat_reporter(queue):
    profiles = get_profile_collection()
    while True:
        complete_user_count = profiles.find({'status': 2, 'extend': 3}).count()
        profile_not_done_count = profiles.find({'status': 0}).count()
        logger.info('STAT: complete user: %d', complete_user_count)
        logger.info('STAT: profile task: %d', profile_not_done_count)
        logger.info('STAT: extend task: %d', queue.qsize())
        time.sleep(config.stat_report_interval)


def get_profile_collection():
    client = MongoClient(config.db_uri)
    try:
        client.database_names()
    except PyMongoError as ex:
        logger.error(ex.message)
        exit()
    return client[config.db_database].profiles


def reset_miner(profiles):
    if profiles.count() == 0:
        logger.info('no profiles exist.')
        logger.info('put user %s as a seed into profile library', config.seed)
        profiles.insert_one({'_id': config.seed, 'status': 0, 'extend': 0})


def signal_handler(signal, frame):
    global exit_flag
    exit_flag = True
    sys.exit()


def start():
    logger.critical('===================================================')
    logger.critical('===================================================')
    logger.critical('===================================================')
    logger.critical('===================================================')

    profiles = get_profile_collection()
    reset_miner(profile_worker)

    workers = []
    workers.append(multiprocessing.Process(target=stat_reporter))

    profile_task_queue = multiprocessing.Queue()
    if config.profile_workers:
        profiles.update_many({'status': 1}, {'$set': {'status': 0}})

        workers += [multiprocessing.Process(target=profile_worker)
                    for i in range(config.profile_workers)]
        logger.info('profile task: %d', profiles.find({'status': 0}).count())

    extend_task_queue = multiprocessing.Queue()
    lock = multiprocessing.Lock()
    if config.relation_workers:
        not_extend_users = profiles.aggregate([
            {'$match': {'extend': {'$lt': 3}}},
            {'$project': {'_id': 1, 'extend': 1}}
        ])
        for user in not_extend_users:
            extend_status = user['extend']
            if extend_status & 1 == 0:
                extend_task_queue.put_nowait((user['_id'], 0, 1))
            if extend_status & 2 == 0:
                extend_task_queue.put_nowait((user['_id'], 0, 2))
            if extend_task_queue.qsize() > config.max_size_relation_task:
                break

        if extend_task_queue.empty():
            logger.warning('there is no user to extend, '
                           'you may need to change the seed.')
        else:
            logger.info('extend queue: %d', extend_task_queue.qsize())

            for i in range(config.relation_workers)]
                workers += [multiprocessing.Process(target=relation_worker,
                                                    args=(extend_queue, lock))

    for worker in workers:
        worker.start()
        time.sleep(config.request_interval / 2)

    while True:
        is_all_dead = all(map(lambda x: not x.is_alive(), workers))
        if is_all_dead:
            break
        time.sleep(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    start()
