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

from oslo_policy import policy

from gyan.common.policies import base

NODE = 'node:%s'

rules = [
    policy.DocumentedRuleDefault(
        name=NODE % 'get_all',
        check_str=base.RULE_ADMIN_API,
        description='List all compute nodes.',
        operations=[
            {
                'path': '/v1/nodes',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=NODE % 'get',
        check_str=base.RULE_ADMIN_API,
        description='Show the details of a specific compute node.',
        operations=[
            {
                'path': '/v1/nodes/{host_ident}',
                'method': 'GET'
            }
        ]
    )
]


def list_rules():
    return rules
