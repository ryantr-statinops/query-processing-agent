"""Infer sector-specific rule families from source schemas, never business IDs."""

from dataclasses import dataclass

from datamate.data.sources import Source, schema_key


@dataclass(frozen=True)
class SectorEvidence:
    sector: str
    score: int
    matched: tuple[str, ...]


_SIGNATURES = {
    "cafe": (("phongban", "sokhach", "phiphucvu", "size"),),
    "pharmacy": (("hoatchat", "sodangky", "solo", "hannsdung"),),
    "construction": (("ngaygiaohang", "dotgiao", "congtrinh"),),
    "baby_shop": (("voucher", "diemthuong", "ngaydangky", "size"),),
    "repair": (("bienso", "congviec", "phieubaohanh", "thoxuong"),),
    "phone_shop": (("imei", "tragop", "maycu", "baohanh"),),
}


def detect_sector(sources: list[Source], description: str = "") -> SectorEvidence | None:
    columns = {schema_key(column) for source in sources for column in source.columns}
    text = schema_key(description)
    scores = []
    for sector, signatures in _SIGNATURES.items():
        evidence = set()
        for signature in signatures:
            evidence.update(token for token in signature if token in columns)
        # README terms can resolve vendor-specific schemas whose headers are cryptic.
        if sector == "cafe" and "phucvu" in text:
            evidence.add("readme:phucvu")
        if sector == "pharmacy" and "hoatchat" in text:
            evidence.add("readme:hoatchat")
        if sector == "construction" and "dotgiao" in text:
            evidence.add("readme:dotgiao")
        if sector == "baby_shop" and "diemthuong" in text:
            evidence.add("readme:diemthuong")
        if sector == "repair" and "bienso" in text:
            evidence.add("readme:bienso")
        if sector == "phone_shop" and "imei" in text:
            evidence.add("readme:imei")
        if evidence:
            scores.append(SectorEvidence(sector, len(evidence), tuple(sorted(evidence))))
    if not scores:
        return None
    scores.sort(key=lambda item: (-item.score, item.sector))
    if len(scores) > 1 and scores[0].score == scores[1].score:
        return None
    return scores[0]
