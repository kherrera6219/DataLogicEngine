import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class AppConfig:
    """Main application configuration"""

    def __init__(self):
        # Flask Configuration
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
        self.DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

        # Database Configuration
        self.DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ukg_system.db')

        # UKG System Configuration
        self.MAX_SIMULATION_PASSES = int(os.environ.get('MAX_SIMULATION_PASSES', '10'))
        self.TARGET_CONFIDENCE = float(os.environ.get('TARGET_CONFIDENCE', '0.995'))
        self.ESI_THRESHOLD = float(os.environ.get('ESI_THRESHOLD', '0.85'))

        # Path Configuration
        self.DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.UKG_DATA_DIR = os.path.join(self.DATA_DIR, 'ukg')
        self.LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

        # Ensure directories exist
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        
        self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.ukg_data_path = os.path.join(self.data_path, 'ukg')
        
        # Load YAML configurations
        #self.ukg_config = self._load_config() # remove the config as it is not being used.
        self.memory_config = {
            'memory_file_path': 'data/memory_store.json'
        }
        self.ka_config = {
            'ka_implementations_path': 'core/knowledge_algorithm/implementations',
            'default_ka_confidence_threshold': 0.7
        }
        self.simulation_config = {
            'layer1_contextualizer': {
                'enabled': True,
                'min_confidence_threshold': 0.6
            },
            'layer2_qpe_ro': {
                'enabled': True,
                'min_confidence_threshold': 0.7,
                'personas': ['KE', 'SE', 'RE', 'CE']
            },
            'layer3_research': {
                'enabled': True,
                'min_confidence_threshold': 0.8
            },
            'target_confidence_threshold': 0.85
        }
        self.orchestration_config = {
            'max_simulation_passes': 3,
            'target_confidence_overall': 0.90,
            'enable_gatekeeper': True,
            'layer_progression': [1, 2, 3],  # Layers to run in sequence
            'location_awareness': {
                'enabled': True,
                'default_location': 'LOC_COUNTRY_USA'
            }
        }
    
    #def _load_config(self):
    #    config = {
    #        'ukg_paths': {
    #            'axis_definitions': str(self.ukg_data_path / 'axis_definitions.yaml'),
    #            'pillar_levels': str(self.ukg_data_path / 'pillar_levels.yaml'),
    #            'sectors': str(self.ukg_data_path / 'sectors.yaml'),
    #            'topics': str(self.ukg_data_path / 'topics.yaml'),
    #            'regulatory_frameworks': str(self.ukg_data_path / 'regulatory_frameworks.yaml'),
    #            'compliance_standards': str(self.ukg_data_path / 'compliance_standards.yaml'),
    #            'locations': str(self.ukg_data_path / 'locations_gazetteer.yaml'),
    #            'personas': str(self.ukg_data_path / 'personas.yaml')
    #        }
    #    }
    #    return config

    @property
    def axis_definitions_path(self):
        return os.path.join(self.UKG_DATA_DIR, 'axis_definitions.yaml')

    @property
    def pillar_levels_path(self):
        return os.path.join(self.UKG_DATA_DIR, 'pillar_levels.yaml')

    @property
    def locations_gazetteer_path(self):
        return os.path.join(self.UKG_DATA_DIR, 'locations_gazetteer.yaml')

    @property
    def regulatory_frameworks_path(self):
        return os.path.join(self.UKG_DATA_DIR, 'regulatory_frameworks.yaml')