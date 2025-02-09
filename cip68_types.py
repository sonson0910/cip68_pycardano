from pycardano import PlutusData, PlutusMap, PlutusByteString, PlutusInteger

class MetaDatum(PlutusData):
    """
    CIP-68 datum: { metadata, version, extra }
    """
    constructor = 0
    metadata: PlutusData
    version: int
    extra: PlutusData

    def __init__(
        self,
        metadata: PlutusMap,
        version: PlutusInteger,
        extra: PlutusByteString
    ):
        self.metadata = metadata
        self.version = version
        self.extra = extra
