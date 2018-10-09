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

"""The gyan Service API."""

import sys

from gyan.common import profiler
from gyan.common import service as gyan_service
import gyan.conf

CONF = gyan.conf.CONF


def main():
    # Parse config file and command line options, then start logging
    gyan_service.prepare_service(sys.argv)

    # Enable object backporting via the conductor
    # TODO(tbh): Uncomment after rpc services are implemented
    # base.gyanObject.indirection_api = base.gyanObjectIndirectionAPI()

    # Setup OSprofiler for WSGI service
    profiler.setup('gyan-api', CONF.api.host_ip)

    # Build and start the WSGI app
    launcher = gyan_service.process_launcher()
    server = gyan_service.WSGIService(
        'gyan_api',
        CONF.api.enable_ssl_api
    )
    launcher.launch_service(server, workers=server.workers)
    launcher.wait()

if __name__ == '__main__':
    sys.exit(main())
