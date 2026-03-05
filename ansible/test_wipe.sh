#!/bin/bash
# Test script for Task 3 - Wipe Logic

echo "=== Task 3: Testing Wipe Logic ==="
echo ""

echo "=========================================="
echo "Scenario 1: Normal deployment (wipe should NOT run)"
echo "=========================================="
echo "Command: ansible-playbook playbooks/deploy.yml --ask-become-pass"
echo "Expected: App deploys normally, wipe tasks skipped"
echo ""

echo "=========================================="
echo "Scenario 2: Wipe only (remove existing deployment)"
echo "=========================================="
echo "Command: ansible-playbook playbooks/deploy.yml -e \"web_app_wipe=true\" --tags web_app_wipe --ask-become-pass"
echo "Expected: App should be removed, deployment skipped"
echo ""

echo "=========================================="
echo "Scenario 3: Clean reinstallation (wipe → deploy)"
echo "=========================================="
echo "Command: ansible-playbook playbooks/deploy.yml -e \"web_app_wipe=true\" --ask-become-pass"
echo "Expected:"
echo "  1. Wipe tasks run first (remove old installation)"
echo "  2. Deployment tasks run second (install fresh)"
echo "  Result: clean reinstallation"
echo ""

echo "=========================================="
echo "Scenario 4a: Safety check - Tag specified but variable false"
echo "=========================================="
echo "Command: ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-become-pass"
echo "Expected: Wipe tasks skipped (when condition blocks it), deployment runs normally"
echo ""

echo "=========================================="
echo "Scenario 4b: Safety check - Variable true, only wipe tag"
echo "=========================================="
echo "Command: ansible-playbook playbooks/deploy.yml -e \"web_app_wipe=true\" --tags web_app_wipe --ask-become-pass"
echo "Expected: Only wipe runs, no deployment"
echo ""

echo "=== Testing completed ==="
echo ""
echo "Note: Use --ask-vault-pass if vault password is required"
echo "Example: ansible-playbook playbooks/deploy.yml -e \"web_app_wipe=true\" --tags web_app_wipe --ask-become-pass --ask-vault-pass"
