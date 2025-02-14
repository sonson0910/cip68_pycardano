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
)
from cip68_types import MetaDatum  # class MetaDatum với trường: metadata, version, extra
from common import get_script_hash
from cip68_utils import to_unit, get_unique_asset_name_suffix
from read_plutusdata import CIP68Datum
from convert_offchain_plutusdata import wrap_cip68_datum
from context import get_chain_context
from read_validator import read_validator

# 1. Kết nối network
context = get_chain_context()  # Hàm bạn đã định nghĩa, trả về BlockFrostChainContext

# 2. Tải signing key, tạo địa chỉ issuer
issuer_skey = PaymentSigningKey.load("me.sk")
issuer_vkey = PaymentVerificationKey.from_signing_key(issuer_skey)
issuer_address = Address(issuer_vkey.hash(), network=Network.TESTNET)

# 3. Nạp scripts:
#    - index=1 => mint script
#    - index=0 => CIP68 store script
validator_minter = read_validator(index=1)
validator_cip68 = read_validator(index=0)

mint_script = validator_minter["script_bytes"]
policy_id = get_script_hash(mint_script)

store_script_hash = validator_cip68["script_hash"]
store_script_address = Address(payment_part=store_script_hash, network=Network.TESTNET)

# 4. Tạo tên token (prefix + suffix)
#    Giả sử ta tạo 1 UTxO 2_000_000 (ảo) để "lấy outputIndex"
#    Hoặc bạn chọn 1 UTxO thực. 
REQUIRED_LOVELACE = 5_000_000

# Lấy tất cả UTxO
utxos = context.utxos(str(issuer_address))
print("All UTxOs:\n", utxos)

chosen_utxo = None

# Duyệt qua từng UTxO, tìm UTxO có coin >= REQUIRED_LOVELACE
for utxo in utxos:
    # Lượng lovelace của UTxO này:
    coin_amount = utxo.output.amount.coin  # Số lovelace
    if coin_amount >= REQUIRED_LOVELACE:
        chosen_utxo = utxo
        break  # Tìm được 1 UTxO thỏa mãn, thì dừng

if chosen_utxo is None:
    raise Exception(f"Không tìm thấy UTxO đủ {REQUIRED_LOVELACE} lovelace!")
else:
    print("Chọn UTxO để trả phí:", chosen_utxo)

asset_suffix = get_unique_asset_name_suffix(chosen_utxo).hex()

#    Tham số (policy_id, suffix, label) -> user to_unit
#    Ở đây: "ebe9d0..." là 1 policy cũ? Có vẻ code cũ. 
#    Thực tế, policy_id = policy_id (vừa tính)
#    => Chúng ta thay "ebe9d0..." = policy_id
refNFT = to_unit(policy_id, asset_suffix, 100)    # prefix_100
userNFT = to_unit(policy_id, asset_suffix, 222)   # prefix_222

# 5. Tạo MetaDatum (có extra) từ file metadata_nft.json
with open('metadata_nft.json', 'r') as file:
    data = json.load(file)

# 5.1. Chuyển JSON off-chain -> Plutus JSON
cip68_data = wrap_cip68_datum(data, constructor=0, version=1)
# 5.2. Parse thành CIP68Datum
#     Lưu ý: CIP68Datum cần CONSTR_ID=0
metadata_cip68 = CIP68Datum.from_json(json.dumps(cip68_data))

# 5.3. Gói trong MetaDatum 
#     (MetaDatum có field: metadata, version, extra)
datum_obj = MetaDatum(
    metadata=metadata_cip68,
    version=1,
    extra=b""
)

# 6. Xây transaction
builder = TransactionBuilder(context)

# 6.1. Lấy UTxO issuer để trả phí
issuer_utxos = context.utxos(str(issuer_address))
if not issuer_utxos:
    raise Exception("No UTxO for issuer.")
builder.add_input(issuer_utxos[0])  # Chọn UTxO đầu (hoặc logic selection)

# 6.2. Mint 2 token (refNFT, userNFT)
mint_assets = Asset({
    AssetName(refNFT): 1,
    AssetName(userNFT): 1
})

redeemer_mint = Redeemer(
    data=0,  # 0 => 'MintTokens' (theo logic CIP-68)
    tag=RedeemerTag.MINT
)

builder.mint = [(mint_assets, mint_script, redeemer_mint)]

# 7. Output #1: Gửi user token -> issuer
val_user = Value(2_000_000, {policy_id: Asset({AssetName(userNFT): 1})})
out_user = TransactionOutput(issuer_address, val_user)
builder.add_output(out_user)

# 8. Output #2: Gửi ref token -> store script, kèm "inline datum"
val_ref = Value(2_000_000, {policy_id: Asset({AssetName(refNFT): 1})})
out_ref = TransactionOutput(
    address=store_script_address,
    amount=val_ref,
    datum=datum_obj  # "inline datum" PyCardano >= 0.3
)
builder.add_output(out_ref)

# 9. Build, sign, submit
tx = builder.build(change_address=issuer_address)
signed_tx = tx.sign([issuer_skey])
tx_id = context.submit_tx(signed_tx)
print("Mint CIP-68 with extra =>", tx_id)
