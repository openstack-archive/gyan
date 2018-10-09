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


"""create_table_gyan_service

Revision ID: a9a92eebd9a8
Revises:
Create Date: 2018

"""

# revision identifiers, used by Alembic.
revision = 'a9a92eebd9a8'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'ml_model',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('host_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('status_reason', sa.Text, nullable=True),
        sa.Column('url', sa.Text, nullable=True),
        sa.Column('hints', sa.Text, nullable=True),
        sa.Column('deployed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['host_id'], ['host.id'])
    )
    op.create_table(
        'host',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('ml_stack', sa.String(length=255), nullable=True),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('mem_available', sa.String(length=255), nullable=True),
        sa.Column('cpus', sa.String(length=255), nullable=True),
        sa.Column('architecture', sa.String(length=255), nullable=True),
        sa.Column('os', sa.String(length=255), nullable=True),
        sa.Column('kernel_version', sa.String(length=255), nullable=True),
        sa.Column('disk_total', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
