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
import json

from oslo_log import log as logging
from oslo_utils import strutils
from oslo_utils import uuidutils
import pecan
import six

from gyan.api.controllers import base
from gyan.api.controllers import link
from gyan.api.controllers.v1 import collection
from gyan.api.controllers.v1.schemas import flavors as schema
from gyan.api.controllers.v1.views import flavors_view as view
from gyan.api import utils as api_utils
from gyan.api import validation
from gyan.common import consts
from gyan.common import context as gyan_context
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common.policies import flavor as policies
from gyan.common import policy
from gyan.common import utils
import gyan.conf
from gyan import objects

CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)


def check_policy_on_flavor(flavor, action):
    context = pecan.request.context
    policy.enforce(context, action, flavor, action=action)


class FlavorCollection(collection.Collection):
    """API representation of a collection of flavors."""

    fields = {
        'flavors',
        'next'
    }

    """A list containing flavor objects"""

    def __init__(self, **kwargs):
        super(FlavorCollection, self).__init__(**kwargs)
        self._type = 'flavors'

    @staticmethod
    def convert_with_links(rpc_flavors, limit, url=None,
                           expand=False, **kwargs):
        context = pecan.request.context
        collection = FlavorCollection()
        collection.flavors = \
            [view.format_flavor(url, p)
             for p in rpc_flavors]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class FlavorController(base.Controller):
    """Controller for Flavors."""

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def get_all(self, **kwargs):
        """Retrieve a list of flavors.

        """
        context = pecan.request.context
        policy.enforce(context, "flavor:get_all",
                       action="flavor:get_all")
        return self._get_flavors_collection(**kwargs)

    def _get_flavors_collection(self, **kwargs):
        context = pecan.request.context
        if utils.is_all_projects(kwargs):
            policy.enforce(context, "flavor:get_all_all_projects",
                           action="flavor:get_all_all_projects")
            context.all_projects = True
        kwargs.pop('all_projects', None)
        limit = api_utils.validate_limit(kwargs.pop('limit', None))
        sort_dir = api_utils.validate_sort_dir(kwargs.pop('sort_dir', 'asc'))
        sort_key = kwargs.pop('sort_key', 'id')
        resource_url = kwargs.pop('resource_url', None)
        expand = kwargs.pop('expand', None)

        flavor_allowed_filters = ['name', 'cpu', 'python_version', 'driver',
                                   'memory', 'disk', 'additional_details']
        filters = {}
        for filter_key in flavor_allowed_filters:
            if filter_key in kwargs:
                policy_action = policies.FLAVOR % ('get_one:' + filter_key)
                context.can(policy_action, might_not_exist=True)
                filter_value = kwargs.pop(filter_key)
                filters[filter_key] = filter_value
        marker_obj = None
        marker = kwargs.pop('marker', None)
        if marker:
            marker_obj = objects.Flavor.get_by_uuid(context,
                                                      marker)
        if kwargs:
            unknown_params = [str(k) for k in kwargs]
            msg = _("Unknown parameters: %s") % ", ".join(unknown_params)
            raise exception.InvalidValue(msg)

        flavors = objects.Flavor.list(context,
                                          limit,
                                          marker_obj,
                                          sort_key,
                                          sort_dir,
                                          filters=filters)
        return FlavorCollection.convert_with_links(flavors, limit,
                                                    url=resource_url,
                                                    expand=expand,
                                                    sort_key=sort_key,
                                                    sort_dir=sort_dir)

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def get_one(self, flavor_ident, **kwargs):
        """Retrieve information about the given flavor.

        :param flavor_ident: UUID or name of a flavor.
        """
        context = pecan.request.context
        if utils.is_all_projects(kwargs):
            policy.enforce(context, "flavor:get_one_all_projects",
                           action="flavor:get_one_all_projects")
            context.all_projects = True
        flavor = utils.get_flavor(flavor_ident)
        check_policy_on_flavor(flavor.as_dict(), "flavor:get_one")
        return view.format_flavor(pecan.request.host_url,
                                    flavor)

    @base.Controller.api_version("1.0")
    @pecan.expose('json')
    @api_utils.enforce_content_types(['application/json'])
    @exception.wrap_pecan_controller_exception
    @validation.validated(schema.flavor_create)
    def post(self, **flavor_dict):
        return self._do_post(**flavor_dict)

    def _do_post(self, **flavor_dict):
        """Create or run a new flavor.

        :param flavor_dict: a flavor within the request body.
        """
        context = pecan.request.context
        policy.enforce(context, "flavor:create",
                       action="flavor:create")

        LOG.debug(flavor_dict)
        flavor_dict["additional_details"] = json.dumps(flavor_dict["additional_details"])
        LOG.debug(flavor_dict)
        new_flavor = objects.Flavor(context, **flavor_dict)
        flavor = new_flavor.create(context)
        LOG.debug(new_flavor)
        # compute_api.flavor_create(context, new_flavor)
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('flavors',
                                                 flavor.id)
        pecan.response.status = 201
        return view.format_flavor(pecan.request.host_url,
                                    flavor)

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    def patch(self, flavor_ident, **patch):
        """Update an existing flavor.

        :param flavor_ident: UUID or name of a flavor.
        :param patch: a json PATCH document to apply to this flavor.
        """
        context = pecan.request.context
        flavor = utils.get_flavor(flavor_ident)
        check_policy_on_flavor(flavor.as_dict(), "flavor:update")
        return view.format_flavor(context, pecan.request.host_url,
                                    flavor.as_dict())

    @pecan.expose('json')
    @exception.wrap_pecan_controller_exception
    @validation.validate_query_param(pecan.request, schema.query_param_delete)
    def delete(self, flavor_ident, **kwargs):
        """Delete a flavor.

        :param flavor_ident: UUID or Name of a Flavor.
        :param force: If True, allow to force delete the Flavor.
        """
        context = pecan.request.context
        flavor = utils.get_flavor(flavor_ident)
        check_policy_on_flavor(flavor.as_dict(), "flavor:delete")
        flavor.destroy(context)
        pecan.response.status = 204