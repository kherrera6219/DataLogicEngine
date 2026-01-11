import yaml

def get_ka_specs(ka_ids):
    try:
        with open('data/registries/ka_registry.yaml', 'r') as f:
            registry = yaml.safe_load(f)
            
        found = []
        for record in registry:
            if record['KA_ID'] in ka_ids:
                found.append(record)
                
        for ka in found:
            print(f"--- {ka['KA_ID']}: {ka['KA_Name']} ---")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target_ids = [f"KA-{i:03d}" for i in range(1, 15)]
    get_ka_specs(target_ids)
