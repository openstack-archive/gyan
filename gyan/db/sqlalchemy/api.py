# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
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

"""SQLAlchemy storage backend."""

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_utils import importutils
from oslo_utils import strutils
from oslo_utils import timeutils
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import func

from gyan.common import consts
from gyan.common import exception
from gyan.common.i18n import _
import gyan.conf
from gyan.db.sqlalchemy import models

profiler_sqlalchemy = importutils.try_import('osprofiler.sqlalchemy')

CONF = gyan.conf.CONF

_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.enginefacade.get_legacy_facade()
        if profiler_sqlalchemy:
            if CONF.profiler.enabled and CONF.profiler.trace_sqlalchemy:
                profiler_sqlalchemy.add_tracing(sa, _FACADE.get_engine(), "db")
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.

    :param session: if present, the session to use
    """

    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


def add_identity_filter(query, value):
    """Adds an identity filter to a query.

    Filters results by ID, if supplied value is a valid integer.
    Otherwise attempts to filter results by UUID.

    :param query: Initial query to add filter to.
    :param value: Value for filtering results by.
    :return: Modified query.
    """
    if strutils.is_int_like(value):
        return query.filter_by(id=value)
    elif uuidutils.is_uuid_like(value):
        return query.filter_by(uuid=value)
    else:
        raise exception.InvalidIdentity(identity=value)


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None, default_sort_key='id'):
    if not query:
        query = model_query(model)
    sort_keys = [default_sort_key]
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    try:
        query = db_utils.paginate_query(query, model, limit, sort_keys,
                                        marker=marker, sort_dir=sort_dir)
    except db_exc.InvalidSortKey:
        raise exception.InvalidParameterValue(
            _('The sort_key value "%(key)s" is an invalid field for sorting')
            % {'key': sort_key})
    return query.all()


class Connection(object):
    """SqlAlchemy connection."""

    def __init__(self):
        pass

    def _add_project_filters(self, context, query):
        if context.is_admin and context.all_projects:
            return query

        if context.project_id:
            query = query.filter_by(project_id=context.project_id)
        else:
            query = query.filter_by(user_id=context.user_id)

        return query

    def _add_filters(self, query, model, filters=None, filter_names=None):
        """Generic way to add filters to a Gyan model"""
        if not filters:
            return query

        if not filter_names:
            filter_names = []

        for name in filter_names:
            if name in filters:
                value = filters[name]
                if isinstance(value, list):
                    column = getattr(model, name)
                    query = query.filter(column.in_(value))
                else:
                    column = getattr(model, name)
                    query = query.filter(column == value)

        return query

    def _add_compute_hosts_filters(self, query, filters):
        filter_names = None
        return self._add_filters(query, models.ComputeHost, filters=filters,
                                 filter_names=filter_names)

    def list_compute_hosts(self, context, filters=None, limit=None,
                           marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.ComputeHost)
        query = self._add_compute_hosts_filters(query, filters)
        return _paginate_query(models.ComputeHost, limit, marker,
                               sort_key, sort_dir, query,
                               default_sort_key='id')

    def create_compute_host(self, context, values):
        # ensure defaults are present for new compute hosts
        if not values.get('id'):
            values['id'] = uuidutils.generate_uuid()

        compute_host = models.ComputeHost()
        compute_host.update(values)
        try:
            compute_host.save()
        except db_exc.DBDuplicateEntry:
            raise exception.ComputeHostAlreadyExists(
                field='UUID', value=values['uuid'])
        return compute_host

    def get_compute_host(self, context, host_uuid):
        query = model_query(models.ComputeHost)
        query = query.filter_by(id=host_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.ComputeHostNotFound(
                compute_host=host_uuid)

    def get_compute_host_by_hostname(self, context, hostname):
        query = model_query(models.ComputeHost)
        query = query.filter_by(hostname=hostname)
        try:
            return query.one()
        except NoResultFound:
            raise exception.ComputeHostNotFound(
                compute_host=hostname)
        except MultipleResultsFound:
            raise exception.Conflict('Multiple compute hosts exist with same '
                                     'hostname. Please use the uuid instead.')

    def destroy_compute_host(self, context, host_uuid):
        session = get_session()
        with session.begin():
            query = model_query(models.ComputeHost, session=session)
            query = query.filter_by(uuid=host_uuid)
            count = query.delete()
            if count != 1:
                raise exception.ComputeHostNotFound(
                    compute_host=host_uuid)

    def update_compute_host(self, context, host_uuid, values):
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing ComputeHost.")
            raise exception.InvalidParameterValue(err=msg)

        return self._do_update_compute_host(host_uuid, values)

    def _do_update_compute_host(self, host_uuid, values):
        session = get_session()
        with session.begin():
            query = model_query(models.ComputeHost, session=session)
            query = query.filter_by(uuid=host_uuid)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.ComputeHostNotFound(
                    compute_host=host_uuid)

            ref.update(values)
        return ref

    def list_ml_models(self, context, filters=None, limit=None,
                      marker=None, sort_key=None, sort_dir=None):
        query = model_query(models.Capsule)
        query = self._add_project_filters(context, query)
        query = self._add_ml_models_filters(query, filters)
        return _paginate_query(models.Capsule, limit, marker,
                               sort_key, sort_dir, query)

    def create_ml_model(self, context, values):
        # ensure defaults are present for new ml_models
        # here use the infra container uuid as the ml_model uuid
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()
        ml_model = models.ML_Model()
        ml_model.update(values)
        try:
            ml_model.save()
        except db_exc.DBDuplicateEntry:
            raise exception.MLModelAlreadyExists(field='UUID',
                                                 value=values['uuid'])
        return ml_model

    def get_ml_model_by_uuid(self, context, ml_model_uuid):
        query = model_query(models.ML_Model)
        query = self._add_project_filters(context, query)
        query = query.filter_by(uuid=ml_model_uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.MLModelNotFound(ml_model=ml_model_uuid)

    def get_ml_model_by_name(self, context, ml_model_name):
        query = model_query(models.ML_Model)
        query = self._add_project_filters(context, query)
        query = query.filter_by(meta_name=ml_model_name)
        try:
            return query.one()
        except NoResultFound:
            raise exception.MLModelNotFound(ml_model=ml_model_name)
        except MultipleResultsFound:
            raise exception.Conflict('Multiple ml_models exist with same '
                                     'name. Please use the ml_model uuid '
                                     'instead.')

    def destroy_ml_model(self, context, ml_model_id):
        session = get_session()
        with session.begin():
            query = model_query(models.ML_Model, session=session)
            query = add_identity_filter(query, ml_model_id)
            count = query.delete()
            if count != 1:
                raise exception.MLModelNotFound(ml_model_id)

    def update_ml_model(self, context, ml_model_id, values):
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing ML Model.")
            raise exception.InvalidParameterValue(err=msg)

        return self._do_update_ml_model_id(ml_model_id, values)

    def _do_update_ml_model_id(self, ml_model_id, values):
        session = get_session()
        with session.begin():
            query = model_query(models.ML_Model, session=session)
            query = add_identity_filter(query, ml_model_id)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.MLModelNotFound(ml_model=ml_model_id)

            ref.update(values)
        return ref

    def _add_ml_models_filters(self, query, filters):
        filter_names = ['uuid', 'project_id', 'user_id']
        return self._add_filters(query, models.ML_Model, filters=filters,
                                 filter_names=filter_names)
