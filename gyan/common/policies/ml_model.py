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

ML_MODEL = 'ml_model:%s'

rules = [
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'create',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Create a new ML Model.',
        operations=[
            {
                'path': '/v1/ml_models',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'delete',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Delete a ML Model.',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'delete_all_projects',
        check_str=base.RULE_ADMIN_API,
        description='Delete a ml models from all projects.',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'delete_force',
        check_str=base.RULE_ADMIN_API,
        description='Forcibly delete a ML model.',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'get_one',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Retrieve the details of a specific ml model.',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'get_all',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Retrieve the details of all ml models.',
        operations=[
            {
                'path': '/v1/ml_models',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'get_all_all_projects',
        check_str=base.RULE_ADMIN_API,
        description='Retrieve the details of all ml models across projects.',
        operations=[
            {
                'path': '/v1/ml_models',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'update',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Update a ML Model.',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name=ML_MODEL % 'upload_trained_model',
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Upload the trained ML Model',
        operations=[
            {
                'path': '/v1/ml_models/{ml_model_ident}/upload_trained_model',
                'method': 'POST'
            }
        ]
    ),
]


def list_rules():
    return rules
