from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from .exceptions import UKGNotFoundError
from .utils import package_data_path


@dataclass
class KARegistry:
    df: pd.DataFrame

    @classmethod
    def load_default(cls) -> "KARegistry":
        path = package_data_path("ka_registry.xlsx")
        if not path.exists():
            raise UKGNotFoundError(f"Missing KA registry at {path}")
        df = pd.read_excel(path)
        return cls(df)

    def by_id(self, ka_id: str) -> Dict[str, Any]:
        row = self.df[self.df["KA_ID"] == ka_id]
        if row.empty:
            raise UKGNotFoundError(f"KA not found: {ka_id}")
        return row.iloc[0].to_dict()


@dataclass
class Axis2Registry:
    df: pd.DataFrame

    @classmethod
    def load_default(cls) -> "Axis2Registry":
        path = package_data_path("axis2.xlsx")
        if not path.exists():
            raise UKGNotFoundError(f"Missing AXIS2 dataset at {path}")
        df = pd.read_excel(path)
        return cls(df)


@dataclass
class PLRegistry:
    df: pd.DataFrame

    @classmethod
    def load_default(cls) -> "PLRegistry":
        path = package_data_path("pl1_107.xlsx")
        if not path.exists():
            raise UKGNotFoundError(f"Missing PL1-107 dataset at {path}")
        df = pd.read_excel(path)
        return cls(df)
