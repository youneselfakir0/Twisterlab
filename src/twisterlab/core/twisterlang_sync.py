#!/usr/bin/env python3
"""
TwisterLang Sync - Vocabulary Synchronization Module
Ensures all agents share the same TwisterLang vocabulary version
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List

from .twisterlang_decoder import TwisterLangDecoder
from .twisterlang_encoder import TwisterLangEncoder


class TwisterLangSync:
    def __init__(
        self,
        vocab_file: str = "twisterlang_vocab.json",
        sync_log_file: str = "twisterlang_sync.log",
    ):
        self.vocab_file = Path(vocab_file)
        self.sync_log_file = Path(sync_log_file)
        self.encoder = TwisterLangEncoder(vocab_file)
        self.decoder = TwisterLangDecoder(vocab_file)
        self.sync_history: List[Dict] = []
        self.load_sync_history()

    def load_sync_history(self) -> None:
        """Load synchronization history"""
        if self.sync_log_file.exists():
            try:
                with open(self.sync_log_file, "r", encoding="utf-8") as f:
                    self.sync_history = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load sync history: {e}")
                self.sync_history = []

    def save_sync_history(self) -> None:
        """Save synchronization history"""
        with open(self.sync_log_file, "w", encoding="utf-8") as f:
            json.dump(self.sync_history, f, indent=2, ensure_ascii=False)

    def get_vocab_checksum(self) -> str:
        """Calculate checksum of current vocabulary"""
        if not self.vocab_file.exists():
            return ""

        with open(self.vocab_file, "rb") as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()

    def get_vocab_metadata(self) -> Dict:
        """Get vocabulary metadata for comparison"""
        checksum = self.get_vocab_checksum()
        vocab_size = len(self.encoder.vocab) if hasattr(self.encoder, "vocab") else 0

        # Get version and last update
        version = "1.0"
        last_update = int(time.time())

        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version = data.get("version", "1.0")
                    last_update = data.get("last_updated", last_update)
            except Exception:
                pass

        return {
            "checksum": checksum,
            "version": version,
            "last_update": last_update,
            "vocab_size": vocab_size,
            "file_size": self.vocab_file.stat().st_size if self.vocab_file.exists() else 0,
        }

    def compare_vocabularies(self, remote_metadata: Dict) -> Dict:
        """
        Compare local vocabulary with remote metadata
        Returns: {'action': 'push'|'pull'|'sync', 'reason': str, 'details': dict}
        """
        local_meta = self.get_vocab_metadata()

        if local_meta["checksum"] == remote_metadata.get("checksum"):
            return {
                "action": "sync",
                "status": "ok",
                "needs_sync": False,
                "reason": "vocabularies_are_identical",
                "details": {"checksum": local_meta["checksum"]},
            }

        local_time = local_meta["last_update"]
        remote_time = remote_metadata.get("last_update", 0)

        if local_time > remote_time:
            return {
                "action": "push",
                "status": "push",
                "needs_sync": True,
                "reason": "local_is_newer",
                "details": {
                    "local_time": local_time,
                    "remote_time": remote_time,
                    "time_diff": local_time - remote_time,
                },
            }
        elif remote_time > local_time:
            return {
                "action": "pull",
                "status": "pull",
                "needs_sync": True,
                "reason": "remote_is_newer",
                "details": {
                    "local_time": local_time,
                    "remote_time": remote_time,
                    "time_diff": remote_time - local_time,
                },
            }
        else:
            # Same timestamp but different checksum - conflict resolution
            if local_meta["vocab_size"] > remote_metadata.get("vocab_size", 0):
                return {
                    "action": "push",
                    "status": "push",
                    "needs_sync": True,
                    "reason": "local_has_more_entries",
                    "details": {
                        "local_size": local_meta["vocab_size"],
                        "remote_size": remote_metadata.get("vocab_size", 0),
                    },
                }
            else:
                return {
                    "action": "pull",
                    "status": "pull",
                    "needs_sync": True,
                    "reason": "remote_has_more_entries_or_conflict_resolution",
                    "details": {
                        "local_size": local_meta["vocab_size"],
                        "remote_size": remote_metadata.get("vocab_size", 0),
                    },
                }

    def push_vocabulary(self, target_agent: str) -> Dict:
        """
        Push local vocabulary to target agent
        Returns: {'success': bool, 'message': str, 'details': dict}
        """
        try:
            # In a real implementation, this would send the vocab file
            # For now, simulate the operation
            metadata = self.get_vocab_metadata()

            sync_record = {
                "timestamp": int(time.time()),
                "action": "push",
                "target_agent": target_agent,
                "metadata": metadata,
                "status": "simulated_success",
            }

            self.sync_history.append(sync_record)
            self.save_sync_history()

            return {
                "success": True,
                "message": f"Vocabulary pushed to {target_agent}",
                "details": {
                    "target": target_agent,
                    "checksum": metadata["checksum"],
                    "vocab_size": metadata["vocab_size"],
                },
            }

        except Exception as e:
            error_record = {
                "timestamp": int(time.time()),
                "action": "push",
                "target_agent": target_agent,
                "status": "error",
                "error": str(e),
            }
            self.sync_history.append(error_record)
            self.save_sync_history()

            return {
                "success": False,
                "message": f"Push failed: {str(e)}",
                "details": {"error": str(e)},
            }

    def pull_vocabulary(self, source_agent: str, remote_vocab_data: Dict) -> Dict:
        """
        Pull and merge vocabulary from source agent
        Returns: {'success': bool, 'message': str, 'details': dict}
        """
        try:
            # Validate remote data
            if not isinstance(remote_vocab_data, dict):
                raise ValueError("Invalid vocabulary data format")

            required_keys = ["version", "last_updated", "vocabulary"]
            if not all(key in remote_vocab_data for key in required_keys):
                raise ValueError("Missing required vocabulary keys")

            # Backup current vocab
            backup_file = self.vocab_file.with_suffix(".backup")
            if self.vocab_file.exists():
                import shutil

                shutil.copy2(self.vocab_file, backup_file)

            # Merge vocabularies
            merged_vocab = self._merge_vocabularies(remote_vocab_data)

            # Save merged vocabulary
            with open(self.vocab_file, "w", encoding="utf-8") as f:
                json.dump(merged_vocab, f, indent=2, ensure_ascii=False)

            # Reload encoder/decoder
            self.encoder = TwisterLangEncoder(str(self.vocab_file))
            self.decoder = TwisterLangDecoder(str(self.vocab_file))

            sync_record = {
                "timestamp": int(time.time()),
                "action": "pull",
                "source_agent": source_agent,
                "status": "success",
                "merged_entries": len(merged_vocab.get("vocabulary", {})),
            }

            self.sync_history.append(sync_record)
            self.save_sync_history()

            return {
                "success": True,
                "message": f"Vocabulary pulled from {source_agent}",
                "details": {
                    "source": source_agent,
                    "new_entries": len(merged_vocab.get("vocabulary", {})),
                    "backup_created": str(backup_file),
                },
            }

        except Exception as e:
            # Restore backup if it exists
            backup_file = self.vocab_file.with_suffix(".backup")
            if backup_file.exists():
                import shutil

                shutil.copy2(backup_file, self.vocab_file)

            error_record = {
                "timestamp": int(time.time()),
                "action": "pull",
                "source_agent": source_agent,
                "status": "error",
                "error": str(e),
            }
            self.sync_history.append(error_record)
            self.save_sync_history()

            return {
                "success": False,
                "message": f"Pull failed: {str(e)}",
                "details": {"error": str(e)},
            }

    def _merge_vocabularies(self, remote_vocab: Dict) -> Dict:
        """Merge remote vocabulary with local one"""
        local_vocab = {}
        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                    local_vocab = local_data.get("vocabulary", {})
            except Exception:
                pass

        remote_vocab_entries = remote_vocab.get("vocabulary", {})

        # Merge strategy: remote takes precedence for conflicts
        merged_vocab = local_vocab.copy()
        merged_vocab.update(remote_vocab_entries)

        # Update metadata
        current_time = int(time.time())
        merged_data = {
            "version": remote_vocab.get("version", "1.0"),
            "last_updated": current_time,
            "vocabulary": merged_vocab,
        }

        return merged_data

    def get_sync_status(self) -> Dict:
        """Get synchronization status and history"""
        metadata = self.get_vocab_metadata()

        recent_syncs = self.sync_history[-10:] if self.sync_history else []

        # Calculate sync statistics
        total_syncs = len(self.sync_history)
        successful_syncs = len([s for s in self.sync_history if s.get("status") == "success"])
        failed_syncs = len([s for s in self.sync_history if s.get("status") == "error"])

        return {
            "current_vocab": metadata,
            "sync_statistics": {
                "total_operations": total_syncs,
                "successful": successful_syncs,
                "failed": failed_syncs,
                "success_rate": successful_syncs / total_syncs if total_syncs > 0 else 0,
            },
            "recent_operations": recent_syncs,
            "last_sync": recent_syncs[-1] if recent_syncs else None,
        }

    def cleanup_old_backups(self, keep_days: int = 7) -> Dict:
        """Clean up old backup files"""
        backup_pattern = f"{self.vocab_file.stem}*.backup"
        backup_files = list(self.vocab_file.parent.glob(backup_pattern))

        current_time = time.time()
        keep_seconds = keep_days * 24 * 60 * 60

        removed_files = []
        for backup_file in backup_files:
            if current_time - backup_file.stat().st_mtime > keep_seconds:
                backup_file.unlink()
                removed_files.append(str(backup_file))

        return {
            "removed_backups": removed_files,
            "kept_backups": len(backup_files) - len(removed_files),
            "keep_days": keep_days,
        }


# Singleton instance for global use
_sync_instance = None


def get_sync_manager() -> TwisterLangSync:
    """Get global sync manager instance"""
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = TwisterLangSync()
    return _sync_instance


def sync_vocabularies(agent_list: List[str]) -> Dict:
    """Synchronize vocabularies across multiple agents"""
    sync_manager = get_sync_manager()
    results = {}

    local_meta = sync_manager.get_vocab_metadata()

    for agent in agent_list:
        # In a real implementation, this would query each agent
        # For simulation, assume agents have same vocab
        remote_meta = local_meta.copy()
        comparison = sync_manager.compare_vocabularies(remote_meta)

        results[agent] = {
            "comparison": comparison,
            "action_taken": "none",  # Would be push/pull in real implementation
            "status": "simulated",
        }

    return {"sync_results": results, "local_metadata": local_meta, "total_agents": len(agent_list)}


# Example usage and testing
if __name__ == "__main__":
    # Test the sync manager
    sync_mgr = get_sync_manager()

    print("TwisterLang Sync Manager Test")
    print("=" * 40)

    # Test metadata
    meta = sync_mgr.get_vocab_metadata()
    print(f"Current vocab metadata: {meta}")

    # Test sync status
    status = sync_mgr.get_sync_status()
    print(f"Sync status: {status['sync_statistics']}")

    # Test vocabulary comparison
    remote_meta = meta.copy()
    remote_meta["last_update"] = meta["last_update"] - 3600  # 1 hour older
    comparison = sync_mgr.compare_vocabularies(remote_meta)
    print(f"Comparison result: {comparison}")

    print("Sync manager test completed successfully!")
