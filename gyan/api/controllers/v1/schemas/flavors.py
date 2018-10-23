# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy

from gyan.api.controllers.v1.schemas import parameter_types

_flavor_properties = {}

flavor_create = {
    'type': 'object',
    'properties': {
        "name": parameter_types.flavor_name,
        "driver": parameter_types.flavor_driver,
        "cpu": parameter_types.flavor_cpu,
        "disk": parameter_types.flavor_disk,
        'memory': parameter_types.flavor_memory,
        'python_version': parameter_types.flavor_python_version,
        'additional_details': parameter_types.flavor_additional_details

    },
    'required': ['name', 'cpu', 'memory', 'python_version', 'disk', 'driver', 'additional_details'],
    'additionalProperties': False
}


query_param_create = {
    'type': 'object',
    'properties': {
        'run': parameter_types.boolean_extended
    },
    'additionalProperties': False
}

ml_model_update = {
    'type': 'object',
    'properties': {},
    'additionalProperties': False
}

query_param_delete = {
    'type': 'object',
    'properties': {
        'force': parameter_types.boolean_extended,
        'all_projects': parameter_types.boolean_extended,
        'stop': parameter_types.boolean_extended
    },
    'additionalProperties': False
}
