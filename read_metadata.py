import json
from pycardano import PlutusData
from convert_offchain_plutusdata import wrap_cip68_datum

with open('metadata_nft.json', 'r') as file:
    data = json.load(file)

cip68_data = wrap_cip68_datum(data, constructor=0, version=1)

print(cip68_data)

with open("plutus_datum.json","w") as f:
    json.dump(cip68_data, f, indent=2)

# print(data)
# metadata = PlutusData.from_json(json.dumps(cip68_data))
# print(metadata)

