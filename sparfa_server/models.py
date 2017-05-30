from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

metadata = sa.MetaData()

ecosystems = sa.Table('ecosystems', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('uuid', UUID, nullable=False, unique=True)
                      )

books = sa.Table('books', metadata,
                 sa.Column('id', sa.Integer, primary_key=True),
                 sa.Column('uuid', UUID, nullable=False, unique=True),
                 sa.Column('ecosystem_id', None, sa.ForeignKey('ecosystems.id'))
                 )

chapters = sa.Table('chapters', metadata,
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('uuid', UUID, unique=True),
                    sa.Column('book_id', None, sa.ForeignKey('books.id')),
                    sa.Column('container_cnx_identity', sa.String(50)),
                    sa.Column('container_parent_uuid', UUID)
                    )
