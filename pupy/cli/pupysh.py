#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------
# Copyright (c) 2015, Nicolas VERDIER (contact@n1nj4.eu)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
# --------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import os
import logging
import argparse

args = None

def parse_args():
    parser = argparse.ArgumentParser(prog='pupysh', description="Pupy console")
    parser.add_argument(
        '--loglevel', '-d',
        help='change log verbosity', dest='loglevel',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='WARNING')
    parser.add_argument('--logfile', '-DF', help='log to file', dest='logfile', default=None)
    parser.add_argument(
        '-l', '--listen',
        help='Bind server listener with transport and args to port.'
        'Example: -l ssl 127.0.0.1:443 -l kcp 80 -l xyz 1234 OPTION1=value OPTION2=value.',
        nargs='+',
        metavar=('TRANSPORT', '<<EXTERNAL_IP=>IP>:<EXTERNAL_PORT=>PORT OPTION=value'),
        action='append', default=[]
    )
    parser.add_argument(
        '--workdir', help='Set Workdir (Default = current workdir)')
    parser.add_argument('-NE', '--not-encrypt',
                        help='Do not encrypt configuration', action='store_true')
    parser.add_argument('--sound', dest='sounds',
                        help='Play a sound when a session connects', action='store_true')
    return parser

try:
    import pupy.pupylib.PupySignalHandler
    assert pupy.pupylib.PupySignalHandler
except ImportError:
    pass

from pupy.pupylib import (
    PupyServer, PupyCmdLoop, PupyCredentials, PupyConfig
)

def main():
    parser = parse_args()
    args = parser.parse_args()
    if args.workdir:
        os.chdir(args.workdir)

        if os.getuid() == 0 and os.getgid() == 0:
            wdstat = os.stat(args.workdir)
            os.setresgid(wdstat.st_uid, wdstat.st_uid, wdstat.st_uid)
            os.setresuid(wdstat.st_uid, wdstat.st_uid, wdstat.st_uid)

    root_logger = logging.getLogger()

    if args.logfile:
        logging_stream = logging.FileHandler(args.logfile)
        logging_stream.setFormatter(
            logging.Formatter(
                '%(asctime)-15s|%(levelname)-5s|%(relativeCreated)6d|%(threadName)s|%(name)s| %(message)s'))
    else:
        logging_stream = logging.StreamHandler()
        logging_stream.setFormatter(logging.Formatter('%(asctime)-15s| %(message)s'))

    logging_stream.setLevel(logging.DEBUG)

    root_logger.handlers = []

    root_logger.addHandler(logging_stream)
    root_logger.setLevel(args.loglevel)
    PupyCredentials.DEFAULT_ROLE = 'CONTROL'
    if args.not_encrypt:
        PupyCredentials.ENCRYPTOR = None

    # Try to initialize credentials before CMD loop
    try:
        credentials = PupyCredentials.Credentials(validate=True)
    except PupyCredentials.EncryptionError as e:
        logging.error(e)
        exit(1)

    config = PupyConfig()

    if args.listen:
        listeners = {
            x[0]: x[1:] if len(x) > 1 else [] for x in args.listen
        }

        config.set('pupyd', 'listen', ','.join(listeners))
        for listener in listeners:
            args = listeners[listener]
            if args:
                config.set('listeners', listener, ' '.join(args))

    pupyServer = PupyServer(config, credentials)
    pupycmd = PupyCmdLoop(pupyServer)

    pupyServer.start()
    pupycmd.loop()
    pupyServer.stop()
    pupyServer.finished.wait()

if __name__ == "__main__":
    main()