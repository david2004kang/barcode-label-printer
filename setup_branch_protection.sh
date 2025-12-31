#!/bin/bash
# Script to help set up branch protection via GitHub Web UI

echo "=========================================="
echo "Branch Protection Setup Guide"
echo "=========================================="
echo ""
echo "Due to GitHub API limitations for personal repositories,"
echo "branch protection must be configured via the web UI."
echo ""
echo "Please follow these steps:"
echo ""
echo "1. Open this URL in your browser:"
echo "   https://github.com/david2004kang/barcode-label-printer/settings/branches"
echo ""
echo "2. Click 'Add rule' or edit existing rule for 'master' branch"
echo ""
echo "3. Enable the following settings:"
echo "   ✓ Require a pull request before merging"
echo "     - Require approvals: 1"
echo "   ✓ Require status checks to pass before merging"
echo "     - Require branches to be up to date before merging"
echo "   ✓ Include administrators (enforce_admins)"
echo "   ✗ Allow force pushes"
echo "   ✗ Allow deletions"
echo ""
echo "4. Click 'Create' or 'Save changes'"
echo ""
echo "=========================================="
echo ""
echo "Opening GitHub settings page..."
echo ""

# Try to open the URL (works on most systems)
if command -v xdg-open > /dev/null; then
    xdg-open "https://github.com/david2004kang/barcode-label-printer/settings/branches" 2>/dev/null &
elif command -v open > /dev/null; then
    open "https://github.com/david2004kang/barcode-label-printer/settings/branches" 2>/dev/null &
elif command -v start > /dev/null; then
    start "https://github.com/david2004kang/barcode-label-printer/settings/branches" 2>/dev/null &
else
    echo "Please manually open: https://github.com/david2004kang/barcode-label-printer/settings/branches"
fi
