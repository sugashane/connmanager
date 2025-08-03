#!/usr/bin/env python3


import argparse
import os
import sys
import logging

from connmanager.connection_service import ConnectionService
from connmanager.database_connection import DatabaseConnection
from connmanager.logging_utils import setup_logging

DB_PATH = os.path.expanduser(".cm.db")
logger = logging.getLogger(__name__)

def parse_args() -> argparse.ArgumentParser:
    """
    Parse command line arguments and return the parser.
    """
    parser = argparse.ArgumentParser(description="Manage connections.")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help='Add a new connection. Can be shortened to "a".')

    parser_connect = subparsers.add_parser(
        "connect", help='Connect to a host by alias or id. Can be shortened to "c".'
    )
    parser_connect.add_argument("alias_or_id", help="The alias or id of the connection to connect to.")

    parser_list = subparsers.add_parser(
        name="list",
        help='List all connections or all connections for a specified protocol. Can be shortened to "l".',
    )
    parser_list.add_argument(
        "protocol_or_tag",
        nargs="?",
        default=None,
        help="The protocol or tag to filter connections on (optional).",
    )

    parser_search = subparsers.add_parser(
        "search",
        help='Search all aliases and IP/hostnames in the table and return all matches. Can be shortened to "s".',
    )
    parser_search.add_argument("text", help="The text pattern to search for.")

    parser_delete = subparsers.add_parser(
        "delete", help='Delete connection by alias name. Can be shortened to "d".'
    )
    parser_delete.add_argument("alias_or_id", help="The alias or id of the connection to be deleted.")

    parser_edit = subparsers.add_parser(
        "edit", help='Edit a connection by alias. Can be shortened to "e".'
    )
    parser_edit.add_argument("alias_or_id", help="The alias or id of the connection to be edited.")

    parser_import = subparsers.add_parser(
        "import", help='Import connections from a JSON file. Can be shortened to "i".'
    )
    parser_import.add_argument("json_file", help="The JSON file to import connections from.")

    parser_export = subparsers.add_parser(
        "export", help='Export connections to a JSON file. Can be shortened to "x".'
    )
    parser_export.add_argument("json_file", help="The JSON file to export connections to.")

    return parser

def map_shortened_commands(args: list[str]) -> list[str]:
    """
    Map shortened command aliases to their full command names.
    """
    command_aliases = {
        "a": "add",
        "l": "list",
        "s": "search",
        "c": "connect",
        "d": "delete",
        "e": "edit",
        "i": "import",
        "x": "export",
    }
    if args and args[0] in command_aliases:
        args[0] = command_aliases[args[0]]
    return args

def main() -> None:
    """
    Main entry point for the CLI tool. Handles argument parsing, logging, and command dispatch.
    """
    if len(sys.argv) < 2:
        logger.error("No command provided. Use -h or --help for usage information.")
        sys.exit(1)

    mapped_args = map_shortened_commands(sys.argv[1:])
    parser = parse_args()
    args = parser.parse_args(mapped_args)

    # Set up logging level
    setup_logging(debug=getattr(args, "debug", False))

    db = DatabaseConnection(DB_PATH)
    manager = ConnectionService(db)

    if args.command.casefold() == "add":
        manager.add_connection()
    elif args.command == "edit":
        manager.edit_connection(args.alias_or_id)
    elif args.command.casefold() == "delete":
        manager.delete_connection(args.alias_or_id)
    elif args.command.casefold() == "list":
        manager.get_connections_summary(args.protocol_or_tag)
    elif args.command.casefold() == "search":
        manager.search_connections(args.text)
    elif args.command.casefold() == "connect":
        manager.connect_to_alias_or_id(args.alias_or_id)
    elif args.command == "import":
        manager.import_connections(args.json_file)
    elif args.command == "export":
        manager.export_connections(args.json_file)

if __name__ == "__main__":
    main()