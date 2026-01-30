import sys
try:
    print("Attempting to import ukg_sdk.truth_engine.truthgate module...")
    import ukg_sdk.truth_engine.truthgate as tg_module
    print(f"Module imported: {tg_module}")
    print(f"File: {tg_module.__file__}")
    print(f"Attributes: {dir(tg_module)}")
    
    print("Attempting to access TruthGate class...")
    if hasattr(tg_module, 'TruthGate'):
        print(f"TruthGate found: {tg_module.TruthGate}")
    else:
        print("TruthGate NOT found in module attributes!")

except ImportError as e:
    print(f"ImportError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
