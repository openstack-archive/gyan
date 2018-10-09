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

import sys

from oslo_log import log as logging
from oslo_utils import importutils
from oslo_utils import units

from gyan.common.i18n import _
import gyan.conf
from gyan import objects

LOG = logging.getLogger(__name__)
CONF = gyan.conf.CONF


def load_ml_model_driver(ml_model_driver=None):
    """Load a ml_model driver module.

    Load the ml_model driver module specified by the ml_model_driver
    configuration option or, if supplied, the driver name supplied as an
    argument.
    :param ml_model_driver: a ml_model driver name to override the config opt
    :returns: a MLModelDriver instance
    """
    if not ml_model_driver:
        ml_model_driver = CONF.ml_model_driver
        if not ml_model_driver:
            LOG.error("ML Model driver option required, "
                      "but not specified")
            sys.exit(1)

    LOG.info("Loading ML Model driver '%s'", ml_model_driver)
    try:
        if not ml_model_driver.startswith('gyan.'):
            ml_model_driver = 'gyan.ml_model.%s' % ml_model_driver
        driver = importutils.import_object(ml_model_driver)
        if not isinstance(driver, MLModelDriver):
            raise Exception(_('Expected driver of type: %s') %
                            str(MLModelDriver))

        return driver
    except ImportError:
        LOG.exception("Unable to load the ml model driver")
        sys.exit(1)


class MLModelDriver(object):
    """Base class for ml model drivers."""

    def create(self, context, ml_model, **kwargs):
        """Create a container."""
        raise NotImplementedError()

    def delete(self, context, ml_model, force):
        """Delete a ML Model."""
        raise NotImplementedError()

    def list(self, context):
        """List all ML Models."""
        raise NotImplementedError()

    def show(self, context, ml_model):
        """Show the details of a ML Models."""
        raise NotImplementedError()

    def train(self, context, ml_model):
        """Train a ML Model."""
        raise NotImplementedError()

    def deploy(self, context, ml_model):
        """Deploy a ML Model."""
        raise NotImplementedError()

    def undeploy(self, context, ml_model):
        """Undeploy a ML Model."""
        raise NotImplementedError()

    def get_available_hosts(self):
        pass

    def get_available_resources(self, host):
        pass

    def node_is_available(self, hostname):
        """Return whether this compute service manages a particular host."""
        if hostname in self.get_available_hosts():
            return True
        return False