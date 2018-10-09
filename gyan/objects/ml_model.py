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
from gyan.objects import exec_instance as exec_inst
from gyan.objects import fields as z_fields
from gyan.objects import pci_device


LOG = logging.getLogger(__name__)

@base.GyanObjectRegistry.register
class ML_Model(base.GyanPersistentObject, base.GyanObject):
    VERSION = '1'

    fields = {
        'id': fields.UUIDField(nullable=True),
        'name': fields.StringField(nullable=True),
        'project_id': fields.StringField(nullable=True),
        'user_id': fields.StringField(nullable=True),
        'status': fields.StringField(nullable=True),
        'status_reason': fields.StringField(nullable=True),
        'url': fields.StringField(nullable=True),
        'deployed': fields.BooleanField(nullable=True),
        'node': fields.UUIDField(nullable=True),
        'hints': fields.StringField(nullable=True),
        'created_at': fields.DateTimeField(tzinfo_aware=False, nullable=True),
        'updated_at': fields.DateTimeField(tzinfo_aware=False, nullable=True)
    }

    @staticmethod
    def _from_db_object(ml_model, db_ml_model):
        """Converts a database entity to a formal object."""
        for field in ml_model.fields:
            setattr(ml_model, field, db_ml_model[field])

        ml_model.obj_reset_changes()
        return ml_model

    @staticmethod
    def _from_db_object_list(db_objects, cls, context):
        """Converts a list of database entities to a list of formal objects."""
        return [ML_Model._from_db_object(cls(context), obj)
                for obj in db_objects]

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a ml model based on uuid and return a :class:`ML_Model` object.

        :param uuid: the uuid of a ml model.
        :param context: Security context
        :returns: a :class:`ML_Model` object.
        """
        db_ml_model = dbapi.get_ml_model_by_uuid(context, uuid)
        ml_model = ML_Model._from_db_object(cls(context), db_ml_model)
        return ml_model

    @base.remotable_classmethod
    def get_by_name(cls, context, name):
        """Find a ml model based on name and return a Ml model object.

        :param name: the logical name of a ml model.
        :param context: Security context
        :returns: a :class:`ML_Model` object.
        """
        db_ml_model = dbapi.get_ml_model_by_name(context, name)
        ml_model = ML_Model._from_db_object(cls(context), db_ml_model)
        return ml_model

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None,
             sort_key=None, sort_dir=None, filters=None):
        """Return a list of ML Model objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param filters: filters when list ml models, the filter name could be
                        'name', 'project_id', 'user_id'.
        :returns: a list of :class:`ML_Model` object.

        """
        db_ml_models = dbapi.list_ml_models(
            context, limit=limit, marker=marker, sort_key=sort_key,
            sort_dir=sort_dir, filters=filters)
        return ML_Model._from_db_object_list(db_ml_models, cls, context)

    @base.remotable_classmethod
    def list_by_host(cls, context, host):
        """Return a list of ML Model objects by host.

        :param context: Security context.
        :param host: A compute host.
        :returns: a list of :class:`ML_Model` object.

        """
        db_ml_models = dbapi.list_ml_models(context, filters={'host': host})
        return ML_Model._from_db_object_list(db_ml_models, cls, context)

    def create(self, context):
        """Create a ML_Model record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Container(context)

        """
        values = self.obj_get_changes()
        db_ml_model = dbapi.create_ml_model(context, values)
        self._from_db_object(self, db_ml_model)

    @base.remotable
    def destroy(self, context=None):
        """Delete the ML_Model from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ML Model(context)
        """
        dbapi.destroy_ml_model(context, self.uuid)
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
