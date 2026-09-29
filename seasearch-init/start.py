#!/usr/bin/env python3
"""
Wraps the image's /scripts/start.py. After first-time setup has generated
seafevents.conf (and before seafevents starts), it enables SeaSearch and
disables the Elasticsearch indexer. Existing [SEASEARCH] settings are kept.
"""

import base64
import os
import re
import sys

sys.path.insert(0, '/scripts')

import start  # noqa: E402
from utils import loginfo, logwarning  # noqa: E402

SEAFEVENTS_CONF = '/shared/seafile/conf/seafevents.conf'
SECTION_RE = re.compile(r'^\s*\[.*\]\s*$')


def find_section(lines, name):
    for i, line in enumerate(lines):
        if line.strip() == '[%s]' % name:
            return i
    return -1


def section_end(lines, start_index):
    for i in range(start_index + 1, len(lines)):
        if SECTION_RE.match(lines[i]):
            return i
    return len(lines)


def add_seasearch_section(lines):
    if find_section(lines, 'SEASEARCH') != -1:
        loginfo('seafevents.conf already has a [SEASEARCH] section, leaving it unchanged.')
        return False

    user = os.environ.get('INIT_SS_ADMIN_USER', '')
    password = os.environ.get('INIT_SS_ADMIN_PASSWORD', '')
    if not user or not password:
        logwarning('INIT_SS_ADMIN_USER or INIT_SS_ADMIN_PASSWORD is empty, skipping [SEASEARCH] setup.')
        return False

    token = base64.b64encode(('%s:%s' % (user, password)).encode()).decode()
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    lines.extend([
        '\n',
        '[SEASEARCH]\n',
        'enabled = true\n',
        'seasearch_url = %s\n' % os.environ.get('SEASEARCH_URL', 'http://seasearch:4080'),
        'seasearch_token = %s\n' % token,
        'interval = %s\n' % os.environ.get('SEASEARCH_INDEX_INTERVAL', '10m'),
        'index_office_pdf = %s\n' % os.environ.get('SEASEARCH_INDEX_OFFICE_PDF', 'true'),
    ])
    loginfo('Added [SEASEARCH] section to seafevents.conf.')
    return True


def disable_index_files(lines):
    header = find_section(lines, 'INDEX FILES')
    if header == -1:
        lines.extend(['\n', '[INDEX FILES]\n', 'enabled = false\n'])
        return True

    end = section_end(lines, header)
    for i in range(header + 1, end):
        if re.match(r'^\s*enabled\s*=', lines[i]):
            if lines[i].split('=', 1)[1].strip().lower() == 'false':
                return False
            lines[i] = 'enabled = false\n'
            return True

    lines.insert(header + 1, 'enabled = false\n')
    return True


def configure_seasearch():
    if not os.path.exists(SEAFEVENTS_CONF):
        logwarning('%s not found, skipping SeaSearch setup.' % SEAFEVENTS_CONF)
        return

    with open(SEAFEVENTS_CONF) as fp:
        lines = fp.readlines()

    changed = add_seasearch_section(lines)
    if disable_index_files(lines):
        loginfo('Disabled [INDEX FILES] (Elasticsearch) in seafevents.conf.')
        changed = True

    if changed:
        with open(SEAFEVENTS_CONF, 'w') as fp:
            fp.writelines(lines)


_init_seafile_server = start.init_seafile_server


def init_seafile_server():
    _init_seafile_server()
    configure_seasearch()


start.init_seafile_server = init_seafile_server

if __name__ == '__main__':
    start.setup_logging()
    start.main()
