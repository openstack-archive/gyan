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
SQLAlchemy models for ML INFRA service
"""

from oslo_db.sqlalchemy import models
from oslo_serialization import jsonutils as json
from oslo_utils import timeutils
import six.moves.urllib.parse as urlparse
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import sql
from sqlalchemy import String
from sqlalchemy import LargeBinary
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator, TEXT

import gyan.conf


def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')


def table_args():
    engine_name = urlparse.urlparse(gyan.conf.CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': gyan.conf.CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JsonEncodedType(TypeDecorator):
    """Abstract base type serialized as json-encoded string in db."""
    type = None
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            # Save default value according to current type to keep the
            # interface the consistent.
            value = self.type()
        elif not isinstance(value, self.type):
            raise TypeError("%s supposes to store %s objects, but %s given"
                            % (self.__class__.__name__,
                               self.type.__name__,
                               type(value).__name__))
        serialized_value = json.dump_as_bytes(value)
        return serialized_value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONEncodedDict(JsonEncodedType):
    """Represents dict serialized as json-encoded string in db."""
    type = dict


class JSONEncodedList(JsonEncodedType):
    """Represents list serialized as json-encoded string in db."""
    type = list


class GyanBase(models.TimestampMixin,
              models.ModelBase):

    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    def save(self, session=None):
        import gyan.db.sqlalchemy.api as db_api

        if session is None:
            session = db_api.get_session()

        super(GyanBase, self).save(session)


Base = declarative_base(cls=GyanBase)


class ML_Model(Base):
    """Represents a ML Model."""

    __tablename__ = 'ml_model'
    __table_args__ = (
        schema.UniqueConstraint('id', name='uniq_mlmodel0uuid'),
        table_args()
    )
    id = Column(Integer, primary_key=True)
    project_id = Column(String(255))
    user_id = Column(String(255))
    name = Column(String(255))
    status = Column(String(20))
    status_reason = Column(Text, nullable=True)
    host_id = Column(String(255), nullable=True)
    deployed = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    hints = Column(Text, nullable=True)
    ml_type = Column(String(255), nullable=True)
    ml_data = Column(LargeBinary(length=(2**32)-1), nullable=True)
    started_at = Column(DateTime)


class ComputeHost(Base):
    """Represents a compute host. """

    __tablename__ = 'compute_host'
    __table_args__ = (
        table_args()
    )
    id = Column(String(36), primary_key=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)


class Flavor(Base):
    """Represents a Flavor. """

    __tablename__ = 'flavor'
    __table_args__ = (
        table_args()
    )
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    python_version = Column(String(255), nullable=False)
    cpu = Column(String(255), nullable=False)
    driver = Column(String(255), nullable=False)
    memory = Column(String(255), nullable=False)
    disk = Column(String(255), nullable=False)
    additional_details = Column(Text, nullable=False)
