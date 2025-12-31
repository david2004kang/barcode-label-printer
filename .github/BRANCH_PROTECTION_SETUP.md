# Branch Protection 設定說明

## 快速設定（透過 GitHub Web UI）

由於 GitHub API 對個人 repository 的限制，建議透過 Web UI 設定：

### 直接連結
**https://github.com/david2004kang/barcode-label-printer/settings/branches**

### 設定步驟

1. **前往設定頁面**
   - 點擊上方連結，或
   - Repository → Settings → Branches

2. **新增或編輯 Branch Protection Rule**
   - Branch name pattern: `master`
   - 點擊 "Add rule" 或編輯現有規則

3. **啟用以下保護規則**

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: `1` (至少需要 1 個審核)
   - ❌ Dismiss stale pull request approvals when new commits are pushed
   - ❌ Require review from Code Owners

   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - Required status checks: 留空（讓所有檢查都必須通過）

   ✅ **Include administrators**
   - ✅ **勾選此選項** - 這會讓 repository owner 也需要遵循規則

   ❌ **Allow force pushes**: **取消勾選**
   ❌ **Allow deletions**: **取消勾選**

4. **儲存變更**
   - 點擊 "Create" 或 "Save changes"

## 使用腳本開啟設定頁面

執行以下命令會自動開啟設定頁面：

```bash
./setup_branch_protection.sh
```

或在 Windows 中：
```cmd
start https://github.com/david2004kang/barcode-label-printer/settings/branches
```

## 保護規則說明

設定完成後：

- ✅ **其他貢獻者**：必須透過 Pull Request，且需要至少 1 個審核才能合併
- ✅ **Repository Owner (您)**：雖然是 admin，但如果啟用 "Include administrators"，也需要遵循規則
- ✅ **CI/CD 檢查**：所有 GitHub Actions 測試必須通過才能合併
- ❌ **Force Push**：不允許強制推送
- ❌ **Branch Deletion**：不允許刪除 master branch

## 驗證設定

設定完成後，可以透過以下方式驗證：

```bash
gh api repos/david2004kang/barcode-label-printer/branches/master/protection \
  --jq '.required_pull_request_reviews.required_approving_review_count'
```

應該返回：`1`

## 注意事項

1. **Repository Owner 權限**
   - 即使啟用 "Include administrators"，repository owner 在某些情況下仍可能可以直接 push
   - 如需完全限制，可能需要額外的 GitHub 設定

2. **CI/CD 檢查**
   - 確保所有 GitHub Actions workflows 都正常運作
   - 可以在 Branch Protection 設定中選擇特定的 status checks 作為必要檢查

3. **緊急修復**
   - 如果需要緊急修復，repository owner 可以暫時關閉保護規則
   - 或使用 `--force-with-lease`（不推薦，且可能被保護規則阻止）

## 當前保護狀態

查看當前保護規則：
**https://github.com/david2004kang/barcode-label-printer/settings/branches**
