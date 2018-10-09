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

from oslo_serialization import jsonutils
from oslo_versionedobjects import fields

from gyan.db import api as dbapi
from gyan.objects import base


@base.GyanObjectRegistry.register
class ComputeHost(base.GyanPersistentObject, base.GyanObject):
    # Version 1: Initial Version
    VERSION = '1'

    fields = {
        'id': fields.UUIDField(read_only=True, nullable=False),
        'hostname': fields.StringField(nullable=False)
    }

    @staticmethod
    def _from_db_object(context, compute_node, db_compute_node):
        """Converts a database entity to a formal object."""
        fields = set(compute_node.fields)
        for field in fields:
            setattr(compute_node, field, db_compute_node[field])

        compute_node.obj_reset_changes(recursive=True)
        return compute_node

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [ComputeNode._from_db_object(context, cls(context), obj)
                for obj in db_objects]

    @base.remotable
    def create(self, context):
        """Create a compute node record in the DB.

        :param context: Security context.

        """
        values = self.obj_get_changes()

        db_compute_host = dbapi.create_compute_host(context, values)
        self._from_db_object(context, self, db_compute_host)

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a compute node based on uuid.

        :param uuid: the uuid of a compute node.
        :param context: Security context
        :returns: a :class:`ComputeNode` object.
        """
        db_compute_node = dbapi.get_compute_host(context, uuid)
        compute_node = ComputeHost._from_db_object(
            context, cls(context), db_compute_node)
        return compute_node

    @base.remotable_classmethod
    def get_by_name(cls, context, hostname):
        db_compute_node = dbapi.get_compute_host_by_hostname(
            context, hostname)
        return cls._from_db_object(context, cls(), db_compute_node)

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of ComputeNode objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: filters when list resource providers.
        :returns: a list of :class:`ComputeNode` object.

        """
        db_compute_nodes = dbapi.list_compute_hosts(
            context, limit=limit, marker=marker, sort_key=sort_key,
            sort_dir=sort_dir, filters=filters)
        return ComputeHost._from_db_object_list(
            db_compute_nodes, cls, context)

    @base.remotable
    def destroy(self, context=None):
        """Delete the ComputeNode from the DB.

        :param context: Security context.
        """
        dbapi.destroy_compute_host(context, self.uuid)
        self.obj_reset_changes(recursive=True)

    @base.remotable
    def save(self, context=None):
        """Save updates to this ComputeNode.

        Updates will be made column by column based on the result
        of self.what_changed().

        :param context: Security context.
        """
        updates = self.obj_get_changes()
        dbapi.update_compute_host(context, self.uuid, updates)
        self.obj_reset_changes(recursive=True)