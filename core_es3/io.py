from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from es3_modifier import ES3
from es3_modifier.main import decrypt_aes_128_cbc, InvalidDataException

if TYPE_CHECKING:
    from pathlib import Path

@dataclass
class ES3Backend:
    key: str
    _original_data: bytes = field(default=b"", init=False)

    def _fix_json_syntax(self, json_str: str) -> str:
        """Fix common JSON syntax issues in ES3 save files"""
        
        fixed = json_str
        if '"value" : {' in fixed and ':14,' in fixed:
            import re as re_module
            pattern = r'"value" : \{([^}]+)\}'
            matches = re_module.findall(pattern, fixed)
            for match in matches:
                fixed_content = re_module.sub(r'(\d+):', r'"\1":', match)
                original = f'"value" : {{{match}}}'
                replacement = f'"value" : {{{fixed_content}}}'
                fixed = fixed.replace(original, replacement, 1)
        lines = fixed.split('\n')
        for i, line in enumerate(lines):
            if '{' in line and ':' in line and not line.strip().startswith('"'):
                while re.search(r'\{(\d+):', line):
                    line = re.sub(r'\{(\d+):', r'{"\1":', line)
                while re.search(r',(\d+):', line):
                    line = re.sub(r',(\d+):', r',"\1":', line)
                lines[i] = line
        
        fixed = '\n'.join(lines)
        fixed = re.sub(r'(\{\s*)(?!"[^"]*")([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r'(\,\s*)(?!"[^"]*")([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r'(\{)(\d+)(:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r'(,)(\d+)(:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r'(\{\s*)(?!"[^"]*")([^{}\s:"]+)(\s*:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r'(\,\s*)(?!"[^"]*")([^{}\s:"]+)(\s*:)', r'\1"\2"\3', fixed)
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        fixed = re.sub(r'("[^"]+"\s*:\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*[,\}])', r'\1"\2"\3', fixed)
        fixed = fixed.replace("'", '"')
        fixed = re.sub(r'""([^"]+)""', r'"\1"', fixed)

        return fixed

    def load_bytes(self, data: bytes) -> dict[str, Any]:
        self._original_data = data
        
        try:
            decrypted = decrypt_aes_128_cbc(data, self.key)
            decoded = decrypted.decode('utf-8')

            try:
                return json.loads(decoded)
            except json.JSONDecodeError as e:
                fixed_json = self._fix_json_syntax(decoded)

                try:
                    return json.loads(fixed_json)

                except json.JSONDecodeError as e2:
                    raise InvalidDataException(f'Decrypted data was not in a valid ES3 format. JSON parsing failed at line {e.lineno}, column {e.colno}: {e.msg}') from e

        except Exception as e:
            raise InvalidDataException(f'Decrypted data was not in a valid ES3 format. Error: {e}') from e

    def save_bytes(self, payload: dict[str, Any]) -> bytes:
        if not self._original_data:
            raise RuntimeError("No original data loaded before save.")
        
        try:
            decrypted = decrypt_aes_128_cbc(self._original_data, self.key)
            original_json_str = decrypted.decode('utf-8')
            new_values = {}
            if 'PlayersMoney' in payload:
                new_values['PlayersMoney'] = payload['PlayersMoney']
            if 'Experience' in payload:
                new_values['Experience'] = payload['Experience']
            modified_json_str = original_json_str
            for key, new_value in new_values.items():
                flexible_pattern = f'"{key}"[^:]*:[^{{]*{{[^}}]*"value"[^:]*:[^0-9]*([0-9]+)'
                match = re.search(flexible_pattern, modified_json_str)
                if match:
                    old_value = match.group(1)
                    modified_json_str = modified_json_str.replace(old_value, str(new_value["value"]))

            es3 = ES3(self._original_data, self.key)
            return es3.save(modified_json_str)
            
        except Exception as e:
            es3 = ES3(self._original_data, self.key)
            raw_json = json.dumps(payload)
            return es3.save(raw_json)

    def load_from_file(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"Save file not found: {path}")
        data = path.read_bytes()
        return self.load_bytes(data)

    def save_to_file(self, path: Path, payload: dict[str, Any]) -> None:
        if path.exists():
            backup_name = f"{path.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            backup_path = path.with_name(backup_name)
            backup_path.write_bytes(path.read_bytes())

        data = self.save_bytes(payload)
        path.write_bytes(data)
