#
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

import itertools

from oslo_log import log as logging

from gyan.api.controllers import link
from gyan.common.policies import ml_model as policies

_basic_keys = (
    'id',
    'user_id',
    'project_id',
    'name',
    'url',
    'status',
    'status_reason',
    'host_id',
    'deployed',
    'ml_type'
)

LOG = logging.getLogger(__name__)


def format_ml_model(context, url, ml_model):
    def transform(key, value):
        LOG.debug(key)
        LOG.debug(value)
        if key not in _basic_keys:
            return
        # strip the key if it is not allowed by policy
        policy_action = policies.ML_MODEL % ('get_one:%s' % key)
        if not context.can(policy_action, fatal=False, might_not_exist=True):
            return
        if key == 'id':
            yield ('id', value)
            if url:
                yield ('links', [link.make_link(
                    'self', url, 'ml_models', value),
                    link.make_link(
                        'bookmark', url,
                        'ml_models', value,
                        bookmark=True)])
        else:
            yield (key, value)

    return dict(itertools.chain.from_iterable(
        transform(k, v) for k, v in ml_model.items()))
