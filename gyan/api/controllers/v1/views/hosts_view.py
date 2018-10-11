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

from gyan.api.controllers import link


_basic_keys = (
    'id',
    'hostname',
    'type',
    'status'
)


def format_host(url, host):
    def transform(key, value):
        if key not in _basic_keys:
            return
        if key == 'id':
            yield ('id', value)
            yield ('links', [link.make_link(
                'self', url, 'hosts', value),
                link.make_link(
                    'bookmark', url,
                    'hosts', value,
                    bookmark=True)])
        else:
            yield (key, value)

    return dict(itertools.chain.from_iterable(
        transform(k, v) for k, v in host.as_dict().items()))
