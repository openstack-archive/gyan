#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import shlex
import sys

from oslo_log import log as logging
from oslo_privsep import priv_context
from oslo_service import service

from gyan.common import rpc_service
from gyan.common import service as gyan_service
from gyan.common import utils
import gyan.conf

CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)


def main():
    gyan_service.prepare_service(sys.argv)

    LOG.info('Starting server in PID %s', os.getpid())
    CONF.log_opt_values(LOG, logging.DEBUG)

    CONF.import_opt('topic', 'gyan.conf.compute', group='compute')
    CONF.import_opt('host', 'gyan.conf.compute', group='compute')
    

    from gyan.compute import manager as compute_manager
    endpoints = [
        compute_manager.Manager(),
    ]
    #import pdb;pdb.set_trace()
    server = rpc_service.Service.create(CONF.compute.topic, CONF.compute.host,
                                        endpoints, binary='gyan-compute')
    launcher = service.launch(CONF, server, restart_method='mutate')
    launcher.wait()
