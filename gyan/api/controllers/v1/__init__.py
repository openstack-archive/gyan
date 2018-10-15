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

"""
Version 1 of the Gyan API

NOTE: IN PROGRESS AND NOT FULLY IMPLEMENTED.
"""

from oslo_log import log as logging
import pecan

from gyan.api.controllers import base as controllers_base
from gyan.api.controllers import link
from gyan.api.controllers.v1 import hosts as host_controller
from gyan.api.controllers.v1 import ml_models as ml_model_controller
from gyan.api.controllers import versions as ver
from gyan.api import http_error
from gyan.common.i18n import _

LOG = logging.getLogger(__name__)


BASE_VERSION = 1

MIN_VER_STR = '%s %s' % (ver.Version.service_string, ver.BASE_VER)

MAX_VER_STR = '%s %s' % (ver.Version.service_string, ver.CURRENT_MAX_VER)

MIN_VER = ver.Version({ver.Version.string: MIN_VER_STR},
                      MIN_VER_STR, MAX_VER_STR)
MAX_VER = ver.Version({ver.Version.string: MAX_VER_STR},
                      MIN_VER_STR, MAX_VER_STR)


class MediaType(controllers_base.APIBase):
    """A media type representation."""

    fields = (
        'base',
        'type',
    )


class V1(controllers_base.APIBase):
    """The representation of the version 1 of the API."""

    fields = (
        'id',
        'media_types',
        'links',
        'hosts',
        'ml_models'
    )

    @staticmethod
    def convert():
        v1 = V1()
        v1.id = "v1"
        v1.links = [link.make_link('self', pecan.request.host_url,
                                   'v1', '', bookmark=True),
                    link.make_link('describedby',
                                   'https://docs.openstack.org',
                                   'developer/gyan/dev',
                                   'api-spec-v1.html',
                                   bookmark=True, type='text/html')]
        v1.media_types = [MediaType(base='application/json',
                          type='application/vnd.openstack.gyan.v1+json')]
        v1.hosts = [link.make_link('self', pecan.request.host_url,
                                        'hosts', ''),
                         link.make_link('bookmark',
                                        pecan.request.host_url,
                                        'hosts', '',
                                        bookmark=True)]
        v1.ml_models = [link.make_link('self', pecan.request.host_url,
                                    'ml-models', ''),
                     link.make_link('bookmark',
                                    pecan.request.host_url,
                                    'ml-models', '',
                                    bookmark=True)]
        return v1


class Controller(controllers_base.Controller):
    """Version 1 API controller root."""

    hosts = host_controller.HostController()
    ml_models = ml_model_controller.MLModelController()

    @pecan.expose('json')
    def get(self):
        return V1.convert()

    def _check_version(self, version, headers=None):
        if headers is None:
            headers = {}
        # ensure that major version in the URL matches the header
        if version.major != BASE_VERSION:
            raise http_error.HTTPNotAcceptableAPIVersion(_(
                "Mutually exclusive versions requested. Version %(ver)s "
                "requested but not supported by this service. "
                "The supported version range is: "
                "[%(min)s, %(max)s].") % {'ver': version,
                                          'min': MIN_VER_STR,
                                          'max': MAX_VER_STR},
                headers=headers,
                max_version=str(MAX_VER),
                min_version=str(MIN_VER))
        # ensure the minor version is within the supported range
        if version < MIN_VER or version > MAX_VER:
            raise http_error.HTTPNotAcceptableAPIVersion(_(
                "Version %(ver)s was requested but the minor version is not "
                "supported by this service. The supported version range is: "
                "[%(min)s, %(max)s].") % {'ver': version, 'min': MIN_VER_STR,
                                          'max': MAX_VER_STR},
                headers=headers,
                max_version=str(MAX_VER),
                min_version=str(MIN_VER))

    @pecan.expose()
    def _route(self, args):
        version = ver.Version(
            pecan.request.headers, MIN_VER_STR, MAX_VER_STR)

        # Always set the basic version headers
        pecan.response.headers[ver.Version.min_string] = MIN_VER_STR
        pecan.response.headers[ver.Version.max_string] = MAX_VER_STR
        pecan.response.headers[ver.Version.string] = " ".join(
            [ver.Version.service_string, str(version)])
        pecan.response.headers["vary"] = ver.Version.string

        # assert that requested version is supported
        self._check_version(version, pecan.response.headers)
        pecan.request.version = version
        if pecan.request.body:
            msg = ("Processing request: url: %(url)s, %(method)s, "
                   "body: %(body)s" %
                   {'url': pecan.request.url,
                    'method': pecan.request.method,
                    'body': pecan.request.body})
            # LOG.debug(msg)
        LOG.debug(args)
        return super(Controller, self)._route(args)


__all__ = ('Controller',)
