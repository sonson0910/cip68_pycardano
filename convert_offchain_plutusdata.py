import json

def to_plutus_data(obj):
    """
    Chuyển một đối tượng Python (str, int, list, dict, ...) 
    thành 1 dict kiểu Plutus-JSON.
    
    Quy ước:
      - str -> {"bytes": "<hex of UTF-8>"}
      - int -> {"int": <number>}
      - list -> {"list": [to_plutus_data(x) for x in list]}
      - dict -> {"map": [ {"k":..., "v":...}, ... ] }
      - Nếu gặp kiểu không xác định -> convert sang str -> bytes
    """
    if isinstance(obj, str):
        return {"bytes": obj.encode("utf-8").hex()}
    elif isinstance(obj, int):
        return {"int": obj}
    elif isinstance(obj, list):
        return {
            "list": [to_plutus_data(item) for item in obj]
        }
    elif isinstance(obj, dict):
        # Mỗi key, value -> "k","v"
        arr = []
        for k, v in obj.items():
            arr.append({
                "k": to_plutus_data(k),
                "v": to_plutus_data(v)
            })
        return {"map": arr}
    else:
        # fallback: convert sang str -> bytes
        s = str(obj)
        return {"bytes": s.encode("utf-8").hex()}

def wrap_cip68_datum(metadata_dict, constructor=0, version=1):
    """
    Gói `metadata_dict` (python dict) thành 1 PlutusData JSON:
      {
        "constructor": <constructor>,
        "fields": [
          { "map": ... },  <-- metadata
          { "int": <version> }
        ]
      }
    """
    metadata_plutus = to_plutus_data(metadata_dict)  # => {"map":[...]}
    # Tạo object PlutusData CIP-68
    return {
        "constructor": constructor,
        "fields": [
            metadata_plutus,   # fields[0] = map
            {"int": version},  # fields[1] = version
        ]
    }
