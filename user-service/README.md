# User Service

### Build Proto Buf
```bash
# Build user.proto
cd app/buf/user
python -m grpc_tools.protoc -I ../../protos --python_out=. --pyi_out=. --grpc_python_out=. ../../protos/user.proto 
```

### VS Code Preference: Open User Settings (JSON)
```json
{
    "workbench.colorTheme": "Default Dark+",
    "editor.fontSize": 18,
    "editor.tabSize": 4,
    "editor.unicodeHighlight.invisibleCharacters": false,
    "typescript.updateImportsOnFileMove.enabled": "always",
    "javascript.updateImportsOnFileMove.enabled": "always",
    "[python]": {
      "editor.defaultFormatter": "ms-python.black-formatter",
      "editor.formatOnSave": true,
      "editor.codeActionsOnSave": {
          "source.organizeImports": "explicit"
      },
    },
    "isort.args":[
        "--profile", "black", "--settings-path=${workspaceFolder}/setup.cfg"
    ],
}
```