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
import png
import os
import tempfile
import numpy as np

import tensorflow as tf

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

    def _load(self, session, path):
        saver = tf.train.import_meta_graph(path + '/model.meta')
        saver.restore(session, tf.train.latest_checkpoint(path))
        return tf.get_default_graph()

    def predict(self, context, ml_model_path, data):
        session = tf.Session()
        graph = self._load(session, ml_model_path)
        img_file, img_path = tempfile.mkstemp()
        with os.fdopen(img_file, 'wb') as f:
            f.write(data)
        png_data = png.Reader(img_path)
        img = np.array(list(png_data.read()[2]))
        img = img.reshape(1, 784)
        tensor = graph.get_tensor_by_name('x:0')
        prediction = graph.get_tensor_by_name('classification:0')
        return {"data": session.run(prediction, feed_dict={tensor:img})[0]}


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