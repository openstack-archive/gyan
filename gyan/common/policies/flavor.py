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

FLAVOR = 'flavor:%s'

rules = [
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'create',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Create a new Flavor.',
        operations=[
            {
                'path': '/v1/flavors',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'delete',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Delete a Flavor.',
        operations=[
            {
                'path': '/v1/flavors/{flavor_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'delete_all_projects',
        check_str=base.RULE_ADMIN_API,
        description='Delete a flavors from all projects.',
        operations=[
            {
                'path': '/v1/flavors/{flavor_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'delete_force',
        check_str=base.RULE_ADMIN_API,
        description='Forcibly delete a Flavor.',
        operations=[
            {
                'path': '/v1/flavors/{flavor_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'get_one',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Retrieve the details of a specific ml model.',
        operations=[
            {
                'path': '/v1/flavors/{flavor_ident}',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'get_all',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Retrieve the details of all ml models.',
        operations=[
            {
                'path': '/v1/flavors',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'get_all_all_projects',
        check_str=base.RULE_ADMIN_API,
        description='Retrieve the details of all ml models across projects.',
        operations=[
            {
                'path': '/v1/flavors',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR % 'update',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Update a ML Model.',
        operations=[
            {
                'path': '/v1/flavors/{flavor_ident}',
                'method': 'PATCH'
            }
        ]
    ),
]


def list_rules():
    return rules