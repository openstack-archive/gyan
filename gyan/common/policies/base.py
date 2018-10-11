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

ROLE_ADMIN = 'role:admin'
RULE_ADMIN_OR_OWNER = 'is_admin:True or project_id:%(project_id)s'
RULE_ADMIN_API = 'rule:context_is_admin'
RULE_DENY_EVERYBODY = 'rule:deny_everybody'

rules = [
    policy.RuleDefault(
        name='context_is_admin',
        check_str=ROLE_ADMIN
    ),
    policy.RuleDefault(
        name='admin_or_owner',
        check_str=RULE_ADMIN_OR_OWNER
    ),
    policy.RuleDefault(
        name='admin_api',
        check_str=RULE_ADMIN_API
    ),
    policy.RuleDefault(
        name="deny_everybody",
        check_str="!",
        description="Default rule for deny everybody."),
]


def list_rules():
    return rules
