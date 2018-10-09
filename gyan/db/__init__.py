# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_db import options

from gyan.common import paths
import gyan.conf

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('gyan.sqlite')

options.set_defaults(gyan.conf.CONF)
options.set_defaults(gyan.conf.CONF, _DEFAULT_SQL_CONNECTION)
