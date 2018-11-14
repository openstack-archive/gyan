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
import shlex
import os
import time
import yaml

from eventlet import greenthread

from oslo_log import log as logging
from oslo_utils import strutils
from oslo_utils import uuidutils
import pecan
import six

from gyan.api.controllers import base
from gyan.api.controllers import link
from gyan.api.controllers.v1 import collection
from gyan.api.controllers.v1.schemas import ml_models as schema
from gyan.api.controllers.v1.views import ml_models_view as view
from gyan.api import utils as api_utils
from gyan.api import validation
from gyan.common import consts
from gyan.common import context as gyan_context
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common.policies import ml_model as policies
from gyan.common import clients
from gyan.common import policy
from gyan.common import utils
import gyan.conf
from gyan import objects

CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)
BASE_TEMPLATE = os.path.join(CONF.state_path, "base.yaml")

def check_policy_on_ml_model(ml_model, action):
    context = pecan.request.context
    policy.enforce(context, action, ml_model, action=action)


class MLModelCollection(collection.Collection):
    """API representation of a collection of ml models."""

    fields = {
        'ml_models',
        'next'
    }

    """A list containing ml models objects"""

    def __init__(self, **kwargs):
        super(MLModelCollection, self).__init__(**kwargs)
        self._type = 'ml_models'

    @staticmethod
    def convert_with_links(rpc_ml_models, limit, url=None,
                           expand=False, **kwargs):
        context = pecan.request.context
        collection = MLModelCollection()
        collection.ml_models = \
            [view.format_ml_model(context, url, p.as_dict())
             for p in rpc_ml_models]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class MLModelController(base.Controller):
    """Controller for MLModels."""

    _custom_actions = {
        'upload_trained_model': ['POST'],
        'deploy': ['GET'],
        'undeploy': ['GET'],
        'predict': ['POST']
    }

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def get_all(self, **kwargs):
        """Retrieve a list of ml models.

        """
        context = pecan.request.context
        policy.enforce(context, "ml_model:get_all",
                       action="ml_model:get_all")
        return self._get_ml_models_collection(**kwargs)

    def _get_ml_models_collection(self, **kwargs):
        context = pecan.request.context
        if utils.is_all_projects(kwargs):
            policy.enforce(context, "ml_model:get_all_all_projects",
                           action="ml_model:get_all_all_projects")
            context.all_projects = True
        kwargs.pop('all_projects', None)
        limit = api_utils.validate_limit(kwargs.pop('limit', None))
        sort_dir = api_utils.validate_sort_dir(kwargs.pop('sort_dir', 'asc'))
        sort_key = kwargs.pop('sort_key', 'id')
        resource_url = kwargs.pop('resource_url', None)
        expand = kwargs.pop('expand', None)

        ml_model_allowed_filters = ['name', 'status', 'project_id', 'user_id',
                                    'type']
        filters = {}
        for filter_key in ml_model_allowed_filters:
            if filter_key in kwargs:
                policy_action = policies.MLMODEL % ('get_one:' + filter_key)
                context.can(policy_action, might_not_exist=True)
                filter_value = kwargs.pop(filter_key)
                filters[filter_key] = filter_value
        marker_obj = None
        marker = kwargs.pop('marker', None)
        if marker:
            marker_obj = objects.ML_Model.get_by_uuid(context,
                                                      marker)
        if kwargs:
            unknown_params = [str(k) for k in kwargs]
            msg = _("Unknown parameters: %s") % ", ".join(unknown_params)
            raise exception.InvalidValue(msg)

        ml_models = objects.ML_Model.list(context,
                                          limit,
                                          marker_obj,
                                          sort_key,
                                          sort_dir,
                                          filters=filters)
        return MLModelCollection.convert_with_links(ml_models, limit,
                                                    url=resource_url,
                                                    expand=expand,
                                                    sort_key=sort_key,
                                                    sort_dir=sort_dir)

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def get_one(self, ml_model_ident, **kwargs):
        """Retrieve information about the given ml_model.

        :param ml_model_ident: UUID or name of a ml_model.
        """
        context = pecan.request.context
        if utils.is_all_projects(kwargs):
            policy.enforce(context, "ml_model:get_one_all_projects",
                           action="ml_model:get_one_all_projects")
            context.all_projects = True
        ml_model = utils.get_ml_model(ml_model_ident)
        check_policy_on_ml_model(ml_model.as_dict(), "ml_model:get_one")
        return view.format_ml_model(context, pecan.request.host_url,
                                    ml_model.as_dict())

    @base.Controller.api_version("1.0")
    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def upload_trained_model(self, ml_model_ident, **kwargs):
        context = pecan.request.context
        LOG.debug(ml_model_ident)
        ml_model = utils.get_ml_model(ml_model_ident)
        LOG.debug(ml_model)
        ml_model.ml_data = pecan.request.body
        ml_model.save(context)
        pecan.response.status = 200
        compute_api = pecan.request.compute_api
        new_model = view.format_ml_model(context, pecan.request.host_url,
                                         ml_model.as_dict())
        # compute_api.ml_model_create(context, new_model)
        return new_model

    @base.Controller.api_version("1.0")
    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def predict(self, ml_model_ident, **kwargs):
        context = pecan.request.context
        LOG.debug(ml_model_ident)
        ml_model = utils.get_ml_model(ml_model_ident)
        pecan.response.status = 200
        compute_api = pecan.request.compute_api
        host_ip = ml_model.deployed_on
        LOG.debug(pecan.request.POST['file'])
        predict_dict = {
            "data": base64.b64encode(pecan.request.POST['file'].file.read())
        }
        LOG.debug(predict_dict)
        prediction = compute_api.ml_model_predict(context, ml_model_ident, host_ip, **predict_dict)
        return prediction

    @base.Controller.api_version("1.0")
    @pecan.expose('json')
    @api_utils.enforce_content_types(['application/json'])
    @exception.wrap_pecan_controller_exception
    @validation.validated(schema.ml_model_create)
    def post(self, **ml_model_dict):
        return self._do_post(**ml_model_dict)

    def _do_post(self, **ml_model_dict):
        """Create or run a new ml model.

        :param ml_model_dict: a ml_model within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, "ml_model:create",
                       action="ml_model:create")

        ml_model_dict['project_id'] = context.project_id
        ml_model_dict['user_id'] = context.user_id
        name = ml_model_dict.get('name')
        ml_model_dict['name'] = name

        ml_model_dict['status'] = consts.CREATED
        ml_model_dict['ml_type'] = ml_model_dict['type']
        ml_model_dict['flavor_id'] = ml_model_dict['flavor_id']
        extra_spec = {}
        extra_spec['hints'] = ml_model_dict.get('hints', None)
        # ml_model_dict["model_data"] = open("/home/bharath/model.zip", "rb").read()
        new_ml_model = objects.ML_Model(context, **ml_model_dict)
        # heat_client = clients.OpenStackClients(context).heat()

        ml_model = new_ml_model.create(context)
        LOG.debug(new_ml_model)
        # compute_api.ml_model_create(context, new_ml_model)
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('ml_models',
                                                 ml_model.id)
        pecan.response.status = 201
        return view.format_ml_model(context, pecan.request.host_url,
                                    ml_model.as_dict())

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    @validation.validated(schema.ml_model_update)
    def patch(self, ml_model_ident, **patch):
        """Update an existing ml model.

        :param ml_model_ident: UUID or name of a ml model.
        :param patch: a json PATCH document to apply to this ml model.
        """
        ml_model = utils.get_ml_model(ml_model_ident)
        check_policy_on_ml_model(ml_model.as_dict(), "ml_model:update")
        utils.validate_ml_model_state(ml_model, 'update')
        context = pecan.request.context
        compute_api = pecan.request.compute_api
        ml_model = compute_api.ml_model_update(context, ml_model, patch)
        return view.format_ml_model(context, pecan.request.node_url,
                                    ml_model.as_dict())

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    @validation.validate_query_param(pecan.request, schema.query_param_delete)
    def delete(self, ml_model_ident, **kwargs):
        """Delete a ML Model.

        :param ml_model_ident: UUID or Name of a ML Model.
        :param force: If True, allow to force delete the ML Model.
        """
        context = pecan.request.context
        ml_model = utils.get_ml_model(ml_model_ident)
        check_policy_on_ml_model(ml_model.as_dict(), "ml_model:delete")
        ml_model.destroy(context)
        pecan.response.status = 204

    def _do_compute_node_schedule(self, context, ml_model, url, compute_api, host_url):
        target_status = "COMPLETE"
        timeout = 500
        sleep_interval = 5
        stack_data = {
            "files": {},
            "disable_rollback": True,
            "parameters": {},
            "stack_name": "TENSORFLOW",
            "environment": {}
        }
        stack_data["template"] = yaml.safe_load(open(BASE_TEMPLATE))
        LOG.debug(stack_data)
        heat_client = clients.OpenStackClients(context).heat()
        stack = heat_client.stacks.create(**stack_data)
        LOG.debug(stack)
        stack_id = stack["stack"]["id"]
        while True:
            stack_result = heat_client.stacks.get(stack_id)
            status = stack_result.status
            if (status == target_status):
                break
        if status == target_status:
            ml_model.status = consts.DEPLOYED_COMPUTE_NODE
            ml_model.save(context)
        else:
            ml_model.status = consts.DEPLOYMENT_FAILED
            ml_model.save(context)
            return
        host_ip = None
        stack_result = heat_client.stacks.get(stack_id)
        for output in stack_result.outputs:
            if "public" in output["output_key"]:
                host_ip = output["output_value"]
        ml_model.deployed_on = host_ip
        ml_model.save(context)
        while True:
            hosts = objects.ComputeHost.list(context)
            LOG.debug(hosts)
            LOG.debug(host_ip)
            for host in hosts:
                if host_ip == host.hostname:
                    ml_model.status = consts.DEPLOYED
                    ml_model.url = url
                    ml_model.save(context)
                    ml_model.ml_data = None
                    new_model = view.format_ml_model(context, host_url,
                                                     ml_model.as_dict())
                    compute_api.ml_model_create(context, new_model, host_ip)
                    return
            greenthread.sleep(sleep_interval)
        return None

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def deploy(self, ml_model_ident, **kwargs):
        """Deploy ML Model.

        :param ml_model_ident: UUID or Name of a ML Model.
        """

        context = pecan.request.context
        ml_model = utils.get_ml_model(ml_model_ident)

        @utils.synchronized(ml_model.id)
        def do_compute_schedule(context, ml_model, url, compute_api, host_url):
            self._do_compute_node_schedule(context, ml_model, url, compute_api, host_url)

        check_policy_on_ml_model(ml_model.as_dict(), "ml_model:deploy")
        utils.validate_ml_model_state(ml_model, 'deploy')
        LOG.debug('Calling compute.ml_model_deploy with %s',
                  ml_model.id)
        ml_model.status = consts.DEPLOYMENT_STARTED
        url = pecan.request.url.replace("deploy", "predict")
        # ml_model.url = url
        compute_api = pecan.request.compute_api
        utils.spawn_n(do_compute_schedule, context, ml_model, url, compute_api, pecan.request.host_url)
        ml_model.save(context)
        pecan.response.status = 202
        return view.format_ml_model(context, pecan.request.host_url,
                                    ml_model.as_dict())

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def undeploy(self, ml_model_ident, **kwargs):
        """Undeploy ML Model.

        :param ml_model_ident: UUID or Name of a ML Model.
        """
        context = pecan.request.context
        ml_model = utils.get_ml_model(ml_model_ident)
        check_policy_on_ml_model(ml_model.as_dict(), "ml_model:deploy")
        utils.validate_ml_model_state(ml_model, 'undeploy')
        LOG.debug('Calling compute.ml_model_deploy with %s',
                  ml_model.id)
        ml_model.status = consts.CREATED
        ml_model.url = None
        ml_model.save(context)
        pecan.response.status = 202
        return view.format_ml_model(context, pecan.request.host_url,
                                    ml_model.as_dict())