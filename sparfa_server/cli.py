import argparse
import logging
import sys

from sparfa_server.api import fetch_pending_ecosystems, fetch_course_uuids
from sparfa_server.loaders import load_ecosystem, load_course, run


def parse_args(arguments):
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='commands', dest='command')

    load_parser = subparsers.add_parser('load',
                                        help='Import an ecosystem, course, or run loaders')
    ecosystem_group = load_parser.add_mutually_exclusive_group()

    ecosystem_group.add_argument('-e', '--ecosystem_uuid',
                                 action='store',
                                 dest='ecosystem_uuid',
                                 help='The ecosystem uuid to import.')
    ecosystem_group.add_argument('-c', '--course_uuid',
                                 action='store',
                                 dest='course_uuid',
                                 help='The course uuid to import')
    ecosystem_group.add_argument('-a', '--all',
                                 action='store_true',
                                 dest='all',
                                 help='Specifies if all ecosystems and courses'
                                      'should be imported')
    ecosystem_group.add_argument('-r', '--run',
                                 action='store_true',
                                 dest='run',
                                 help='Starts the loading process for '
                                      'Ecosystems and Courses')

    load_parser.add_argument('-d', '--delay',
                             action='store',
                             dest='delay',
                             type=int,
                             default=600,
                             help='The delay time in seconds that the '
                                  'loaders will run.')

    return parser.parse_args(arguments)


def main():
    args = parse_args(sys.argv[1:])
    logging.basicConfig(level=logging.INFO)

    if args.command == 'load':
        if args.ecosystem_uuid:
            load_ecosystem(args.ecosystem_uuid)
        elif args.course_uuid:
            load_course(args.course_uuid)
        elif args.all:
            ecosystem_uuids = fetch_pending_ecosystems()
            api_course_uuids = fetch_course_uuids()
            for eco_uuid in ecosystem_uuids:
                load_ecosystem(eco_uuid)
            for course_uuid in api_course_uuids:
                load_course(course_uuid)
        elif args.run:
            try:
                run(args.delay)
            except (KeyboardInterrupt, SystemExit):
                pass


if __name__ == '__main__':
    main()
