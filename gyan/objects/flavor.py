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

from oslo_log import log as logging
from oslo_versionedobjects import fields

from gyan.common import exception
from gyan.common.i18n import _
from gyan.db import api as dbapi
from gyan.objects import base
from gyan.objects import fields as z_fields


LOG = logging.getLogger(__name__)


@base.GyanObjectRegistry.register
class Flavor(base.GyanPersistentObject, base.GyanObject):
    VERSION = '1'

    fields = {
        'id': fields.UUIDField(nullable=True),
        'name': fields.StringField(nullable=True),
        'cpu': fields.StringField(nullable=True),
        'memory': fields.StringField(nullable=True),
        'python_version': fields.StringField(nullable=True),
        'disk': fields.BooleanField(nullable=True),
        'additional_details': fields.StringField(nullable=True),
        'created_at': fields.DateTimeField(tzinfo_aware=False, nullable=True),
        'updated_at': fields.DateTimeField(tzinfo_aware=False, nullable=True),
        'driver': z_fields.ModelField(nullable=True)
    }

    @staticmethod
    def _from_db_object(flavor, db_flavor):
        """Converts a database entity to a formal object."""
        for field in flavor.fields:
            setattr(flavor, field, db_flavor[field])

        flavor.obj_reset_changes()
        return flavor

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [Flavor._from_db_object(cls(context), obj)
                for obj in db_objects]

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a ml model based on uuid and return a :class:`ML_Model` object.

        :param uuid: the uuid of a ml model.
        :param context: Security context
        :returns: a :class:`ML_Model` object.
        """
        db_flavor = dbapi.get_flavor_by_uuid(context, uuid)
        flavor = Flavor._from_db_object(cls(context), db_flavor)
        return flavor

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a flavor based on name and return a Flavor object.

        :param name: the logical name of a ml model.
        :param context: Security context
        :returns: a :class:`ML_Model` object.
        """
        db_flavor = dbapi.get_flavor_by_name(context, name)
        flavor = Flavor._from_db_object(cls(context), db_flavor)
        return flavor

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of Flavor objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: filters when list ml models, the filter name could be
                        'name', 'project_id', 'user_id'.
        :returns: a list of :class:`ML_Model` object.

        """
        db_flavors = dbapi.list_flavors(
            context, limit=limit, marker=marker, sort_key=sort_key,
            sort_dir=sort_dir, filters=filters)
        return Flavor._from_db_object_list(db_flavors, cls, context)

    def create(self, context):
        """Create a Flavor record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ML_Model(context)

        """
        values = self.obj_get_changes()
        db_flavor = dbapi.create_flavor(context, values)
        return self._from_db_object(self, db_flavor)

    @base.remotable
    def destroy(self, context=None):
        """Delete the Flavor from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ML Model(context)
        """
        dbapi.destroy_flavor(context, self.id)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this Flavor.

        Updates will be made column by column based on the result
        of self.what_changed().

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ML Model(context)
        """
        updates = self.obj_get_changes()
        dbapi.update_ml_model(context, self.id, updates)

        self.obj_reset_changes()

    def obj_load_attr(self, attrname):
        if not self._context:
            raise exception.OrphanedObjectError(method='obj_load_attr',
                                                objtype=self.obj_name())

        LOG.debug("Lazy-loading '%(attr)s' on %(name)s uuid %(uuid)s",
                  {'attr': attrname,
                   'name': self.obj_name(),
                   'uuid': self.uuid,
                   })

        self.obj_reset_changes([attrname])
