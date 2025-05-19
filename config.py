import os
import yaml
from pathlib import Path

class AppConfig:
    def __init__(self):
        self.data_path = Path('data')
        self.ukg_data_path = self.data_path / 'ukg'
        
        # Load YAML configurations
        self.ukg_config = self._load_config()
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
    
    def _load_config(self):
        config = {
            'ukg_paths': {
                'axis_definitions': str(self.ukg_data_path / 'axis_definitions.yaml'),
                'pillar_levels': str(self.ukg_data_path / 'pillar_levels.yaml'),
                'sectors': str(self.ukg_data_path / 'sectors.yaml'),
                'topics': str(self.ukg_data_path / 'topics.yaml'),
                'regulatory_frameworks': str(self.ukg_data_path / 'regulatory_frameworks.yaml'),
                'compliance_standards': str(self.ukg_data_path / 'compliance_standards.yaml'),
                'locations': str(self.ukg_data_path / 'locations_gazetteer.yaml'),
                'personas': str(self.ukg_data_path / 'personas.yaml')
            }
        }
        return config
