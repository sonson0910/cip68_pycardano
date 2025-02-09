import json
from dataclasses import dataclass
from pycardano import PlutusData

from pycardano.plutus import PlutusData

@dataclass
class CIP68Datum(PlutusData):
    CONSTR_ID = 0  # Trùng với constructor trong JSON
    # Giả sử ta có 2 trường
    metadata: dict
    version: int

# Đọc file JSON "plutus_data.json"
with open("plutus_datum.json", "r") as f:
    raw_json = f.read()

# Gọi from_json trên CIP68Datum:
obj = CIP68Datum.from_json(raw_json)

print(obj)
print("metadata:", obj.metadata)
print("version:", obj.version)
