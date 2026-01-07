# Demo Scripts

This directory contains demonstration scripts for the DataLogicEngine Universal Knowledge Graph system.

## Directory Structure

```
demos/
├── ka/                    # Knowledge Algorithm demos
│   ├── run_ka_demo.py
│   ├── run_ka_master_demo.py
│   └── run_ka_orchestration_demo.py
│
├── layers/                # Layer-specific demos
│   ├── run_layer1_demo.py
│   ├── run_layered_database_demo.py
│   ├── run_ukg_layer7_demo.py
│   ├── run_ukg_layer8_demo.py
│   └── run_ukg_layer9_10_demo.py
│
├── simulation/            # Simulation system demos
│   ├── run_ukg_simulation_demo.py
│   ├── run_quad_demo.py
│   ├── quad_demo.py
│   └── ukg_simulation_demo.py
│
├── compliance/            # Compliance and regulatory demos
│   ├── run_regulatory_compliance_demo.py
│   ├── run_refinement_workflow_demo.py
│   └── security_compliance_demo.py
│
└── standalone/            # Standalone execution demos
    ├── run_standalone.py
    ├── run_standalone_demo.py
    ├── run_ukg_standalone.py
    ├── run_ukg_13axis_demo.py
    └── run_ukg_demo.py
```

## Running Demos

All demos should be run from the project root directory:

```bash
# Knowledge Algorithm demos
python demos/ka/run_ka_demo.py
python demos/ka/run_ka_master_demo.py

# Layer demos
python demos/layers/run_layer1_demo.py

# Simulation demos
python demos/simulation/run_quad_demo.py

# Compliance demos
python demos/compliance/run_regulatory_compliance_demo.py
```

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Set up environment variables in `.env` file at project root.
