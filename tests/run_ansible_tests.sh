#!/bin/bash
# Script to run the Ansible playbook for testing GoLLM shell queries

echo "Starting GoLLM shell query tests with Ansible..."

# Create test results directory if it doesn't exist
mkdir -p test_results

# Set environment variables for testing
export GOLLM_ADAPTER_TYPE=modular
export GOLLM_LOG_LEVEL=DEBUG

# Run the Ansible playbook
ansible-playbook ansible_test.yml -v

echo "Tests completed! Check the test_results directory for detailed logs."
echo "Test summary: test_results/test_summary.md"
