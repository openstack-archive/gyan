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

from heatclient import client as heatclient

from gyan.common import exception
from gyan.common import keystone
import gyan.conf


class OpenStackClients(object):
    """Convenience class to create and cache client instances."""

    def __init__(self, context):
        self.context = context
        self._keystone = None
        self._heat = None

    def url_for(self, **kwargs):
        return self.keystone().session.get_endpoint(**kwargs)

    def gyan_url(self):
        endpoint_type = self._get_client_option('gyan', 'endpoint_type')
        region_name = self._get_client_option('gyan', 'region_name')
        return self.url_for(service_type='ml-infra',
                            interface=endpoint_type,
                            region_name=region_name)

    @property
    def auth_token(self):
        return self.context.auth_token or self.keystone().auth_token

    def keystone(self):
        if self._keystone:
            return self._keystone

        self._keystone = keystone.KeystoneClientV3(self.context)
        return self._keystone

    def _get_client_option(self, client, option):
        return getattr(getattr(gyan.conf.CONF, '%s_client' % client), option)

    @exception.wrap_keystone_exception
    def heat(self):
        if self._heat:
            return self._heat

        heatclient_version = self._get_client_option('heat', 'api_version')
        session = self.keystone().session
        self._heat = heatclient.Client(heatclient_version,
                                           session=session)

        return self._heat