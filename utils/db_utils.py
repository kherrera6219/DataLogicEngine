"""Database utility helpers for the UKG system.

These helpers provide small, testable wrappers around common CRUD
operations so the Phase 3 test suite can exercise database behavior
without repeating boilerplate session management.
"""

import logging
from datetime import datetime
from typing import Optional

from extensions import db
from db_models import Edge, KAExecution, KnowledgeAlgorithm, Node
from backend.models import MemoryEntry, UkgSession


class DatabaseManager:
    """Lightweight helper for common database interactions."""

    @staticmethod
    def add_node(uid: str, node_type: str, label: str, axis_number: int, description: Optional[str] = None,
                 attributes: Optional[dict] = None) -> Optional[Node]:
        """Add a new knowledge graph node."""
        try:
            node = Node(
                uid=uid,
                node_type=node_type,
                label=label,
                axis_number=axis_number,
                description=description,
                attributes=attributes,
            )
            db.session.add(node)
            db.session.commit()
            logging.info("Added node with UID: %s", uid)
            return node
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to add node: %s", exc, exc_info=True)
            return None

    @staticmethod
    def get_node_by_uid(uid: str) -> Optional[Node]:
        """Retrieve a node by its UID."""
        return Node.query.filter_by(uid=uid).first()

    @staticmethod
    def add_edge(uid: str, edge_type: str, source_uid: str, target_uid: str, weight: float = 1.0,
                 attributes: Optional[dict] = None) -> Optional[Edge]:
        """Create an edge between two nodes."""
        try:
            source_node = DatabaseManager.get_node_by_uid(source_uid)
            target_node = DatabaseManager.get_node_by_uid(target_uid)
            if not source_node or not target_node:
                logging.error("Failed to add edge: source or target node not found. Source: %s Target: %s", source_uid,
                              target_uid)
                return None

            edge = Edge(
                uid=uid,
                edge_type=edge_type,
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                weight=weight,
                attributes=attributes,
            )
            db.session.add(edge)
            db.session.commit()
            logging.info("Added edge with UID: %s", uid)
            return edge
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to add edge: %s", exc, exc_info=True)
            return None

    @staticmethod
    def create_session(session_id: str, query: Optional[str] = None, target_confidence: float = 0.85) -> Optional[UkgSession]:
        """Create a new UKG session record."""
        try:
            session = UkgSession(
                session_id=session_id,
                user_query=query,
                target_confidence=target_confidence,
                status="active",
                started_at=datetime.utcnow(),
            )
            db.session.add(session)
            db.session.commit()
            logging.info("Created session with ID: %s", session_id)
            return session
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to create session: %s", exc, exc_info=True)
            return None

    @staticmethod
    def complete_session(session_id: str, final_confidence: Optional[float] = None) -> bool:
        """Mark a session as completed."""
        try:
            session = UkgSession.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error("Session not found: %s", session_id)
                return False

            session.status = "completed"
            session.completed_at = datetime.utcnow()
            if final_confidence is not None:
                session.final_confidence = final_confidence

            db.session.commit()
            logging.info("Completed session with ID: %s", session_id)
            return True
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to complete session: %s", exc, exc_info=True)
            return False

    @staticmethod
    def add_memory_entry(uid: str, session_id: str, entry_type: str, content: dict,
                         pass_num: int = 0, layer_num: int = 0, confidence: float = 1.0) -> Optional[MemoryEntry]:
        """Add a new memory entry to the database."""
        try:
            session = UkgSession.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error("Session not found: %s", session_id)
                return None

            memory_entry = MemoryEntry(
                uid=uid,
                session_id=session_id,
                entry_type=entry_type,
                content=content,
                pass_num=pass_num,
                layer_num=layer_num,
                confidence=confidence,
            )
            db.session.add(memory_entry)
            db.session.commit()
            logging.info("Added memory entry with UID: %s", uid)
            return memory_entry
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to add memory entry: %s", exc, exc_info=True)
            return None

    @staticmethod
    def get_memory_entries_by_session(session_id: str, entry_type: Optional[str] = None):
        """Get all memory entries for a specific session."""
        query = MemoryEntry.query.filter_by(session_id=session_id)
        if entry_type:
            query = query.filter_by(entry_type=entry_type)
        return query.all()

    @staticmethod
    def register_knowledge_algorithm(algorithm_id: str, name: str, description: Optional[str] = None,
                                     input_schema: Optional[dict] = None, output_schema: Optional[dict] = None,
                                     version: str = "1.0", language: str = "python") -> Optional[KnowledgeAlgorithm]:
        """Register a knowledge algorithm in the database."""
        try:
            ka = KnowledgeAlgorithm(
                uid=f"ka-{algorithm_id}",
                algorithm_id=algorithm_id,
                name=name,
                description=description,
                input_schema=input_schema or {},
                output_schema=output_schema or {},
                version=version,
                language=language,
                code="",
            )
            db.session.add(ka)
            db.session.commit()
            logging.info("Registered KA with ID: %s", algorithm_id)
            return ka
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to register KA: %s", exc, exc_info=True)
            return None

    @staticmethod
    def record_ka_execution(algorithm_id: str, session_id: str, input_data: dict, output_data: Optional[dict] = None,
                            status: str = "completed", error_message: Optional[str] = None) -> Optional[KAExecution]:
        """Record the execution of a knowledge algorithm."""
        try:
            ka = KnowledgeAlgorithm.query.filter_by(algorithm_id=algorithm_id).first()
            if not ka:
                logging.error("KA not found: %s", algorithm_id)
                return None

            execution = KAExecution(
                uid=f"ka-exec-{algorithm_id}-{session_id}-{int(datetime.utcnow().timestamp())}",
                algorithm_id=ka.id,
                input_params={"session_id": session_id, "payload": input_data},
                output_results=output_data,
                status=status,
                error_message=error_message,
                started_at=datetime.utcnow(),
            )
            db.session.add(execution)
            db.session.commit()
            logging.info("Recorded execution of KA %s in session %s", algorithm_id, session_id)
            return execution
        except Exception as exc:  # pragma: no cover - defensive logging path
            db.session.rollback()
            logging.error("Failed to record KA execution: %s", exc, exc_info=True)
            return None
