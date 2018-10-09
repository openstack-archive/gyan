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

from gyan.objects import compute_host
from gyan.objects import ml_model
from gyan.objects import resource_class
from gyan.objects import resource_provider


ComputeHost = compute_host.ComputeHost
ML_Model = ml_model.ML_Model

__all__ = (
    'ComputeHost',
    'ML_Model'
)
