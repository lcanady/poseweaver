#!/bin/bash

# Fix APT sources for Ubuntu 25.04 (Plucky)
# Remove problematic PPA and continue with Nginx setup

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Fixing APT sources for Ubuntu 25.04..."

# Remove the problematic deadsnakes PPA
if [ -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-plucky.list ]; then
    print_status "Removing deadsnakes PPA for Ubuntu 25.04..."
    rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-plucky.list
fi

# Also check for other deadsnakes entries
find /etc/apt/sources.list.d/ -name "*deadsnakes*" -delete 2>/dev/null || true

# Update package lists
print_status "Updating package lists..."
apt update

print_success "APT sources fixed successfully!"
print_status "You can now continue with the Nginx setup."
