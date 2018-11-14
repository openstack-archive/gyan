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

from oslo_config import cfg

from gyan.conf import api
from gyan.conf import compute
from gyan.conf import ml_model_driver
from gyan.conf import database
from gyan.conf import keystone
from gyan.conf import path
from gyan.conf import profiler
from gyan.conf import scheduler
from gyan.conf import services
from gyan.conf import ssl
from gyan.conf import utils
from gyan.conf import gyan_client
from gyan.conf import heat_client

CONF = cfg.CONF

api.register_opts(CONF)
compute.register_opts(CONF)
ml_model_driver.register_opts(CONF)
database.register_opts(CONF)
keystone.register_opts(CONF)
path.register_opts(CONF)
scheduler.register_opts(CONF)
services.register_opts(CONF)
gyan_client.register_opts(CONF)
heat_client.register_opts(CONF)
ssl.register_opts(CONF)
profiler.register_opts(CONF)
utils.register_opts(CONF)