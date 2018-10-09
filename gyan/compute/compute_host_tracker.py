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

import collections
import copy

from oslo_log import log as logging

from gyan.common import exception
from gyan.common import utils
from gyan import objects
from gyan.objects import base as obj_base

LOG = logging.getLogger(__name__)
COMPUTE_RESOURCE_SEMAPHORE = "compute_resources"


class ComputeHostTracker(object):
    def __init__(self, host, ml_model_driver):
        self.host = host
        self.ml_model_driver = ml_model_driver
        self.compute_host = None
        self.tracked_ml_models = {}
        self.old_resources = collections.defaultdict(objects.ComputeHost)
        
        
    def update_available_resources(self, context):
        # Check if the compute_host is already registered
        host = self._get_compute_host(context)
        if not host:
            # If not, register it and pass the object to the driver
            host = objects.ComputeHost(context)
            host.hostname = self.host
            host.type = self.ml_model_driver.__class__.__name__
            host.status = "AVAILABLE"
            host.create(context)
            LOG.info('Host created for :%(host)s', {'host': self.host})
        self.ml_model_driver.get_available_resources(host)
        self.compute_host = host
        return host

    def _get_compute_host(self, context):
        """Returns compute host for the host"""
        try:
            return objects.ComputeHost.get_by_name(context, self.host)
        except exception.ComputeHostNotFound:
            LOG.warning("No compute host record for: %(host)s",
                        {'host': self.host})

    
    def _set_ml_model_host(self, context, ml_model):
        """Tag the ml_model as belonging to this host.

        This should be done while the COMPUTE_RESOURCES_SEMAPHORE is held so
        the resource claim will not be lost if the audit process starts.
        """
        ml_model.host = self.host
        ml_model.save(context)