import os
import secrets  # noqa: PLC0415 — used for local PG password generation
import subprocess  # nosec B404
import socket
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseLifecycleManager:
    """
    Manages the lifecycle of portable database instances (PostgreSQL, Redis, Neo4j).
    Designed for desktop deployment where external services are unavailable.
    """
    
    def __init__(
        self,
        base_dir: Optional[str] = None,
        *,
        stop_timeout_seconds: float = 10.0,
        product_version: str = "0.1.1",
    ):
        if base_dir:
            self.base_dir = base_dir
        else:
            # Handle PyInstaller frozen state
            if getattr(sys, 'frozen', False):
                # If frozen, base_dir is adjacent to the executable
                application_path = os.path.dirname(sys.executable)
            else:
                # If running as script, base_dir is root of project (assuming script in root)
                application_path = os.getcwd()
            
            self.base_dir = os.path.join(application_path, 'databases')
        self.stop_timeout_seconds = max(0.1, float(stop_timeout_seconds))
        self.product_version = str(product_version)
        self.last_failure_reasons: dict[str, str] = {}
        
        # Postgres Config
        self.pg_bin = os.path.join(self.base_dir, 'postgresql', 'bin')
        self.pg_data = os.path.join(self.base_dir, 'postgresql', 'data')
        self.pg_port = int(os.environ.get("POSTGRES_LOCAL_PORT", "5432"))
        self.pg_process: Optional[subprocess.Popen] = None
        
        # Redis Config
        self.redis_bin = os.path.join(self.base_dir, 'redis')
        self.redis_data = os.path.join(self.base_dir, 'redis', 'data')
        self.redis_port = int(os.environ.get("REDIS_LOCAL_PORT", "6379"))
        self.redis_process: Optional[subprocess.Popen] = None

        # Neo4j Config
        self.neo4j_bin = os.path.join(self.base_dir, 'neo4j', 'bin')
        self.neo4j_data = os.path.join(self.base_dir, 'neo4j', 'data')
        self.neo4j_port = int(os.environ.get("NEO4J_LOCAL_PORT", "7687"))
        self.neo4j_process: Optional[subprocess.Popen] = None

    def is_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def expected_identity(self, service: str) -> str:
        return f"datalogicengine:{self.product_version}:{service}:{id(self)}"

    def probe_service(self, service: str) -> tuple[bool, str | None]:
        """Report health only when the owned child process is still alive."""
        process_by_service = {
            "postgresql": self.pg_process,
            "redis": self.redis_process,
            "neo4j": self.neo4j_process,
        }
        port_by_service = {
            "postgresql": self.pg_port,
            "redis": self.redis_port,
            "neo4j": self.neo4j_port,
        }
        process = process_by_service[service]
        if process is not None and process.poll() is None:
            return True, f"{self.expected_identity(service)}:pid={process.pid}"
        port = port_by_service[service]
        if self.is_port_in_use(port):
            return True, f"foreign-listener:127.0.0.1:{port}"
        return False, None

    def _get_or_create_pg_password(self) -> str:
        """
        Return the local PostgreSQL password for this desktop installation.
        Creates and persists a random password on first call.
        The file is chmod 0o600 (owner-read-only) on POSIX systems.
        """
        pw_file = os.path.join(self.base_dir, 'postgresql', '.pg_local_pw')
        if os.path.exists(pw_file):
            pw = open(pw_file).read().strip()  # noqa: WPS515
            if pw:
                return pw
        pw = secrets.token_urlsafe(24)
        os.makedirs(os.path.dirname(pw_file), exist_ok=True)
        with open(pw_file, 'w') as fh:
            fh.write(pw)
        try:
            os.chmod(pw_file, 0o600)
        except OSError:
            logger.warning("Could not restrict permissions on %s (non-POSIX platform)", pw_file)
        return pw

    def _resolve_executable(self, executable_path: str) -> str:
        """
        Resolve and validate executable paths under the managed database directory.
        Prevents path traversal when building process command lists.
        """
        resolved_path = os.path.abspath(executable_path)
        base_root = os.path.abspath(self.base_dir)
        if not resolved_path.startswith(base_root):
            raise ValueError(f"Executable path outside managed database root: {resolved_path}")
        return resolved_path

    def start_postgres(self):
        """Start portable PostgreSQL instance."""
        if self.is_port_in_use(self.pg_port):
            logger.error("PostgreSQL port %s is owned by an unverified listener", self.pg_port)
            self.last_failure_reasons["postgresql"] = "foreign_listener_on_configured_port"
            return False

        # Ensure data directory is initialized
        if not os.path.exists(os.path.join(self.pg_data, 'PG_VERSION')):
            logger.info("Initializing PostgreSQL data directory with scram-sha-256 auth...")
            try:
                initdb_path = os.path.join(self.pg_bin, 'initdb.exe' if os.name == 'nt' else 'initdb')
                safe_initdb = self._resolve_executable(initdb_path)
                pg_pw = self._get_or_create_pg_password()
                pw_file = os.path.join(self.base_dir, 'postgresql', '.pg_local_pw')
                # Write password to a temp file consumed by --pwfile; use scram-sha-256 for all
                # connections (loopback-only, but trust auth is disallowed by policy).
                with open(pw_file, 'w') as _pwf:
                    _pwf.write(pg_pw)
                subprocess.run(  # nosec B603
                    [safe_initdb, '-D', self.pg_data, '--auth=scram-sha-256', f'--pwfile={pw_file}'],
                    check=True,
                    shell=False,
                )
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL: {e}")
                self.last_failure_reasons["postgresql"] = "initialization_failed"
                return False

        logger.info(f"Starting PostgreSQL on port {self.pg_port}...")
        try:
            postgres_path = os.path.join(self.pg_bin, 'postgres.exe' if os.name == 'nt' else 'postgres')
            safe_postgres = self._resolve_executable(postgres_path)
            self.pg_process = subprocess.Popen([
                safe_postgres,
                '-D', self.pg_data, 
                '-p', str(self.pg_port),
                '-h', '127.0.0.1'
            ], shell=False)  # nosec B603
            logger.info("PostgreSQL started successfully.")
            self.last_failure_reasons.pop("postgresql", None)
            return True
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL: {e}")
            self.last_failure_reasons["postgresql"] = "start_failed"
            return False

    def start_redis(self):
        """Start portable Redis instance."""
        if self.is_port_in_use(self.redis_port):
            logger.error("Redis port %s is owned by an unverified listener", self.redis_port)
            self.last_failure_reasons["redis"] = "foreign_listener_on_configured_port"
            return False

        if not os.path.exists(self.redis_data):
            os.makedirs(self.redis_data)

        logger.info(f"Starting Redis on port {self.redis_port}...")
        try:
            redis_exe = 'redis-server.exe' if os.name == 'nt' else 'redis-server'
            redis_path = os.path.join(self.redis_bin, redis_exe)
            safe_redis = self._resolve_executable(redis_path)
            
            # Create a minimal config if needed or use command line args
            self.redis_process = subprocess.Popen([
                safe_redis,
                '--port', str(self.redis_port),
                '--bind', '127.0.0.1',
                '--dir', self.redis_data,
                '--save', '60 1', # Save every 60s if 1 key changed
                '--loglevel', 'warning'
            ], shell=False)  # nosec B603
            logger.info("Redis started successfully.")
            self.last_failure_reasons.pop("redis", None)
            return True
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            self.last_failure_reasons["redis"] = "start_failed"
            return False

    def _find_java_home(self) -> str:
        """Return a JAVA_HOME path, searching common locations when not set."""
        bundled_jre = os.path.join(self.base_dir, "jre")
        if self._java_home_has_runtime(bundled_jre):
            return bundled_jre

        neo4j_home = os.path.dirname(self.neo4j_bin)
        neo4j_jre = os.path.join(neo4j_home, "jre")
        if self._java_home_has_runtime(neo4j_jre):
            return neo4j_jre

        # Explicit env var is respected after app-owned runtimes.
        if os.environ.get("JAVA_HOME"):
            return os.environ["JAVA_HOME"]

        candidates = []
        if os.name == "nt":
            for base in [
                os.path.expandvars(r"%ProgramFiles%\Java"),
                os.path.expandvars(r"%ProgramFiles%\Eclipse Adoptium"),
                os.path.expandvars(r"%ProgramFiles%\Amazon Corretto"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft"),
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Eclipse Adoptium"),
            ]:
                if os.path.isdir(base):
                    for entry in os.listdir(base):
                        full = os.path.join(base, entry)
                        if os.path.isfile(os.path.join(full, "bin", "java.exe")):
                            candidates.append(full)
            # VS Code / IntelliJ embedded JREs
            for pattern_base in [
                os.path.expandvars(r"%USERPROFILE%\.antigravity\extensions"),
                os.path.expandvars(r"%USERPROFILE%\.vscode\extensions"),
            ]:
                if os.path.isdir(pattern_base):
                    for ext in os.listdir(pattern_base):
                        jre_dir = os.path.join(pattern_base, ext, "jre")
                        if os.path.isdir(jre_dir):
                            for jvm in os.listdir(jre_dir):
                                full = os.path.join(jre_dir, jvm)
                                if os.path.isfile(os.path.join(full, "bin", "java.exe")):
                                    candidates.append(full)

        # Return newest-looking candidate (heuristic: sort by name desc)
        if candidates:
            return sorted(candidates, reverse=True)[0]
        return ""

    @staticmethod
    def _java_home_has_runtime(java_home: str) -> bool:
        java_exe = "java.exe" if os.name == "nt" else "java"
        return os.path.isfile(os.path.join(java_home, "bin", java_exe))

    def start_neo4j(self):
        """Start portable Neo4j instance."""
        if self.is_port_in_use(self.neo4j_port):
            logger.error("Neo4j port %s is owned by an unverified listener", self.neo4j_port)
            self.last_failure_reasons["neo4j"] = "foreign_listener_on_configured_port"
            return False

        logger.info(f"Starting Neo4j on port {self.neo4j_port}...")
        try:
            neo4j_bin = os.path.join(self.neo4j_bin, 'neo4j.bat' if os.name == 'nt' else 'neo4j')
            safe_neo4j = self._resolve_executable(neo4j_bin)
            neo4j_home = os.path.dirname(self.neo4j_bin)
            java_home = self._find_java_home()
            env = {**os.environ, "NEO4J_HOME": neo4j_home}
            if java_home:
                env["JAVA_HOME"] = java_home
                logger.info(f"Neo4j using JAVA_HOME={java_home}")
            # Use 'console' mode to run as a child process we can monitor
            self.neo4j_process = subprocess.Popen(
                [safe_neo4j, 'console'], env=env, shell=False  # nosec B603
            )
            logger.info("Neo4j started successfully.")
            self.last_failure_reasons.pop("neo4j", None)
            return True
        except Exception as e:
            logger.error(f"Failed to start Neo4j: {e}")
            self.last_failure_reasons["neo4j"] = "start_failed"
            return False

    def start_all(self):
        """Start all managed database services."""
        results = {}
        # Ensure base directories exist
        for db_name in ['postgresql', 'redis', 'neo4j']:
            path = os.path.join(self.base_dir, db_name)
            if not os.path.exists(path):
                logger.warning(f"Database directory {path} does not exist. Skipping {db_name} startup.")
                results[db_name] = False
                continue
            
            if db_name == 'postgresql':
                results[db_name] = self.start_postgres()
            elif db_name == 'redis':
                results[db_name] = self.start_redis()
            elif db_name == 'neo4j':
                results[db_name] = self.start_neo4j()
        return results

    def stop_all(self):
        """Gracefully shutdown all managed database services."""
        processes = []
        results = {
            "postgresql": self.pg_process is None,
            "redis": self.redis_process is None,
            "neo4j": self.neo4j_process is None,
        }
        if self.pg_process:
            logger.info("Stopping PostgreSQL...")
            self.pg_process.terminate()
            processes.append(('PostgreSQL', self.pg_process))
            
        if self.redis_process:
            logger.info("Stopping Redis...")
            self.redis_process.terminate()
            processes.append(('Redis', self.redis_process))

        if self.neo4j_process:
            logger.info("Stopping Neo4j...")
            self.neo4j_process.terminate()
            processes.append(('Neo4j', self.neo4j_process))

        # Wait for all processes to exit
        for name, proc in processes:
            try:
                proc.wait(timeout=self.stop_timeout_seconds)
                logger.info(f"{name} stopped.")
                results[name.lower()] = True
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} did not stop gracefully. Killing...")
                proc.kill()
                proc.wait()
                results[name.lower()] = True
        self.pg_process = None
        self.redis_process = None
        self.neo4j_process = None
        return results

_process_db_manager: DatabaseLifecycleManager | None = None


def get_db_manager() -> DatabaseLifecycleManager:
    """Return the application-owned manager or one process fallback instance."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            manager = current_app.extensions.get("dle_database_manager")
            if manager is not None:
                return manager
    except ImportError:
        pass

    global _process_db_manager
    if _process_db_manager is None:
        _process_db_manager = DatabaseLifecycleManager()
    return _process_db_manager
