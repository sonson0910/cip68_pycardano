from pycardano import PlutusData

class MetaDatum(PlutusData):
    """
    CIP-68 datum: { metadata, version, extra }
    """
    CONSTR_ID = 0,
    metadata: dict
    version: int
    extra: bytes

    def __init__(
        self,
        metadata: dict,
        version: int,
        extra: bytes
    ):
        self.metadata = metadata
        self.version = version
        self.extra = extra
