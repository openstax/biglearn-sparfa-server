
from sparfa_server.api import blapi


def main():
    ecosystem_uuids = blapi.fetch_ecosystem_metadatas()
    print(ecosystem_uuids)


if __name__ == '__main__':
    main()
