# Branch Protection 設定說明

## 透過 GitHub Web UI 設定（推薦）

由於個人 repository 的 API 限制，建議透過 GitHub Web UI 設定 branch protection：

### 步驟

1. **前往 Branch Protection 設定頁面**
   - 連結：https://github.com/david2004kang/barcode-label-printer/settings/branches
   - 或：Repository → Settings → Branches

2. **選擇 master branch**
   - 在 "Branch protection rules" 區塊中，點擊 "Add rule" 或編輯現有規則
   - Branch name pattern: `master`

3. **啟用以下保護規則**

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: `1`
   - ✅ Dismiss stale pull request approvals when new commits are pushed: 取消勾選
   - ✅ Require review from Code Owners: 取消勾選

   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - Required status checks: 選擇所有 CI/CD checks（或留空讓所有檢查都必須通過）

   ✅ **Require conversation resolution before merging**
   - （可選）啟用以確保所有討論都解決

   ✅ **Do not allow bypassing the above settings**
   - ✅ Include administrators: **勾選**（這會讓您也需要遵循規則）

   ✅ **Restrict who can push to matching branches**
   - 個人 repository 不支援此功能，但透過上述規則已可達到保護效果

   ❌ **Allow force pushes**: **取消勾選**
   ❌ **Allow deletions**: **取消勾選**

4. **儲存變更**
   - 點擊 "Create" 或 "Save changes"

## 透過 GitHub CLI 設定（進階）

如果 API 支援，可以使用以下命令：

```bash
gh api repos/david2004kang/barcode-label-printer/branches/master/protection \
  --method PUT \
  -f required_status_checks='{"strict":true,"contexts":[]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

## 驗證設定

設定完成後，可以透過以下方式驗證：

```bash
gh api repos/david2004kang/barcode-label-printer/branches/master/protection \
  --jq '.required_pull_request_reviews.required_approving_review_count'
```

應該返回：`1`

## 注意事項

1. **Repository Owner 權限**
   - 即使啟用 "Include administrators"，repository owner 通常仍可以直接 push
   - 如需完全限制，需要透過 GitHub Settings 中的其他選項

2. **CI/CD 檢查**
   - 確保所有 GitHub Actions workflows 都設定為 required status checks
   - 這可以在 Branch Protection 設定中選擇

3. **緊急情況**
   - 如果需要緊急修復，repository owner 可以暫時關閉保護規則
   - 或使用 `--force-with-lease`（不推薦）

## 當前保護狀態

查看當前保護規則：
https://github.com/david2004kang/barcode-label-printer/settings/branches
