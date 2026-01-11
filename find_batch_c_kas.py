import yaml

def find_safety_kas():
    try:
        with open('data/registries/ka_registry.yaml', 'r') as f:
            registry = yaml.safe_load(f)
            
        target_categories = ["Safety", "Ethics", "Truth"]
        found = []
        for record in registry:
            if record.get("Category") in target_categories:
                # Filter out already implemented ones
                if record['KA_ID'] not in ["KA-004", "KA-009", "KA-010", "KA-014", "KA-081", "KA-099"]: # 081 was in Batch A, 014 exists, 004/009/010 done
                     found.append(record)

        print(f"Found {len(found)} pending Safety/Ethics/Truth KAs:")
        for ka in found:
            print(f"- {ka['KA_ID']} ({ka['Category']}): {ka['KA_Name']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_safety_kas()
