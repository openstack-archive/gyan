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

"""Handles all requests relating to compute resources (e.g. ml_models,
and compute hosts on which they run)."""

from oslo_log import log as logging

from gyan.common import consts
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common import profiler
from gyan.compute import rpcapi
import gyan.conf
from gyan import objects


CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)


@profiler.trace_cls("rpc")
class API(object):
    """API for interacting with the compute manager."""

    def __init__(self, context):
        self.rpcapi = rpcapi.API(context=context)
        super(API, self).__init__()

    def ml_model_create(self, context, new_ml_model, extra_spec):
        try:
            host_state = self._schedule_ml_model(context, ml_model,
                                                  extra_spec)
        except exception.NoValidHost:
            new_ml_model.status = consts.ERROR
            new_ml_model.status_reason = _(
                "There are not enough hosts available.")
            new_ml_model.save(context)
            return
        except Exception:
            new_ml_model.status = consts.ERROR
            new_ml_model.status_reason = _("Unexpected exception occurred.")
            new_ml_model.save(context)
            raise

        self.rpcapi.ml_model_create(context, host_state['host'],
                                     new_ml_model)

    def ml_model_delete(self, context, ml_model, *args):
        self._record_action_start(context, ml_model, ml_model_actions.DELETE)
        return self.rpcapi.ml_model_delete(context, ml_model, *args)

    def ml_model_show(self, context, ml_model):
        return self.rpcapi.ml_model_show(context, ml_model)