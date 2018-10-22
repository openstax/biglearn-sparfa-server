from uuid import uuid4

from pytest import raises

from sparfa_server.orm.sessions import transaction
from sparfa_server.orm.models import Ecosystem


class TestBiglearnSession(object):

    def test_upsert_values(self):
        with transaction() as session:
            # Not sent to Postgres at all
            assert session.upsert_values(Ecosystem, []) is None

            assert not session.query(Ecosystem).all()

        ecosystem_uuids = set((str(uuid4()), str(uuid4())))
        ecosystem_values = [{
            'uuid': ecosystem_uuid, 'sequence_number': 0
        } for ecosystem_uuid in ecosystem_uuids]

        with transaction() as session:
            with raises(TypeError):
                # ON CONFLICT DO UPDATE - Not valid without specifying (columns)
                session.upsert_values(Ecosystem, ecosystem_values,
                                      conflict_index_elements=[],
                                      conflict_update_columns=['sequence_number'])

            assert not session.query(Ecosystem).all()

        with transaction() as session:
            assert not session.query(Ecosystem).all()

            # ON CONFLICT (columns) DO NOTHING
            session.upsert_values(Ecosystem, ecosystem_values)

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            assert ecosystem.sequence_number == 0

        ecosystem_values[0]['sequence_number'] = 1
        ecosystem_values[1]['sequence_number'] = 2

        with transaction() as session:
            # ON CONFLICT DO NOTHING
            session.upsert_values(Ecosystem, ecosystem_values, conflict_index_elements=[])

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            assert ecosystem.sequence_number == 0

        with transaction() as session:
            # ON CONFLICT (columns) DO UPDATE
            session.upsert_values(Ecosystem, ecosystem_values,
                                  conflict_update_columns=['sequence_number'])

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            if ecosystem.uuid == ecosystem_values[0]['uuid']:
                assert ecosystem.sequence_number == 1
            else:
                assert ecosystem.sequence_number == 2

    def test_upsert_models(self):
        ecosystem_1 = Ecosystem(uuid=str(uuid4()), sequence_number=0)
        ecosystem_2 = Ecosystem(uuid=str(uuid4()), sequence_number=0)
        ecosystem_uuids = set((ecosystem_1.uuid, ecosystem_2.uuid))

        with transaction() as session:
            assert not session.query(Ecosystem).all()

            # ON CONFLICT (columns) DO NOTHING
            session.upsert_models(Ecosystem, [ecosystem_1, ecosystem_2])

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            assert ecosystem.sequence_number == 0

        ecosystem_1.sequence_number = 1
        ecosystem_2.sequence_number = 2

        with transaction() as session:
            # ON CONFLICT (columns) DO NOTHING
            session.upsert_models(Ecosystem, [ecosystem_1, ecosystem_2])

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            assert ecosystem.sequence_number == 0

        with transaction() as session:
            # ON CONFLICT (columns) DO UPDATE
            session.upsert_models(
                Ecosystem, [ecosystem_1, ecosystem_2], conflict_update_columns=['sequence_number']
            )

            ecosystems = session.query(Ecosystem).all()

        assert len(ecosystems) == 2
        for ecosystem in ecosystems:
            assert ecosystem.uuid in ecosystem_uuids
            assert ecosystem.sequence_number == (1 if ecosystem.uuid == ecosystem_1.uuid else 2)


def test_transaction():
    ecosystem = Ecosystem(uuid=str(uuid4()), sequence_number=0)

    with raises(RuntimeError):
        with transaction() as session:
            assert not session.query(Ecosystem).all()

            session.add(ecosystem)

            assert session.query(Ecosystem).all() == [ecosystem]

            raise RuntimeError('rollback test')

    with transaction() as session:
        assert not session.query(Ecosystem).all()

        session.add(ecosystem)

        assert session.query(Ecosystem).all() == [ecosystem]

    with transaction() as session:
        assert session.query(Ecosystem).all() == [ecosystem]
