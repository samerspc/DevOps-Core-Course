#!/bin/bash
# Test script for Task 1 - Blocks & Tags

echo "=== Task 1: Testing Blocks & Tags ==="
echo ""

echo "1. List all available tags:"
echo "-----------------------------------"
ansible-playbook playbooks/provision.yml --list-tags
echo ""

echo "2. Test selective execution with --tags 'packages':"
echo "-----------------------------------"
ansible-playbook playbooks/provision.yml --tags "packages" --check --diff
echo ""

echo "3. Test selective execution with --tags 'docker_install':"
echo "-----------------------------------"
ansible-playbook playbooks/provision.yml --tags "docker_install" --check --diff
echo ""

echo "4. Test skip tags with --skip-tags 'common':"
echo "-----------------------------------"
ansible-playbook playbooks/provision.yml --skip-tags "common" --check --diff
echo ""

echo "5. Test multiple tags:"
echo "-----------------------------------"
ansible-playbook playbooks/provision.yml --tags "packages,docker_config" --check --diff
echo ""

echo "=== Testing completed ==="
echo ""
echo "Note: Use --ask-become-pass if sudo password is required"
echo "Example: ansible-playbook playbooks/provision.yml --tags 'packages' --ask-become-pass"
