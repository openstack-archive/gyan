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
"""
Base API for Database
"""

from oslo_db import api as db_api

from gyan.common import profiler
import gyan.conf

"""Add the database backend mapping here"""

CONF = gyan.conf.CONF
_BACKEND_MAPPING = {'sqlalchemy': 'gyan.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(CONF,
                                backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


@profiler.trace("db")
def _get_dbdriver_instance():
    """Return a DB API instance."""
    return IMPL


@profiler.trace("db")
def list_ml_models(context, filters=None, limit=None, marker=None,
                    sort_key=None, sort_dir=None):
    """List matching ML Models.

    Return a list of the specified columns for all ml models that match
    the specified filters.

    :param context: The security context
    :param filters: Filters to apply. Defaults to None.
    :param limit: Maximum number of ml_models to return.
    :param marker: the last item of the previous page; we return the next
                   result set.
    :param sort_key: Attribute by which results should be sorted.
    :param sort_dir: Direction in which results should be sorted.
                     (asc, desc)
    :returns: A list of tuples of the specified columns.
    """
    return _get_dbdriver_instance().list_ml_models(
        context, filters, limit, marker, sort_key, sort_dir)


@profiler.trace("db")
def create_ml_model(context, values):
    """Create a new ML Model.

    :param context: The security context
    :param values: A dict containing several items used to identify
                   and track the ML Model
    :returns: A ML Model.
    """
    return _get_dbdriver_instance().create_ml_model(context, values)


@profiler.trace("db")
def get_ml_model_by_uuid(context, ml_model_uuid):
    """Return a ML Model.

    :param context: The security context
    :param ml_model_uuid: The uuid of a ml model.
    :returns: A ML Model.
    """
    return _get_dbdriver_instance().get_ml_model_by_uuid(
        context, ml_model_uuid)


@profiler.trace("db")
def get_ml_model_by_name(context, ml_model_name):
    """Return a ML Model.

    :param context: The security context
    :param ml_model_name: The name of a ML Model.
    :returns: A ML Model.
    """
    return _get_dbdriver_instance().get_ml_model_by_name(
        context, ml_model_name)


@profiler.trace("db")
def destroy_ml_model(context, ml_model_id):
    """Destroy a ml model and all associated interfaces.

    :param context: Request context
    :param ml_model_id: The id or uuid of a ml model.
    """
    return _get_dbdriver_instance().destroy_ml_model(context, ml_model_id)


@profiler.trace("db")
def update_ml_model(context, ml_model_id, values):
    """Update properties of a ml model.

    :param context: Request context
    :param ml_model_id: The id or uuid of a ml model.
    :param values: The properties to be updated
    :returns: A ML Model.
    :raises: MLModelNotFound
    """
    return _get_dbdriver_instance().update_ml_model(
        context, ml_model_id, values)


@profiler.trace("db")
def list_flavors(context, filters=None, limit=None, marker=None,
                    sort_key=None, sort_dir=None):
    """List matching Flavors.

    Return a list of the specified columns for all flavors that match
    the specified filters.

    :param context: The security context
    :param filters: Filters to apply. Defaults to None.
    :param limit: Maximum number of flavors to return.
    :param marker: the last item of the previous page; we return the next
                   result set.
    :param sort_key: Attribute by which results should be sorted.
    :param sort_dir: Direction in which results should be sorted.
                     (asc, desc)
    :returns: A list of tuples of the specified columns.
    """
    return _get_dbdriver_instance().list_flavors(
        context, filters, limit, marker, sort_key, sort_dir)


@profiler.trace("db")
def create_flavor(context, values):
    """Create a new Flavor.

    :param context: The security context
    :param values: A dict containing several items used to identify
                   and track the ML Model
    :returns: A ML Model.
    """
    return _get_dbdriver_instance().create_flavor(context, values)


@profiler.trace("db")
def get_flavor_by_uuid(context, flavor_uuid):
    """Return a Flavor.

    :param context: The security context
    :param flavor_uuid: The uuid of a flavor.
    :returns: A Flavor.
    """
    return _get_dbdriver_instance().get_flavor_by_uuid(
        context, flavor_uuid)


@profiler.trace("db")
def get_flavor_by_name(context, flavor_name):
    """Return a Flavor.

    :param context: The security context
    :param flavor_name: The name of a Flavor.
    :returns: A Flavor.
    """
    return _get_dbdriver_instance().get_flavor_by_name(
        context, flavor_name)


@profiler.trace("db")
def destroy_flavor(context, flavor_id):
    """Destroy a flavor and all associated interfaces.

    :param context: Request context
    :param flavor_id: The id or uuid of a flavor.
    """
    return _get_dbdriver_instance().destroy_flavor(context, flavor_id)


@profiler.trace("db")
def update_flavor(context, flavor_id, values):
    """Update properties of a flavor.

    :param context: Request context
    :param flavor_id: The id or uuid of a flavor.
    :param values: The properties to be updated
    :returns: A Flavor.
    :raises: FlavorNotFound
    """
    return _get_dbdriver_instance().update_flavor(
        context, flavor_id, values)


@profiler.trace("db")
def list_compute_hosts(context, filters=None, limit=None, marker=None,
                       sort_key=None, sort_dir=None):
    """List matching compute hosts.

    Return a list of the specified columns for all compute hosts that match
    the specified filters.

    :param context: The security context
    :param filters: Filters to apply. Defaults to None.
    :param limit: Maximum number of compute nodes to return.
    :param marker: the last item of the previous page; we return the next
                   result set.
    :param sort_key: Attribute by which results should be sorted.
    :param sort_dir: Direction in which results should be sorted.
                     (asc, desc)
    :returns: A list of tuples of the specified columns.
    """
    return _get_dbdriver_instance().list_compute_hosts(
        context, filters, limit, marker, sort_key, sort_dir)


@profiler.trace("db")
def create_compute_host(context, values):
    """Create a new compute host.

    :param context: The security context
    :param values: A dict containing several items used to identify
                   and track the compute node, and several dicts which are
                   passed into the Drivers when managing this compute host.
    :returns: A compute host.
    """
    return _get_dbdriver_instance().create_compute_host(context, values)


@profiler.trace("db")
def get_compute_host(context, host_uuid):
    """Return a compute host.

    :param context: The security context
    :param node_uuid: The uuid of a compute node.
    :returns: A compute node.
    """
    return _get_dbdriver_instance().get_compute_host(context, host_uuid)


@profiler.trace("db")
def get_compute_host_by_hostname(context, hostname):
    """Return a compute node.

    :param context: The security context
    :param hostname: The hostname of a compute node.
    :returns: A compute node.
    """
    return _get_dbdriver_instance().get_compute_host_by_hostname(
        context, hostname)


@profiler.trace("db")
def destroy_compute_host(context, host_uuid):
    """Destroy a compute node and all associated interfaces.

    :param context: Request context
    :param node_uuid: The uuid of a compute node.
    """
    return _get_dbdriver_instance().destroy_compute_host(context, host_uuid)


@profiler.trace("db")
def update_compute_host(context, host_uuid, values):
    """Update properties of a compute node.

    :param context: Request context
    :param node_uuid: The uuid of a compute node.
    :param values: The properties to be updated
    :returns: A compute node.
    :raises: ComputeNodeNotFound
    """
    return _get_dbdriver_instance().update_compute_host(
        context, host_uuid, values)
