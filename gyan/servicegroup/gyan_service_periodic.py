#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Zun Service Layer"""

from oslo_log import log
from oslo_service import periodic_task

from gyan.common import context
from gyan import objects


LOG = log.getLogger(__name__)


class GyanServicePeriodicTasks(periodic_task.PeriodicTasks):
    """Gyan periodic Task class

    Any periodic task job need to be added into this class
    """

    def __init__(self, conf, binary):
        self.gyan_service_ref = None
        self.host = conf.host
        self.binary = binary
        super(GyanServicePeriodicTasks, self).__init__(conf)


def setup(conf, binary, tg):
    pt = GyanServicePeriodicTasks(conf, binary)
    tg.add_dynamic_timer(
        pt.run_periodic_tasks,
        periodic_interval_max=conf.periodic_interval_max,
        context=None)
