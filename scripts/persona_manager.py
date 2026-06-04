"""CLI utility for managing Quad Persona profiles."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from typing import Any, Dict, Optional, Tuple

from core.persona.quad.persona_loader import PersonaLoader
from core.persona.quad.models import PersonaProfile

PERSONA_TYPE_TO_AXIS = {
    "knowledge": 8,
    "sector": 9,
    "regulatory": 10,
    "compliance": 11,
}


def load_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_storage_file(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"personas": [], "domain_mappings": {}}, handle, indent=2)


def find_persona(loader: PersonaLoader, persona_id: str) -> Optional[Tuple[str, PersonaProfile]]:
    for persona_type, personas in loader.personas_by_type.items():
        if persona_id in personas:
            return persona_type, personas[persona_id]
    return None


def list_personas(loader: PersonaLoader, persona_type: Optional[str], as_json: bool) -> int:
    personas = []
    if persona_type:
        personas = list(loader.get_all_personas_by_type(persona_type).values())
    else:
        for group in loader.personas_by_type.values():
            personas.extend(group.values())

    if as_json:
        print(json.dumps([persona.to_dict() for persona in personas], indent=2))
    else:
        for persona in personas:
            print(f"{persona.persona_id} | {persona.persona_type} | {persona.name}")
    return 0


def add_persona(loader: PersonaLoader, args: argparse.Namespace) -> int:
    persona_type = args.persona_type
    if persona_type not in PERSONA_TYPE_TO_AXIS:
        print(f"Invalid persona type: {persona_type}")
        return 1

    axis_number = args.axis_number or PERSONA_TYPE_TO_AXIS[persona_type]
    persona_id = args.persona_id or str(uuid.uuid4())
    profile = PersonaProfile(
        persona_id=persona_id,
        axis_number=axis_number,
        persona_type=persona_type,
        name=args.name,
        description=args.description,
    )

    if args.components_file:
        profile.components = load_json_file(args.components_file)
    if args.metadata_file:
        profile.metadata = load_json_file(args.metadata_file)

    if args.octopus_connections:
        profile.octopus_connections = args.octopus_connections
    if args.spiderweb_connections:
        profile.spiderweb_connections = args.spiderweb_connections

    loader.add_persona(profile)
    loader.save_personas()
    print(f"Added persona {persona_id} ({persona_type})")
    return 0


def update_persona(loader: PersonaLoader, args: argparse.Namespace) -> int:
    persona_id = args.persona_id
    if not persona_id:
        print("--persona-id is required for update")
        return 1

    persona_type = args.persona_type
    profile = None
    if persona_type:
        profile = loader.get_persona(persona_type, persona_id)
    else:
        found = find_persona(loader, persona_id)
        if found:
            persona_type, profile = found

    if not profile:
        print(f"Persona not found: {persona_id}")
        return 1

    if args.name:
        profile.name = args.name
    if args.description is not None:
        profile.description = args.description
    if args.components_file:
        profile.components = load_json_file(args.components_file)
    if args.metadata_file:
        profile.metadata = load_json_file(args.metadata_file)
    if args.octopus_connections is not None:
        profile.octopus_connections = args.octopus_connections
    if args.spiderweb_connections is not None:
        profile.spiderweb_connections = args.spiderweb_connections

    loader.save_personas()
    print(f"Updated persona {persona_id}")
    return 0


def delete_persona(loader: PersonaLoader, args: argparse.Namespace) -> int:
    persona_id = args.persona_id
    if not persona_id:
        print("--persona-id is required for delete")
        return 1

    persona_type = args.persona_type
    if persona_type:
        if loader.delete_persona(persona_type, persona_id):
            loader.save_personas()
            print(f"Deleted persona {persona_id}")
            return 0
        print(f"Persona not found: {persona_id}")
        return 1

    found = find_persona(loader, persona_id)
    if not found:
        print(f"Persona not found: {persona_id}")
        return 1

    persona_type, _ = found
    loader.delete_persona(persona_type, persona_id)
    loader.save_personas()
    print(f"Deleted persona {persona_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Quad Persona profiles.")
    parser.add_argument(
        "--storage-path",
        default=os.environ.get("PERSONA_STORAGE_PATH", os.path.join("data", "personas_db.json")),
        help="Path to personas JSON storage",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List personas")
    list_parser.add_argument("--persona-type", choices=PERSONA_TYPE_TO_AXIS.keys())
    list_parser.add_argument("--json", action="store_true", help="Output JSON")

    add_parser = subparsers.add_parser("add", help="Add a persona")
    add_parser.add_argument("--persona-type", required=True, choices=PERSONA_TYPE_TO_AXIS.keys())
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--description", default="")
    add_parser.add_argument("--persona-id")
    add_parser.add_argument("--axis-number", type=int)
    add_parser.add_argument("--components-file")
    add_parser.add_argument("--metadata-file")
    add_parser.add_argument("--octopus-connections", nargs="*")
    add_parser.add_argument("--spiderweb-connections", nargs="*")

    update_parser = subparsers.add_parser("update", help="Update a persona")
    update_parser.add_argument("--persona-id", required=True)
    update_parser.add_argument("--persona-type", choices=PERSONA_TYPE_TO_AXIS.keys())
    update_parser.add_argument("--name")
    update_parser.add_argument("--description")
    update_parser.add_argument("--components-file")
    update_parser.add_argument("--metadata-file")
    update_parser.add_argument("--octopus-connections", nargs="*")
    update_parser.add_argument("--spiderweb-connections", nargs="*")

    delete_parser = subparsers.add_parser("delete", help="Delete a persona")
    delete_parser.add_argument("--persona-id", required=True)
    delete_parser.add_argument("--persona-type", choices=PERSONA_TYPE_TO_AXIS.keys())

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ensure_storage_file(args.storage_path)
    loader = PersonaLoader(storage_path=args.storage_path)

    if args.command == "list":
        return list_personas(loader, args.persona_type, args.json)
    if args.command == "add":
        return add_persona(loader, args)
    if args.command == "update":
        return update_persona(loader, args)
    if args.command == "delete":
        return delete_persona(loader, args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
