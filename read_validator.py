import json
from pycardano import PlutusV2Script
from pycardano.hash import ScriptHash

def read_validator(index: int = 0) -> dict:
    """
    Đọc file plutus.json, lấy validator thứ `index` trong mảng.
    Trả về dict chứa 'type', 'script_bytes', và 'script_hash'.
    """
    with open("plutus.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    validators = data.get("validators", [])
    if not validators:
        raise ValueError("No validators found in plutus.json.")

    if index < 0 or index >= len(validators):
        raise IndexError(f"Index {index} out of range. Available validators: 0..{len(validators) - 1}")

    validator_info = validators[index]
    compiled_code_hex = validator_info.get("compiledCode")
    hash_hex = validator_info.get("hash")

    if not compiled_code_hex or not hash_hex:
        raise ValueError(f"Validator at index {index} missing 'compiledCode' or 'hash'.")

    # Tạo PlutusV3Script
    script_bytes = PlutusV2Script(bytes.fromhex(compiled_code_hex))

    # Tạo ScriptHash từ hash hex
    script_hash = ScriptHash(bytes.fromhex(hash_hex))

    return {
        "type": "PlutusV2",
        "script_bytes": script_bytes,
        "script_hash": script_hash
    }
