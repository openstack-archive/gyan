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

import base64
import itertools
import os

import six
import time

from oslo_log import log as logging
from oslo_service import periodic_task
from oslo_utils import excutils
from oslo_utils import timeutils
from oslo_utils import uuidutils

from gyan.common import consts
from gyan.common import context
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common import utils
from gyan.common.utils import translate_exception
from gyan.common.utils import wrap_ml_model_event
from gyan.common.utils import wrap_exception
from gyan.compute import compute_host_tracker
import gyan.conf
from gyan.ml_model import driver
from gyan import objects

CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)


class Manager(periodic_task.PeriodicTasks):
    """Manages the running ml_models."""

    def __init__(self, ml_model_driver=None):
        super(Manager, self).__init__(CONF)
        self.driver = driver.load_ml_model_driver(ml_model_driver)
        self.host = CONF.compute.host
        self._resource_tracker = None

    def ml_model_create(self, context, ml_model):
        db_ml_model = objects.ML_Model.get_by_uuid_db(context, ml_model["id"])
        utils.save_model(CONF.state_path, db_ml_model)
        obj_ml_model = objects.ML_Model.get_by_uuid(context, ml_model["id"])
        obj_ml_model.status = consts.SCHEDULED
        obj_ml_model.status_reason = "The ML Model is scheduled and saved to the host %s" % self.host
        obj_ml_model.save(context)

    def ml_model_predict(self, context, ml_model_id, kwargs):
        #open("/home/bharath/Documents/0.png", "wb").write(base64.b64decode(kwargs["data"]))
        model_path = os.path.join(CONF.state_path, ml_model_id)
        return self.driver.predict(context, model_path, base64.b64decode(kwargs["data"]))

    @wrap_ml_model_event(prefix='compute')
    def _do_ml_model_create(self, context, ml_model, requested_networks,
                             requested_volumes, pci_requests=None,
                             limits=None):
        LOG.debug('Creating ml_model: %s', ml_model.uuid)

        try:
            rt = self._get_resource_tracker()
            # As sriov port also need to claim, we need claim pci port before
            # create sandbox.
            with rt.ml_model_claim(context, ml_model, pci_requests, limits):
                sandbox = None
                if self.use_sandbox:
                    sandbox = self._create_sandbox(context, ml_model,
                                                   requested_networks)

                created_ml_model = self._do_ml_model_create_base(
                    context, ml_model, requested_networks, requested_volumes,
                    sandbox, limits)
                return created_ml_model
        except exception.ResourcesUnavailable as e:
            with excutils.save_and_reraise_exception():
                LOG.exception("ML Model resource claim failed: %s",
                              six.text_type(e))
                self._fail_ml_model(context, ml_model, six.text_type(e),
                                     unset_host=True)

    @wrap_ml_model_event(prefix='compute')
    def _do_ml_model_start(self, context, ml_model):
        pass

    @translate_exception
    def ml_model_delete(self, context, ml_model, force=False):
        pass

    @translate_exception
    def ml_model_show(self, context, ml_model):
        pass

    @translate_exception
    def ml_model_start(self, context, ml_model):
        pass

    @translate_exception
    def ml_model_update(self, context, ml_model, patch):
        pass

    @periodic_task.periodic_task(run_immediately=True)
    def inventory_host(self, context):
        rt = self._get_resource_tracker()
        rt.update_available_resources(context)

    def _get_resource_tracker(self):
        if not self._resource_tracker:
            rt = compute_host_tracker.ComputeHostTracker(self.host,
                                                         self.driver)
            self._resource_tracker = rt
        return self._resource_tracker
