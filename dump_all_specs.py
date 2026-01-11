import yaml

def get_all_active_specs():
    try:
        with open('data/registries/ka_registry.yaml', 'r') as f:
            registry = yaml.safe_load(f)
            
        print("TOTAL_KAS_START")
        for record in registry:
            if record.get('Status') == 'Active':
                 print(f"ID: {record['KA_ID']}")
                 print(f"NAME: {record['KA_Name']}")
                 print(f"PURPOSE: {record['Purpose']}")
                 print(f"CATEGORY: {record.get('Category', 'N/A')}")
                 print(f"LAYER: {record.get('Primary_Layers', 'L10')}")
                 print("---")
        print("TOTAL_KAS_END")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_all_active_specs()
