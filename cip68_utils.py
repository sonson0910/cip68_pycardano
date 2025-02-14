def to_label(label: int) -> str:
    """
    Chuyển một số nguyên thành chuỗi hexa (bỏ tiền tố 0x).
    """
    return hex(label)[2:]

def to_unit(policy_id: str, name: str = None, label: int = None) -> str:
    """
    Tương đương với hàm toUnit trong JavaScript.
    - policy_id: chuỗi policy id (yêu cầu độ dài 56).
    - name: tên tài sản (string).
    - label: một số (int) sẽ được chuyển sang định dạng hex.

    Trả về chuỗi policy_id + hex_label + name.
    """
    hex_label = to_label(label) if isinstance(label, int) else ""
    n = name if name is not None else ""

    # Kiểm tra độ dài n + hex_label không vượt quá 64 (32 bytes)
    if len(n + hex_label) > 64:
        raise ValueError("Asset name size exceeds 32 bytes.")

    # Kiểm tra policyId có độ dài đúng 56
    if len(policy_id) != 56:
        raise ValueError(f"Policy id invalid: {policy_id}.")

    return policy_id + hex_label + n


import hashlib

def get_unique_asset_name_suffix(utxo: dict) -> bytes:
    # 1. Lấy transaction_id (dạng hex)
    tx_hash_hex = utxo.input.transaction_id.payload.hex()  # hoặc str(utxo.input.transaction_id)

    # 2. index
    index = utxo.input.index

    # 3. logic băm => 28 bytes
    import hashlib
    sha3 = hashlib.sha3_256(bytes.fromhex(tx_hash_hex)).digest()  # 32 bytes
    first_27 = sha3[:27]

    if index > 255:
        raise ValueError(f"output index {index} > 255, không fit CIP-68 1 byte")

    index_byte = index.to_bytes(1, 'big')
    suffix_28 = index_byte + first_27  # total 28 bytes
    return suffix_28


# Ví dụ sử dụng:
# Giả sử utxo = {
#   "txHash": "abcdef123456...",
#   "outputIndex": 1
# }
# result = get_unique_asset_name_suffix(utxo)
# print(result)
