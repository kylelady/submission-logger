#!/usr/bin/env python2.7

import datetime
import os
import string
import sys

import pprint

from flask import Flask, request
from werkzeug import secure_filename

app = Flask('submission-logger')
app.debug = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ADMINS = ['kylelady@umich.edu']
if not app.debug:
    import logging
    from logging import Formatter
    from logging.handlers import SMTPHandler, SysLogHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               'kylelady@umich.edu',
                               ADMINS, 'submit280 archiver failed!')
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
    app.logger.addHandler(mail_handler)

    syslog_handler = SysLogHandler()
    syslog_handler.setLevel(logging.WARNING)
    app.logger.addHandler(syslog_handler)

archive_directory = '/z/eecs280/archive/f13'

def make_error_msg(missing_key):
    return 'ERROR: missing key "%s". Contact kylelady@umich.edu\n' % missing_key

email_template = '''From: kylelady@umich.edu
Subject: [EECS 280] submission confirmation
To: {uniqname}@umich.edu

uniqname: {uniqname}
timestamp: {timestamp}

files:
'''


@app.route('/', methods=['POST'])
def process_submission():
    data = {}
    for key in ('uniqname', 'compile_out', 'test_out'):
        if key not in request.form:
            logging.error('blargh')
            return make_error_msg(key), 400
        data[key] = request.form[key]

    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    submit_dir = '{user}-{date}'.format(user=data['uniqname'],
            date=timestamp)
    submit_path = os.path.join(archive_directory, submit_dir)
    print 'making path: %s' % submit_path
    os.mkdir(submit_path)

    email_message = [ email_template.format(uniqname=data['uniqname'],
            timestamp=timestamp), ]

    for file in request.files:
        file_path = os.path.join(submit_path, secure_filename(file))
        print 'saving file %s as %s' % (file, file_path)
        request.files[file].save(file_path)
        email_message.append(string.center(secure_filename(file), 78, '-'))
        with open(file_path) as f:
            email_message.append(f.read())
        email_message.append('-' * 78)
        email_message.append('')

    compile_path = os.path.join(submit_path, 'compile.out')
    with open(compile_path, 'w') as f:
        print 'writing compile.out to %s' % compile_path
        f.write(data['compile_out'])

    test_path = os.path.join(submit_path, 'test.out')
    with open(test_path, 'w') as f:
        print 'writing test.out to %s' % test_path
        f.write(data['test_out'])

    print 'done recording; assembling email'

    print email_message

    p = os.popen('/usr/sbin/sendmail -t -i', 'w')
    p.write('\n'.join(email_message))
    status = p.close()
    print 'mail success' if status is not None else 'mail failed'

    return 'submission archived successfully\n', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=43877)
