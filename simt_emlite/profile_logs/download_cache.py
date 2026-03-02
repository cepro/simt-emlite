"""Cache for resumable profile log downloads.

Saves completed chunks to a JSON file so that a failed download can
be resumed on the next run without re-downloading already-fetched chunks.
"""

import datetime
import json
import tempfile
import getpass
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


@dataclass
class CachedLog1Record:
    """Duck-type compatible with EmopProfileLog1Record for create_smip_readings()."""

    import_a: int
    import_b: int


@dataclass
class CachedLog2Record:
    """Duck-type compatible with EmopProfileLog2Record for create_smip_readings()."""

    active_export_a: int
    active_export_b: int = 0  # 0 for single-element meters


class DownloadCache:
    """Manages a per-serial per-date cache file for partial profile downloads.

    Cache file is stored in the system temporary directory to avoid Syncthing churn.
    """

    def __init__(self, output_dir: str, serial: str, date: datetime.date) -> None:
        """Initialize cache.

        Args:
            output_dir: Ignored (kept for compatibility)
            serial: Meter serial number
            date: Download date
        """
        filename = f"{serial}-{date.strftime('%Y%m%d')}.download_cache.json"

        # Use system temp directory, per-user subfolder to avoid Syncthing churn
        # and multi-user permission issues
        tmp_base = Path(tempfile.gettempdir())
        user_cache_dir = tmp_base / f"simt-emlite-cache-{getpass.getuser()}"
        user_cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.cache_path = user_cache_dir / filename
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path) as f:
                    data = json.load(f)
                logger.info(
                    "Loaded download cache",
                    cache_file=str(self.cache_path),
                    log1_chunks=len(data.get("log1_chunks_done", [])),
                    log2_chunks=len(data.get("log2_chunks_done", [])),
                )
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Failed to load cache file, starting fresh",
                    error=str(e),
                )
        return {
            "log1_chunks_done": [],
            "log1_records": {},
            "log2_chunks_done": [],
            "log2_records": {},
        }

    def _save(self) -> None:
        with open(self.cache_path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def has_cached_data(self) -> bool:
        return bool(
            self._data.get("log1_chunks_done") or self._data.get("log2_chunks_done")
        )

    def has_log1_chunk(self, chunk_start_iso: str) -> bool:
        return chunk_start_iso in self._data["log1_chunks_done"]

    def has_log2_chunk(self, chunk_start_iso: str) -> bool:
        return chunk_start_iso in self._data["log2_chunks_done"]

    def save_log1_chunk(
        self, chunk_start_iso: str, records: Dict[str, Dict[str, int]]
    ) -> None:
        self._data["log1_chunks_done"].append(chunk_start_iso)
        self._data["log1_records"].update(records)
        self._save()

    def save_log2_chunk(
        self, chunk_start_iso: str, records: Dict[str, Dict[str, int]]
    ) -> None:
        self._data["log2_chunks_done"].append(chunk_start_iso)
        self._data["log2_records"].update(records)
        self._save()

    def get_log1_records(self) -> Dict[datetime.datetime, CachedLog1Record]:
        result: Dict[datetime.datetime, CachedLog1Record] = {}
        for ts_str, data in self._data["log1_records"].items():
            ts = datetime.datetime.fromisoformat(ts_str)
            result[ts] = CachedLog1Record(
                import_a=data["import_a"],
                import_b=data["import_b"],
            )
        return result

    def get_log2_records(self) -> Dict[datetime.datetime, CachedLog2Record]:
        result: Dict[datetime.datetime, CachedLog2Record] = {}
        for ts_str, data in self._data["log2_records"].items():
            ts = datetime.datetime.fromisoformat(ts_str)
            result[ts] = CachedLog2Record(
                active_export_a=data["active_export_a"],
                active_export_b=data.get("active_export_b", 0),
            )
        return result

    def delete(self) -> None:
        if self.cache_path.exists():
            self.cache_path.unlink()
            logger.info("Deleted download cache", cache_file=str(self.cache_path))
