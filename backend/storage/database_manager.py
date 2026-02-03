import os
import subprocess
import time
import socket
import logging
import signal
import sys
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseLifecycleManager:
    """
    Manages the lifecycle of portable database instances (PostgreSQL, Redis, Neo4j).
    Designed for desktop deployment where external services are unavailable.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
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
        
        # Postgres Config
        self.pg_bin = os.path.join(self.base_dir, 'postgresql', 'bin')
        self.pg_data = os.path.join(self.base_dir, 'postgresql', 'data')
        self.pg_port = 54320
        self.pg_process: Optional[subprocess.Popen] = None
        
        # Redis Config
        self.redis_bin = os.path.join(self.base_dir, 'redis')
        self.redis_data = os.path.join(self.base_dir, 'redis', 'data')
        self.redis_port = 63790
        self.redis_process: Optional[subprocess.Popen] = None

        # Neo4j Config
        self.neo4j_bin = os.path.join(self.base_dir, 'neo4j', 'bin')
        self.neo4j_data = os.path.join(self.base_dir, 'neo4j', 'data')
        self.neo4j_port = 7687
        self.neo4j_process: Optional[subprocess.Popen] = None

    def is_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def start_postgres(self):
        """Start portable PostgreSQL instance."""
        if self.is_port_in_use(self.pg_port):
            logger.info(f"PostgreSQL port {self.pg_port} already in use. Assuming it is running.")
            return

        # Ensure data directory is initialized
        if not os.path.exists(os.path.join(self.pg_data, 'PG_VERSION')):
            logger.info("Initializing PostgreSQL data directory...")
            try:
                initdb_path = os.path.join(self.pg_bin, 'initdb.exe' if os.name == 'nt' else 'initdb')
                subprocess.run([initdb_path, '-D', self.pg_data, '--auth=trust'], check=True)
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL: {e}")
                return

        logger.info(f"Starting PostgreSQL on port {self.pg_port}...")
        try:
            postgres_path = os.path.join(self.pg_bin, 'postgres.exe' if os.name == 'nt' else 'postgres')
            self.pg_process = subprocess.Popen([
                postgres_path, 
                '-D', self.pg_data, 
                '-p', str(self.pg_port),
                '-h', '127.0.0.1'
            ])
            logger.info("PostgreSQL started successfully.")
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL: {e}")

    def start_redis(self):
        """Start portable Redis instance."""
        if self.is_port_in_use(self.redis_port):
            logger.info(f"Redis port {self.redis_port} already in use. Assuming it is running.")
            return

        if not os.path.exists(self.redis_data):
            os.makedirs(self.redis_data)

        logger.info(f"Starting Redis on port {self.redis_port}...")
        try:
            redis_exe = 'redis-server.exe' if os.name == 'nt' else 'redis-server'
            redis_path = os.path.join(self.redis_bin, redis_exe)
            
            # Create a minimal config if needed or use command line args
            self.redis_process = subprocess.Popen([
                redis_path,
                '--port', str(self.redis_port),
                '--bind', '127.0.0.1',
                '--dir', self.redis_data,
                '--save', '60 1', # Save every 60s if 1 key changed
                '--loglevel', 'warning'
            ])
            logger.info("Redis started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")

    def start_neo4j(self):
        """Start portable Neo4j instance."""
        if self.is_port_in_use(self.neo4j_port):
            logger.info(f"Neo4j port {self.neo4j_port} already in use. Assuming it is running.")
            return

        logger.info(f"Starting Neo4j on port {self.neo4j_port}...")
        try:
            neo4j_bin = os.path.join(self.neo4j_bin, 'neo4j.bat' if os.name == 'nt' else 'neo4j')
            # Use 'console' mode to run as a child process we can monitor
            self.neo4j_process = subprocess.Popen([
                neo4j_bin, 'console'
            ], env={**os.environ, 'NEO4J_HOME': os.path.dirname(self.neo4j_bin)})
            logger.info("Neo4j started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Neo4j: {e}")

    def start_all(self):
        """Start all managed database services."""
        # Ensure base directories exist
        for db_name in ['postgresql', 'redis', 'neo4j']:
            path = os.path.join(self.base_dir, db_name)
            if not os.path.exists(path):
                logger.warning(f"Database directory {path} does not exist. Skipping {db_name} startup.")
                continue
            
            if db_name == 'postgresql':
                self.start_postgres()
            elif db_name == 'redis':
                self.start_redis()
            elif db_name == 'neo4j':
                self.start_neo4j()

    def stop_all(self):
        """Gracefully shutdown all managed database services."""
        processes = []
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
                proc.wait(timeout=10)
                logger.info(f"{name} stopped.")
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} did not stop gracefully. Killing...")
                proc.kill()
                proc.wait()

def get_db_manager() -> DatabaseLifecycleManager:
    """Factory for DatabaseLifecycleManager."""
    return DatabaseLifecycleManager()
