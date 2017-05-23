import uuid

from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

metadata = sa.MetaData()

ecosystems = sa.Table('ecosystems', metadata,
                 sa.Column('id', sa.Integer),
                 sa.Column('uuid', UUID)
                 )

books = sa.Table('books', metadata,
                 sa.Column('id', sa.Integer),
                 sa.Column('uuid', UUID),
                 sa.Column('cnx_identity'),
                 sa.Column('ecosystem_id', None, sa.ForeignKey('ecosystems.id'))
                 )

chapters = sa.Table('chapters', metadata,
                         sa.Column('id', sa.Integer),
                         sa.Column('uuid', UUID),
                         sa.Column('book_id', None, sa.ForeignKey('books.id'))
                         )
