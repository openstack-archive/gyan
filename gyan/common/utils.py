# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# It's based on oslo.i18n usage in OpenStack Keystone project and
# recommendations from
# https://docs.openstack.org/oslo.i18n/latest/user/usage.html

"""Utilities and helper functions."""
import base64
import binascii
import eventlet
import functools
import inspect
import json
import mimetypes
import os
import zipfile

from oslo_concurrency import processutils
from oslo_context import context as common_context
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import strutils
import pecan
import six

from gyan.api import utils as api_utils
from gyan.common import consts
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common import privileged
import gyan.conf
from gyan import objects

CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)

VALID_STATES = {
    'deploy': [consts.CREATED, consts.UNDEPLOYED, consts.SCHEDULED],
    'undeploy': [consts.DEPLOYED]
}
def safe_rstrip(value, chars=None):
    """Removes trailing characters from a string if that does not make it empty

    :param value: A string value that will be stripped.
    :param chars: Characters to remove.
    :return: Stripped value.

    """
    if not isinstance(value, six.string_types):
        LOG.warning(
            "Failed to remove trailing character. Returning original object. "
            "Supplied object is not a string: %s.", value)
        return value

    return value.rstrip(chars) or value


def _do_allow_certain_content_types(func, content_types_list):
    # Allows you to bypass pecan's content-type restrictions
    cfg = pecan.util._cfg(func)
    cfg.setdefault('content_types', {})
    cfg['content_types'].update((value, '')
                                for value in content_types_list)
    return func


def allow_certain_content_types(*content_types_list):
    def _wrapper(func):
        return _do_allow_certain_content_types(func, content_types_list)
    return _wrapper


def allow_all_content_types(f):
    return _do_allow_certain_content_types(f, mimetypes.types_map.values())


def spawn_n(func, *args, **kwargs):
    """Passthrough method for eventlet.spawn_n.

    This utility exists so that it can be stubbed for testing without
    interfering with the service spawns.

    It will also grab the context from the threadlocal store and add it to
    the store on the new thread.  This allows for continuity in logging the
    context when using this method to spawn a new thread.
    """
    _context = common_context.get_current()

    @functools.wraps(func)
    def context_wrapper(*args, **kwargs):
        # NOTE: If update_store is not called after spawn_n it won't be
        # available for the logger to pull from threadlocal storage.
        if _context is not None:
            _context.update_store()
        func(*args, **kwargs)

    eventlet.spawn_n(context_wrapper, *args, **kwargs)


def translate_exception(function):
    """Wraps a method to catch exceptions.

    If the exception is not an instance of GyanException,
    translate it into one.
    """

    @functools.wraps(function)
    def decorated_function(self, context, *args, **kwargs):
        try:
            return function(self, context, *args, **kwargs)
        except Exception as e:
            if not isinstance(e, exception.GyanException):
                LOG.exception("Unexpected error: %s", six.text_type(e))
                e = exception.GyanException("Unexpected error: %s"
                                           % six.text_type(e))
                raise e
            raise

    return decorated_function


def custom_execute(*cmd, **kwargs):
    try:
        return processutils.execute(*cmd, **kwargs)
    except processutils.ProcessExecutionError as e:
        sanitized_cmd = strutils.mask_password(' '.join(cmd))
        raise exception.CommandError(cmd=sanitized_cmd,
                                     error=six.text_type(e))


def is_all_projects(search_opts):
    all_projects = search_opts.get('all_projects')
    if all_projects:
        try:
            all_projects = strutils.bool_from_string(all_projects, True)
        except ValueError:
            bools = ', '.join(strutils.TRUE_STRINGS + strutils.FALSE_STRINGS)
            raise exception.InvalidValue(_('Valid all_projects values are: %s')
                                         % bools)
    else:
        all_projects = False
    return all_projects


def get_ml_model(ml_model_ident):
    ml_model = api_utils.get_resource('ML_Model', ml_model_ident)
    if not ml_model:
        pecan.abort(404, ('Not found; the ml model you requested '
                          'does not exist.'))

    return ml_model

def get_flavor(flavor_ident):
    flavor = api_utils.get_resource('Flavor', flavor_ident)
    if not flavor:
        pecan.abort(404, ('Not found; the ml model you requested '
                          'does not exist.'))

    return flavor

def validate_ml_model_state(ml_model, action):
    if ml_model.status not in VALID_STATES[action]:
        raise exception.InvalidStateException(
            id=ml_model.id,
            action=action,
            actual_state=ml_model.status)


def get_wrapped_function(function):
    """Get the method at the bottom of a stack of decorators."""
    if not hasattr(function, '__closure__') or not function.__closure__:
        return function

    def _get_wrapped_function(function):
        if not hasattr(function, '__closure__') or not function.__closure__:
            return None

        for closure in function.__closure__:
            func = closure.cell_contents

            deeper_func = _get_wrapped_function(func)
            if deeper_func:
                return deeper_func
            elif hasattr(closure.cell_contents, '__call__'):
                return closure.cell_contents

        return function

    return _get_wrapped_function(function)


def wrap_ml_model_event(prefix):
    """Warps a method to log the event taken on the ml_model, and result.

    This decorator wraps a method to log the start and result of an event, as
    part of an action taken on a ml_model.
    """
    def helper(function):

        @functools.wraps(function)
        def decorated_function(self, context, *args, **kwargs):
            wrapped_func = get_wrapped_function(function)
            keyed_args = inspect.getcallargs(wrapped_func, self, context,
                                             *args, **kwargs)
            ml_model_uuid = keyed_args['ml_model'].uuid

            event_name = '{0}_{1}'.format(prefix, function.__name__)
            with EventReporter(context, event_name, ml_model_uuid):
                return function(self, context, *args, **kwargs)
        return decorated_function
    return helper


def wrap_exception():
    def helper(function):

        @functools.wraps(function)
        def decorated_function(self, context, ml_model, *args, **kwargs):
            try:
                return function(self, context, ml_model, *args, **kwargs)
            except exception.DockerError as e:
                with excutils.save_and_reraise_exception(reraise=False):
                    LOG.error("Error occurred while calling Docker API: %s",
                              six.text_type(e))
            except Exception as e:
                with excutils.save_and_reraise_exception(reraise=False):
                    LOG.exception("Unexpected exception: %s", six.text_type(e))
        return decorated_function
    return helper


def is_close(x, y, rel_tol=1e-06, abs_tol=0.0):
    return abs(x - y) <= max(rel_tol * max(abs(x), abs(y)), abs_tol)


def is_less_than(x, y):
    if isinstance(x, int) and isinstance(y, int):
        return x < y
    if isinstance(x, float) or isinstance(y, float):
        return False if (x - y) >= 0 or is_close(x, y) else True


def encode_file_data(data):
    if six.PY3 and isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


def decode_file_data(data):
    # Py3 raises binascii.Error instead of TypeError as in Py27
    try:
        return base64.b64decode(data)
    except (TypeError, binascii.Error):
        raise exception.Base64Exception()


def save_model(path, model):
    file_path = os.path.join(path, model.id)
    with open(file_path+'.zip', 'wb') as f:
        f.write(model.ml_data)
    zip_ref = zipfile.ZipFile(file_path+'.zip', 'r')
    zip_ref.extractall(file_path)
    zip_ref.close()
