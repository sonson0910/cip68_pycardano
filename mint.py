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
    InlineDatum,
    PlutusData,
)
from cip68_types import MetaDatum  # class MetaDatum có extra
from common import load_plutus_scripts, get_script_hash

# 1. Kết nối
BF_PROJECT_ID = os.environ.get("preprod06dzhzKlynuTInzvxHDH5cXbdHo524DE")
context = BlockFrostChainContext(BF_PROJECT_ID, network=Network.TESTNET)

# 2. Key
issuer_skey = PaymentSigningKey.load("me.skey")
v_key = PaymentVerificationKey(issuer_skey.public_key)
issuer_address = Address(v_key.hash(), network=Network.TESTNET)

# 3. Nạp scripts
scripts = load_plutus_scripts("plutus.json")
mint_script = scripts["minter.params"] 
mint_policy_id = get_script_hash(mint_script)

store_script = scripts["cip68.params"]
from pycardano import ScriptHash
store_script_hash = ScriptHash(store_script)
store_script_address = Address(script_hash=store_script_hash, network=Network.TESTNET)

# 4. Token name
prefix_ref = bytes.fromhex("0100AABB")
prefix_user = bytes.fromhex("0222CCDD")
suffix_28   = bytes.fromhex("e80f65697e1332fbb75f5a4a0927f5856ade4df76b64bd762a2f6")
ref_token_name = prefix_ref + suffix_28
user_token_name = prefix_user + suffix_28

# 5. Tạo MetaDatum (có extra)
with open('metadata_nft.json', 'r') as file:
    data = json.load(file)

metadata = PlutusData.from_json()
metadata_map = PlutusMap({
    PlutusByteString(b"name"): PlutusByteString(b"My CIP-68 NFT"),
    PlutusByteString(b"description"): PlutusByteString(b"Minted by PyCardano"),
})
version = PlutusInteger(1)
extra_field = PlutusByteString(b"Example Extra Data!")  # bytes

datum_obj = MetaDatum(
    metadata=metadata_map,
    version=version,
    extra=extra_field
)

inline_datum = InlineDatum(datum_obj)

# 6. Build Tx
builder = TransactionBuilder(context)

# Lấy UTxO issuer để trả phí
issuer_utxos = context.utxos(str(issuer_address))
if not issuer_utxos:
    raise Exception("No UTxO for issuer.")
builder.add_input(issuer_utxos[0])

# Mint 2 token
from pycardano import Redeemer
redeemer_mint = Redeemer(
    data=0,  # 0 => 'MintTokens' constructor
    tag=RedeemerTag.MINT
)
mint_assets = Asset({
    AssetName(ref_token_name): 1,
    AssetName(user_token_name): 1
})
builder.mint = [(mint_assets, mint_script, redeemer_mint)]

# Output 1: user token -> issuer 
val_user = Value(2_000_000, {mint_policy_id: Asset({AssetName(user_token_name): 1})})
out_user = TransactionOutput(issuer_address, val_user)
builder.add_output(out_user)

# Output 2: ref token -> script, kèm inline datum CIP-68 (có extra)
val_ref = Value(2_000_000, {mint_policy_id: Asset({AssetName(ref_token_name): 1})})
out_ref = TransactionOutput(store_script_address, val_ref, datum=inline_datum)
builder.add_output(out_ref)

# Xây, ký, submit
tx = builder.build(change_address=issuer_address)
signed_tx = tx.sign([issuer_skey])
tx_id = context.submit_tx(signed_tx)
print("Mint CIP-68 w/ extra =>", tx_id)
