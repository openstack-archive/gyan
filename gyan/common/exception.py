# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gyan base exception handling.

Includes decorator for re-raising Gyan-type exceptions.

"""

import functools
import inspect
import re
import sys

from keystoneclient import exceptions as keystone_exceptions
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import uuidutils
import pecan
import six
from webob import util as woutil

from gyan.common.i18n import _
import gyan.conf

LOG = logging.getLogger(__name__)

CONF = gyan.conf.CONF

try:
    CONF.import_opt('fatal_exception_format_errors',
                    'oslo_versionedobjects.exception')
except cfg.NoSuchOptError as e:
    # Note:work around for gyan run against master branch
    # in devstack gate job, as gyan not branched yet
    # versionobjects kilo/master different version can
    # cause issue here. As it changed import group. So
    # add here before branch to prevent gate failure.
    # Bug: #1447873
    CONF.import_opt('fatal_exception_format_errors',
                    'oslo_versionedobjects.exception',
                    group='oslo_versionedobjects')


def wrap_exception(notifier=None, event_type=None):
    """This decorator wraps a method to catch any exceptions.

    It logs the exception as well as optionally sending
    it to the notification system.
    """
    def inner(f):
        def wrapped(self, context, *args, **kwargs):
            # Don't store self or context in the payload, it now seems to
            # contain confidential information.
            try:
                return f(self, context, *args, **kwargs)
            except Exception as e:
                with excutils.save_and_reraise_exception():
                    if notifier:
                        call_dict = inspect.getcallargs(f, self, context,
                                                        *args, **kwargs)
                        payload = dict(exception=e,
                                       private=dict(args=call_dict)
                                       )

                        temp_type = event_type
                        if not temp_type:
                            # If f has multiple decorators, they must use
                            # functools.wraps to ensure the name is
                            # propagated.
                            temp_type = f.__name__

                        notifier.error(context, temp_type, payload)

        return functools.wraps(f)(wrapped)
    return inner


OBFUSCATED_MSG = _('Your request could not be handled '
                   'because of a problem in the server. '
                   'Error Correlation id is: %s')


def wrap_controller_exception(func, func_server_error, func_client_error):
    """This decorator wraps controllers methods to handle exceptions:

    - if an unhandled Exception or a GyanException with an error code >=500
      is catched, raise a http 5xx ClientSideError and correlates it with a log
      message

    - if a GyanException is catched and its error code is <500, raise a http
      4xx and logs the excp in debug mode

    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as excp:
            if isinstance(excp, GyanException):
                http_error_code = excp.code
            else:
                http_error_code = 500

            if http_error_code >= 500:
                # log the error message with its associated
                # correlation id
                log_correlation_id = uuidutils.generate_uuid()
                LOG.exception("%(correlation_id)s:%(excp)s",
                              {'correlation_id': log_correlation_id,
                               'excp': str(excp)})
                # raise a client error with an obfuscated message
                return func_server_error(log_correlation_id, http_error_code)
            else:
                # raise a client error the original message
                LOG.debug(excp)
                return func_client_error(excp, http_error_code)
    return wrapped


def convert_excp_to_err_code(excp_name):
    """Convert Exception class name (CamelCase) to error-code (Snake-case)"""
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+',
                       excp_name)
    return '-'.join([str.lower(word) for word in words])


def wrap_pecan_controller_exception(func):
    """This decorator wraps pecan controllers to handle exceptions."""
    def _func_server_error(log_correlation_id, status_code):
        pecan.response.status = status_code
        return {
            'faultcode': 'Server',
            'status_code': status_code,
            'title': woutil.status_reasons[status_code],
            'description': six.text_type(OBFUSCATED_MSG % log_correlation_id),
        }

    def _func_client_error(excp, status_code):
        pecan.response.status = status_code
        return {
            'faultcode': 'Client',
            'faultstring': convert_excp_to_err_code(excp.__class__.__name__),
            'status_code': status_code,
            'title': six.text_type(excp),
            'description': six.text_type(excp),
        }

    return wrap_controller_exception(func,
                                     _func_server_error,
                                     _func_client_error)


def wrap_keystone_exception(func):
    """Wrap keystone exceptions and throw gyan specific exceptions."""
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except keystone_exceptions.AuthorizationFailure:
            raise AuthorizationFailure(
                client=func.__name__, message="reason: %s" % sys.exc_info()[1])
        except keystone_exceptions.ClientException:
            raise AuthorizationFailure(
                client=func.__name__,
                message="unexpected keystone client error occurred: %s"
                        % sys.exc_info()[1])
    return wrapped


class GyanException(Exception):
    """Base gyan Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs and hasattr(self, 'code'):
            self.kwargs['code'] = self.code

        if message:
            self.message = message

        try:
            self.message = str(self.message) % kwargs
        except KeyError:
            # kwargs doesn't match a variable in the message
            # log the issue and the kwargs
            LOG.exception('Exception in string format operation, '
                          'kwargs: %s', kwargs)
            try:
                ferr = CONF.fatal_exception_format_errors
            except cfg.NoSuchOptError:
                ferr = CONF.oslo_versionedobjects.fatal_exception_format_errors
            if ferr:
                raise

        super(GyanException, self).__init__(self.message)

    def __str__(self):
        if six.PY3:
            return self.message
        return self.message.encode('utf-8')

    def __unicode__(self):
        return self.message

    def format_message(self):
        if self.__class__.__name__.endswith('_Remote'):
            return self.args[0]
        else:
            return six.text_type(self)


class ObjectNotFound(GyanException):
    message = _("The %(name)s %(id)s could not be found.")


class ObjectNotUnique(GyanException):
    message = _("The %(name)s already exists.")


class ObjectActionError(GyanException):
    message = _('Object action %(action)s failed because: %(reason)s')


class ResourceNotFound(ObjectNotFound):
    message = _("The %(name)s resource %(id)s could not be found.")
    code = 404


class ResourceExists(ObjectNotUnique):
    message = _("The %(name)s resource already exists.")
    code = 409


class AuthorizationFailure(GyanException):
    message = _("%(client)s connection failed. %(message)s")


class UnsupportedObjectError(GyanException):
    message = _('Unsupported object type %(objtype)s')


class IncompatibleObjectVersion(GyanException):
    message = _('Version %(objver)s of %(objname)s is not supported')


class OrphanedObjectError(GyanException):
    message = _('Cannot call %(method)s on orphaned %(objtype)s object')


class Invalid(GyanException):
    message = _("Unacceptable parameters.")
    code = 400


class InvalidValue(Invalid):
    message = _("Received value '%(value)s' is invalid for type %(type)s.")


class ValidationError(Invalid):
    message = "%(detail)s"


class SchemaValidationError(ValidationError):
    message = "%(detail)s"


class InvalidUUID(Invalid):
    message = _("Expected a uuid but received %(uuid)s.")


class InvalidName(Invalid):
    message = _("Expected a name but received %(uuid)s.")


class InvalidDiscoveryURL(Invalid):
    message = _("Received invalid discovery URL '%(discovery_url)s' for "
                "discovery endpoint '%(discovery_endpoint)s'.")


class GetDiscoveryUrlFailed(GyanException):
    message = _("Failed to get discovery url from '%(discovery_endpoint)s'.")


class InvalidUuidOrName(Invalid):
    message = _("Expected a name or uuid but received %(uuid)s.")


class InvalidIdentity(Invalid):
    message = _("Expected an uuid or int but received %(identity)s.")


class InvalidCsr(Invalid):
    message = _("Received invalid csr %(csr)s.")


class HTTPNotFound(ResourceNotFound):
    pass


class Conflict(GyanException):
    message = _('Conflict.')
    code = 409


class ConflictOptions(Conflict):
    message = _('Conflicting options.')


class InvalidState(Conflict):
    message = _("Invalid resource state.")


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    message = _("%(err)s")


class InvalidParamInVersion(Invalid):
    message = _('Invalid param %(param)s because current request '
                'version is %(req_version)s. %(param)s is only '
                'supported from version %(min_version)s')


class InvalidQuotaValue(Invalid):
    message = _("Change would make usage less than 0 for the following "
                "resources: %(unders)s")


class InvalidQuotaMethodUsage(Invalid):
    message = _("Wrong quota method %(method)s used on resource %(res)s")


class PatchError(Invalid):
    message = _("Couldn't apply patch '%(patch)s'. Reason: %(reason)s")


class NotAuthorized(GyanException):
    message = _("Not authorized.")
    code = 403


class MLModelAlreadyExists(GyanException):
    message = _("A ML Model with %(field)s %(value)s already exists.")


class MLModelNotFound(GyanException):
    message = _("ML Model %(ml_model)s could not be found.")

class ConfigInvalid(GyanException):
    message = _("Invalid configuration file. %(error_msg)s")


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class ComputeHostNotFound(HTTPNotFound):
    message = _("Compute host %(compute_host)s could not be found.")


class GyanServiceNotFound(HTTPNotFound):
    message = _("Gyan service %(binary)s on host %(host)s could not be found.")


class ResourceProviderNotFound(HTTPNotFound):
    message = _("Resource provider %(resource_provider)s could not be found.")


class ResourceClassNotFound(HTTPNotFound):
    message = _("Resource class %(resource_class)s could not be found.")


class ComputeHostAlreadyExists(ResourceExists):
    message = _("A compute host with %(field)s %(value)s already exists.")


class GyanServiceAlreadyExists(ResourceExists):
    message = _("Service %(binary)s on host %(host)s already exists.")


class ResourceProviderAlreadyExists(ResourceExists):
    message = _("A resource provider with %(field)s %(value)s already exists.")


class ResourceClassAlreadyExists(ResourceExists):
    message = _("A resource class with %(field)s %(value)s already exists.")


class UniqueConstraintViolated(ResourceExists):
    message = _("A resource with %(fields)s violates unique constraint.")


class InvalidStateException(GyanException):
    message = _("Cannot %(action)s container %(id)s in %(actual_state)s state")
    code = 409


class ServerInError(GyanException):
    message = _('Went to status %(resource_status)s due to '
                '"%(status_reason)s"')


class ServerUnknownStatus(GyanException):
    message = _('%(result)s - Unknown status %(resource_status)s due to '
                '"%(status_reason)s"')


class EntityNotFound(GyanException):
    message = _("The %(entity)s (%(name)s) could not be found.")


class CommandError(GyanException):
    message = _("The command: %(cmd)s failed on the system, due to %(error)s")


class NoValidHost(GyanException):
    message = _("No valid host was found. %(reason)s")


class NotFound(GyanException):
    message = _("Resource could not be found.")
    code = 404


class SchedulerHostFilterNotFound(NotFound):
    message = _("Scheduler Host Filter %(filter_name)s could not be found.")


class ClassNotFound(NotFound):
    message = _("Class %(class_name)s could not be found: %(exception)s")


class ApiVersionsIntersect(GyanException):
    message = _("Version of %(name)s %(min_ver)s %(max_ver)s intersects "
                "with another versions.")


class ConnectionFailed(GyanException):
    message = _("Failed to connect to remote host")


class SocketException(GyanException):
    message = _("Socket exceptions")


class ResourcesUnavailable(GyanException):
    message = _("Insufficient compute resources: %(reason)s.")


class FileNotFound(GyanException):
    message = _("The expected file not exist")


class FailedParseStringToJson(GyanException):
    message = _("Failed parse string to json: %(reason)s.")


class ServerNotUsable(GyanException):
    message = _("gyan server not usable")
    code = 404


class Base64Exception(Invalid):
    msg_fmt = _("Invalid Base 64 file data")
