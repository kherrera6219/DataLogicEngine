import yaml

def get_missing_specs(ka_ids):
    try:
        with open('data/registries/ka_registry.yaml', 'r') as f:
            registry = yaml.safe_load(f)
            
        found = []
        for record in registry:
            if record['KA_ID'] in ka_ids:
                found.append(record)
                
        for ka in found:
            print(f"--- {ka['KA_ID']}: {ka['KA_Name']} ---")
            print(f"Purpose: {ka['Purpose']}")
            print(f"Category: {ka.get('Category', 'N/A')}")
            print(f"Layers: {ka.get('Primary_Layers', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    missing = [
        "KA-037", "KA-040", "KA-042", "KA-044", "KA-051", 
        "KA-057", "KA-058", "KA-063", "KA-064", "KA-068", 
        "KA-069", "KA-070", "KA-071", "KA-072", "KA-073", 
        "KA-076", "KA-077", "KA-099", "KA-101", "KA-102"
    ]
    get_missing_specs(missing)
