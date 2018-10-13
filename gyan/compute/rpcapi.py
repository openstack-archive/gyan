#    Copyright 2016 IBM Corp.
#
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

import functools

from gyan.api import servicegroup
from gyan.common import exception
from gyan.common import profiler
from gyan.common import rpc_service
import gyan.conf
from gyan import objects


def check_ml_model_host(func):
    """Verify the state of ML Model host"""
    @functools.wraps(func)
    def wrap(self, context, ml_model, *args, **kwargs):
        return func(self, context, ml_model, *args, **kwargs)
    return wrap


class API(rpc_service.API):
    """Client side of the ml_model compute rpc API.

    API version history:

        * 1.0 - Initial version.
    """

    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            gyan.conf.CONF.import_opt(
                'topic', 'gyan.conf.compute', group='compute')

        super(API, self).__init__(
            context, gyan.conf.CONF.compute.topic, transport)

    def ml_model_create(self, context, host, ml_model):
        self._cast(host, 'ml_model_create', 
                   ml_model=ml_model)

    @check_ml_model_host
    def ml_model_delete(self, context, ml_model, force):
        return self._cast(ml_model.host, 'ml_model_delete',
                          ml_model=ml_model, force=force)

    @check_ml_model_host
    def ml_model_show(self, context, ml_model):
        return self._call(ml_model.host, 'ml_model_show',
                          ml_model=ml_model)


    @check_ml_model_host
    def ml_model_update(self, context, ml_model, patch):
        return self._call(ml_model.host, 'ml_model_update',
                          ml_model=ml_model, patch=patch)
