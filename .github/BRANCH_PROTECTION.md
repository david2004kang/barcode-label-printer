# Branch Protection Rules

## Master Branch Protection

The `master` branch is protected with the following rules:

### Protection Rules

1. **Required Pull Request Reviews**
   - At least 1 approving review required before merging
   - Dismiss stale reviews when new commits are pushed: **Disabled**
   - Require review from code owners: **Disabled**

2. **Require Status Checks**
   - Require branches to be up to date before merging: **Enabled**
   - Required status checks: All CI/CD checks must pass

3. **Enforce Admins**
   - **Enabled** - Even repository admins must follow these rules

4. **Restrictions**
   - Allow force pushes: **Disabled**
   - Allow deletions: **Disabled**

### What This Means

- **Repository Owner (david2004kang)**: Can still push directly to master (if needed), but protection rules apply
- **Other Contributors**: Must create Pull Requests and get at least 1 approval before merging
- **All Contributors**: Must ensure all CI/CD tests pass before merging

### Bypassing Protection (Owner Only)

If you need to bypass protection rules (e.g., for hotfixes), you can:

1. Use GitHub web interface to temporarily disable protection
2. Or use `--force-with-lease` with admin privileges (not recommended)

### Viewing Protection Rules

You can view current protection rules at:
https://github.com/david2004kang/barcode-label-printer/settings/branches
