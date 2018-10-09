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

import datetime
import eventlet
import functools
import types

from docker import errors
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
import six

from gyan.common import consts
from gyan.common import exception
from gyan.common.i18n import _
from gyan.common import utils
from gyan.compute import api as gyan_compute
import gyan.conf
from gyan.ml_model import driver
from gyan import objects


CONF = gyan.conf.CONF
LOG = logging.getLogger(__name__)


class TensorflowDriver(driver.MLModelDriver):
    """Implementation of ml model drivers for Tensorflow."""  

    def __init__(self):
        super(driver.MLModelDriver, self).__init__()
        self._host = None

    def create(self, context, ml_model):
        return ml_model
        pass


    def delete(self, context, ml_model, force):
        pass

    def list(self, context):
        pass

    def show(self, context, ml_model):
        pass

    def train(self, context, ml_model):
        pass

    def deploy(self, context, ml_model):
        pass

    def undeploy(self, context, ml_model):
       pass