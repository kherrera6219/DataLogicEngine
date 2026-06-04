"""Compatibility entrypoint for the simulation database creation script."""

from scripts.create_simulation_database import *  # noqa: F401,F403
from scripts.create_simulation_database import main


if __name__ == "__main__":
    main()
