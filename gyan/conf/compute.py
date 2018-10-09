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


service_opts = [
    cfg.StrOpt(
        'topic',
        default='gyan-compute',
        help='The queue to add compute tasks to.'),
]

opt_group = cfg.OptGroup(
    name='compute', title='Options for the gyan-compute service')

ALL_OPTS = (service_opts)


def register_opts(conf):
    conf.register_group(opt_group)
    conf.register_opts(ALL_OPTS, opt_group)


def list_opts():
    return {opt_group: ALL_OPTS}
