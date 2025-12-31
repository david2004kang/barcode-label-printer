# 發行到 PyPI 的說明

## 方法 1: 使用 PowerShell 腳本（推薦）

在 Windows PowerShell 中執行：

```powershell
.\publish_to_pypi.ps1
```

## 方法 2: 使用批次檔

在 Windows CMD 中執行：

```cmd
set PYPI_TOKEN=YOUR_PYPI_TOKEN_HERE
.\publish_to_pypi.bat
```

## 方法 3: 手動執行命令

1. 安裝建置工具：
```bash
python -m pip install --upgrade build twine
```

2. 建置套件：
```bash
python -m build
```

3. 檢查套件：
```bash
python -m twine check dist/*
```

4. 上傳到 PyPI：
```bash
python -m twine upload dist/* --username __token__ --password YOUR_PYPI_TOKEN_HERE
```

## 注意事項

1. **確保套件名稱唯一**：`barcode-label-printer` 必須在 PyPI 上可用
2. **版本號**：每次上傳需要更新 `pyproject.toml` 中的版本號
3. **測試上傳**：建議先上傳到 TestPyPI 測試：
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

## 更新版本

發行新版本時，記得：
1. 更新 `pyproject.toml` 中的 `version`
2. 更新 `barcode_label_printer/__init__.py` 中的 `__version__`
3. 提交變更到 git
4. 重新建置和上傳
