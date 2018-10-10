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

###
# This code is taken from nova. Goal is minimal modification.
###

from oslo_log import log as logging
from oslo_utils import importutils
import webob.dec

from gyan.common import context
import gyan.conf

profiler = importutils.try_import("osprofiler.profiler")
profiler_initializer = importutils.try_import("osprofiler.initializer")
profiler_web = importutils.try_import("osprofiler.web")


CONF = gyan.conf.CONF

LOG = logging.getLogger(__name__)


class WsgiMiddleware(object):

    def __init__(self, application, **kwargs):
        self.application = application

    @classmethod
    def factory(cls, global_conf, **local_conf):
        if profiler_web:
            return profiler_web.WsgiMiddleware.factory(global_conf,
                                                       **local_conf)

        def filter_(app):
            return cls(app, **local_conf)

        return filter_

    @webob.dec.wsgify
    def __call__(self, request):
        return request.get_response(self.application)


def setup(binary, host):
    if profiler_initializer and CONF.profiler.enabled:
        profiler_initializer.init_from_conf(
            conf=CONF,
            context=context.get_admin_context().to_dict(),
            project="gyan",
            service=binary,
            host=host)
        LOG.info('OSProfiler is enabled.')


def trace_cls(name, **kwargs):
    """Wrap the OSprofiler trace_cls.

    Wrap the OSprofiler trace_cls decorator so that it will not try to
    patch the class unless OSprofiler is present.

    :param name: The name of action. For example, wsgi, rpc, db, ...
    :param kwargs: Any other keyword args used by profiler.trace_cls
    """

    def decorator(cls):
        if profiler and 'profiler' in CONF:
            trace_decorator = profiler.trace_cls(name, kwargs)
            return trace_decorator(cls)
        return cls

    return decorator


def trace(name, **kwargs):
    """Wrap the OSprofiler trace.

    Wrap the OSprofiler trace decorator so that it will not try to
    patch the functions unless OSprofiler is present.

    :param name: The name of action. For example, wsgi, rpc, db, ...
    :param kwargs: Any other keyword args used by profiler.trace
    """

    def decorator(f):
        if profiler and 'profiler' in CONF:
            trace_decorator = profiler.trace(name, kwargs)
            return trace_decorator(f)
        return f

    return decorator
