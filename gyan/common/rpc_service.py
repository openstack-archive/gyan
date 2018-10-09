#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Common RPC service and API tools for Gyan."""

import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher
from oslo_service import service
from oslo_utils import importutils

from gyan.common import context
from gyan.common import profiler
from gyan.common import rpc
import gyan.conf
from gyan.objects import base as objects_base
from gyan.servicegroup import gyan_service_periodic as servicegroup

osprofiler = importutils.try_import("osprofiler.profiler")

CONF = gyan.conf.CONF


def _init_serializer():
    serializer = rpc.RequestContextSerializer(
        objects_base.GyanObjectSerializer())
    if osprofiler:
        serializer = rpc.ProfilerRequestContextSerializer(serializer)
    else:
        serializer = rpc.RequestContextSerializer(serializer)
    return serializer


class Service(service.Service):

    def __init__(self, topic, server, endpoints, binary):
        super(Service, self).__init__()
        serializer = _init_serializer()
        transport = messaging.get_rpc_transport(CONF)
        access_policy = dispatcher.DefaultRPCAccessPolicy
        # TODO(asalkeld) add support for version='x.y'
        target = messaging.Target(topic=topic, server=server)
        self.endpoints = endpoints
        self._server = messaging.get_rpc_server(transport, target, endpoints,
                                                executor='eventlet',
                                                serializer=serializer,
                                                access_policy=access_policy)
        self.binary = binary
        profiler.setup(binary, CONF.host)

    def start(self):
        servicegroup.setup(CONF, self.binary, self.tg)
        for endpoint in self.endpoints:
            if hasattr(endpoint, 'init_containers'):
                endpoint.init_containers(
                    context.get_admin_context(all_projects=True))
            self.tg.add_dynamic_timer(
                endpoint.run_periodic_tasks,
                periodic_interval_max=CONF.periodic_interval_max,
                context=context.get_admin_context(all_projects=True)
            )
        self._server.start()

    def stop(self):
        if self._server:
            self._server.stop()
            self._server.wait()
        super(Service, self).stop()

    @classmethod
    def create(cls, topic, server, handlers, binary):
        service_obj = cls(topic, server, handlers, binary)
        return service_obj


class API(object):
    def __init__(self, context=None, topic=None, server=None,
                 timeout=None):
        serializer = _init_serializer()
        self._context = context
        if topic is None:
            topic = ''
        target = messaging.Target(topic=topic, server=server)
        self._client = rpc.get_client(target,
                                      serializer=serializer,
                                      timeout=timeout)

    def _call(self, server, method, *args, **kwargs):
        cctxt = self._client.prepare(server=server)
        return cctxt.call(self._context, method, *args, **kwargs)

    def _cast(self, server, method, *args, **kwargs):
        cctxt = self._client.prepare(server=server)
        return cctxt.cast(self._context, method, *args, **kwargs)

    def echo(self, message):
        self._cast('echo', message=message)
