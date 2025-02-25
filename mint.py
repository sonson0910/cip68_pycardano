#!/usr/bin/env python3

import os
import json
from pycardano import (
    BlockFrostChainContext,
    Network,
    Address,
    PaymentVerificationKey,
    PaymentSigningKey,
    TransactionBuilder,
    TransactionOutput,
    Value,
    Asset,
    AssetName,
    Redeemer,
    RedeemerTag,
    PlutusData,
    ScriptHash,
    # Một số lớp khác nếu cần
)
from cip68_types import MetaDatum  # class MetaDatum với trường: metadata, version, extra
from common import get_script_hash
from cip68_utils import get_unique_asset_name_suffix
from read_plutusdata import CIP68Datum
from convert_offchain_plutusdata import wrap_cip68_datum
from context import get_chain_context
from read_validator import read_validator


# 1) Kết nối network
context = get_chain_context()  # Hàm bạn đã định nghĩa, trả về BlockFrostChainContext

# 2) Tải signing key, tạo địa chỉ issuer
issuer_skey = PaymentSigningKey.load("me.sk")
issuer_vkey = PaymentVerificationKey.from_signing_key(issuer_skey)
issuer_address = Address(issuer_vkey.hash(), network=Network.TESTNET)

# 3) Nạp scripts (index=1 => mint script, index=0 => CIP68 store script)
validator_minter = read_validator(index=1)
validator_cip68 = read_validator(index=0)

# 3.1) Lấy Plutus script (cbor) & policy_id
mint_script = validator_minter["script_bytes"]       # PlutusV2Script
policy_id_str = get_script_hash(mint_script)         # Chuỗi hex (56 ký tự)
policy_id_obj = ScriptHash.from_primitive(bytes.fromhex(policy_id_str))
#  => policy_id_obj là ScriptHash (28 bytes)

# 3.2) Địa chỉ script CIP-68
store_script_hash_obj = validator_cip68["script_hash"]  
# Kiểm tra xem read_validator() trả về "script_hash" loại gì:
#  - Nếu là chuỗi hex => store_script_hash_obj = ScriptHash.from_primitive(bytes.fromhex(validator_cip68["script_hash"]))
#  - Nếu đã là ScriptHash => dùng trực tiếp.

# Ở PyCardano cũ, phải dùng Address.from_script_hash(...) thay vì Address(..., script_hash=?)
store_script_address = Address(payment_part=store_script_hash_obj, network=Network.TESTNET)

# 4) Tạo tên token (prefix + suffix)
REQUIRED_LOVELACE = 10_000_000

# Chọn UTxO để trả phí
utxos = context.utxos(str(issuer_address))
chosen_utxo = None
for utxo in utxos:
    if utxo.output.amount.coin >= REQUIRED_LOVELACE:
        chosen_utxo = utxo
        break

if not chosen_utxo:
    raise Exception(f"Không tìm thấy UTxO >= {REQUIRED_LOVELACE} lovelace!")
print("Chọn UTxO để trả phí:", chosen_utxo)

# Tạo suffix 28 bytes => hex
asset_suffix = get_unique_asset_name_suffix(chosen_utxo).hex()

# 4.1) prefix -> 4 bytes => 8 hex => ghép suffix 56 hex => 64 hex => 32 bytes
prefix_ref_hex  = "000643b0"  # 4 bytes => 8 hex
prefix_user_hex = "000de140"

ref_hex  = prefix_ref_hex  + asset_suffix  # => 64 hex => 32 bytes
user_hex = prefix_user_hex + asset_suffix

refNFT_bytes  = bytes.fromhex(ref_hex)
userNFT_bytes = bytes.fromhex(user_hex)

if len(refNFT_bytes) != 32 or len(userNFT_bytes) != 32:
    raise ValueError("Asset name must be 32 bytes")

refNFT  = AssetName(refNFT_bytes)
userNFT = AssetName(userNFT_bytes)

# 5) Tạo MetaDatum CIP-68 (có extra)
with open("metadata_nft.json", "r", encoding="utf-8") as file:
    data = json.load(file)

cip68_data = wrap_cip68_datum(data, constructor=0, version=1)
metadata_cip68 = CIP68Datum.from_json(json.dumps(cip68_data)).to_dict()


datum_obj = MetaDatum(
    metadata=metadata_cip68,
    version=1,
    extra=b""
)

# 6) Xây transaction
builder = TransactionBuilder(context)

# 6.1) Add 1 UTxO issuer trả phí
builder.add_input(chosen_utxo)

# 6.2) Tạo 2 token CIP-68 => 1 ref token, 1 user token
mint_assets = Asset()
mint_assets[refNFT] = 1
mint_assets[userNFT] = 1

redeemer_mint = Redeemer(0)              # data=0 (MintAction::Mint)
redeemer_mint.tag = RedeemerTag.MINT     # => MINT
# Optionally: redeemer_mint.index = 0     # Thường index=0

# 6.3) Gán builder.mint = MultiAsset
#      => key = policy_id_obj (ScriptHash), value=Asset()
my_multi_asset = Asset()
my_multi_asset[refNFT]  = 1
my_multi_asset[userNFT] = 1

from pycardano import MultiAsset
my_nft = MultiAsset()
my_nft[policy_id_obj] = my_multi_asset

builder.mint = my_nft

# 6.4) Thêm minting script + redeemer
builder.add_minting_script(
    script=mint_script,       # PlutusV2Script cbor
    redeemer=redeemer_mint
)

# 7) Output #1: user token -> issuer address
#    => 1 userNFT
val_user = Value(2_000_000, {policy_id_obj: Asset({userNFT: 1})})
out_user = TransactionOutput(issuer_address, val_user)
builder.add_output(out_user)

# 8) Output #2: ref token -> store script, kèm inline datum
val_ref = Value(2_000_000, {policy_id_obj: Asset({refNFT: 1})})
out_ref = TransactionOutput(
    address=store_script_address,
    amount=val_ref,
    datum=datum_obj
)
builder.add_output(out_ref)

# 9) Build, sign, submit
tx = builder.build(change_address=issuer_address)
signed_tx = tx.sign([issuer_skey])
tx_id = context.submit_tx(signed_tx)
print("Mint CIP-68 =>", tx_id)
