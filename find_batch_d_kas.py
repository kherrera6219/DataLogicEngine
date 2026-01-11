import yaml

def find_lifecycle_kas():
    try:
        with open('data/registries/ka_registry.yaml', 'r') as f:
            registry = yaml.safe_load(f)
            
        target_categories = ["Lifecycle", "Governance", "Memory", "Compliance"]
        found = []
        for record in registry:
            if record.get("Category") in target_categories:
                # Filter out implemented ones (KA-012, 016 done? 016 likely not done)
                # 012 was done in Phase 1. 016 (Reg Map) might have been missed or is in this batch.
                if record['KA_ID'] not in ["KA-012"]: 
                     found.append(record)

        print(f"Found {len(found)} pending Lifecycle/Governance KAs:")
        for ka in found:
            print(f"- {ka['KA_ID']} ({ka['Category']}): {ka['KA_Name']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_lifecycle_kas()
