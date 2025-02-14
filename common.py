# common.py

import json
import os
from pycardano import PlutusV2Script, script_hash  # <-- import script_hash
from pycardano.hash import ScriptHash

def load_plutus_scripts(
    plutus_json_path: str = "plutus.json"
) -> dict[str, PlutusV2Script]:
    """
    Đọc file plutus.json, trả về dict { 'title': PlutusV2Script }.
    """
    with open(plutus_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validators = data.get("validators", [])
    if not validators:
        raise Exception("No 'validators' found in plutus.json")

    scripts_dict = {}
    for v in validators:
        title = v.get("title")
        cbor_hex = v.get("compiledCode")
        if not title or not cbor_hex:
            continue
        # 1. Chuyển hex -> bytes
        cbor_bytes = bytes.fromhex(cbor_hex)
        # 2. Tạo PlutusV2Script object
        plutus_script = PlutusV2Script(cbor_bytes)
        # Lưu vào dict
        scripts_dict[title] = plutus_script

    return scripts_dict

def get_script_hash(script: PlutusV2Script) -> str:
    """
    Trả về policy id hoặc script hash dưới dạng hex.
    script là đối tượng PlutusV2Script (cbor bytes).
    Sử dụng script_hash(...) để tính băm.
    """
    shash = script_hash(script)  # Tính hash từ nội dung script
    return shash.payload.hex()
