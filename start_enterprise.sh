
#!/bin/bash
# UKG Enterprise Architecture Runner

echo "Starting UKG Enterprise Architecture..."

# Ensure logs directory exists
mkdir -p logs

# Start the enterprise architecture
python run_enterprise_ukg.py "$@"
