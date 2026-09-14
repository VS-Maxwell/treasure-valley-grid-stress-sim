#!/usr/bin/env python3
"""Build directed dam-to-outlet paths from preserved NLDI and NHDPlusV2 sources."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path
from typing import Iterator


OUTLET_COMID = 24193082
CLASS_CODES = {
    "unresolved-no-indexed-catchment": -1.0,
    "nearby-not-upstream-of-outlet": 0.0,
    "upstream-connected-to-snake-at-weiser": 1.0,
    "unresolved-network-gap": -2.0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def dbf_rows(path: Path, selected_names: set[str]) -> Iterator[dict[str, str]]:
    with path.open("rb") as handle:
        header = handle.read(32)
        if len(header) != 32:
            raise ValueError(f"{path.name} has a truncated DBF header")
        record_count = struct.unpack_from("<I", header, 4)[0]
        header_length, record_length = struct.unpack_from("<HH", header, 8)
        descriptor_bytes = handle.read(header_length - 33)
        terminator = handle.read(1)
        if terminator != b"\r" or len(descriptor_bytes) % 32:
            raise ValueError(f"{path.name} has an invalid DBF field header")
        fields: list[tuple[str, int, int]] = []
        offset = 1
        for index in range(0, len(descriptor_bytes), 32):
            descriptor = descriptor_bytes[index : index + 32]
            name = descriptor[:11].split(b"\0", 1)[0].decode("ascii").upper()
            length = descriptor[16]
            if name in selected_names:
                fields.append((name, offset, length))
            offset += length
        if {field[0] for field in fields} != selected_names:
            raise ValueError(f"{path.name} lacks requested fields {selected_names}")
        if offset != record_length:
            raise ValueError(f"{path.name} DBF record length does not balance")
        for _ in range(record_count):
            record = handle.read(record_length)
            if len(record) != record_length:
                raise ValueError(f"{path.name} has a truncated DBF record")
            if record[:1] == b"*":
                continue
            yield {
                name: record[start : start + length].decode("ascii").strip()
                for name, start, length in fields
            }


def parse_integer(value: str) -> int | None:
    if not value:
        return None
    parsed = int(float(value))
    return parsed if parsed > 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dam_table", type=Path)
    parser.add_argument("dam_comid_receipt", type=Path)
    parser.add_argument("network_receipt", type=Path)
    parser.add_argument("upstream_geojson", type=Path)
    parser.add_argument("plus_flow_dbf", type=Path)
    parser.add_argument("plus_flowline_vaa_dbf", type=Path)
    parser.add_argument("output_table", type=Path)
    parser.add_argument("output_manifest", type=Path)
    parser.add_argument("output_binary", type=Path)
    args = parser.parse_args()

    dam_table = json.loads(args.dam_table.read_text(encoding="utf-8"))
    dam_records = dam_table.get("records")
    if not isinstance(dam_records, list) or len(dam_records) != 647:
        raise ValueError("Expected the immutable 647-record NID v2 table")
    comid_receipt = json.loads(args.dam_comid_receipt.read_text(encoding="utf-8"))
    if (
        comid_receipt.get("status") != "original-api-responses-verified"
        or comid_receipt.get("processed_dam_count") != len(dam_records)
    ):
        raise ValueError("Dam COMID receipt is incomplete")
    network_receipt = json.loads(args.network_receipt.read_text(encoding="utf-8"))
    if (
        network_receipt.get("target_receiving_system", {}).get("outlet_comid")
        != OUTLET_COMID
    ):
        raise ValueError("Network receipt does not identify the accepted outlet")

    upstream_payload = json.loads(args.upstream_geojson.read_text(encoding="utf-8"))
    upstream_comids = {
        int(feature["properties"]["nhdplus_comid"])
        for feature in upstream_payload.get("features", [])
    }
    if (
        len(upstream_comids) != network_receipt.get("upstream_flowline_count")
        or OUTLET_COMID not in upstream_comids
    ):
        raise ValueError("Upstream COMID set does not match the network receipt")

    reverse_edges: dict[int, list[int]] = collections.defaultdict(list)
    edge_set: set[tuple[int, int]] = set()
    for row in dbf_rows(args.plus_flow_dbf, {"FROMCOMID", "TOCOMID"}):
        source = parse_integer(row["FROMCOMID"])
        target = parse_integer(row["TOCOMID"])
        if source is None or target is None:
            continue
        if source in upstream_comids and target in upstream_comids:
            edge = (source, target)
            if edge not in edge_set:
                edge_set.add(edge)
                reverse_edges[target].append(source)

    next_to_outlet: dict[int, int] = {}
    queue: collections.deque[int] = collections.deque([OUTLET_COMID])
    visited = {OUTLET_COMID}
    while queue:
        target = queue.popleft()
        for source in sorted(reverse_edges.get(target, [])):
            if source in visited:
                continue
            visited.add(source)
            next_to_outlet[source] = target
            queue.append(source)

    lengths_km: dict[int, float] = {}
    for row in dbf_rows(args.plus_flowline_vaa_dbf, {"COMID", "LENGTHKM"}):
        comid = parse_integer(row["COMID"])
        if comid in visited and row["LENGTHKM"]:
            lengths_km[comid] = float(row["LENGTHKM"])

    comid_by_provider = {
        record["provider_record_id"]: record
        for record in comid_receipt.get("records", [])
    }
    if len(comid_by_provider) != len(dam_records):
        raise ValueError("Dam COMID records are not unique and complete")

    output_records = []
    packed = bytearray()
    counts = collections.Counter()
    connected_hydroelectric = 0
    for dam in dam_records:
        evidence = comid_by_provider[dam["provider_record_id"]]
        comid = evidence.get("comid")
        path: list[int] = []
        if comid is None:
            classification = "unresolved-no-indexed-catchment"
        elif comid not in upstream_comids:
            classification = "nearby-not-upstream-of-outlet"
        elif comid not in visited:
            classification = "unresolved-network-gap"
        else:
            classification = "upstream-connected-to-snake-at-weiser"
            current = int(comid)
            path.append(current)
            while current != OUTLET_COMID:
                if current not in next_to_outlet:
                    raise ValueError(f"Path from COMID {comid} ended before the outlet")
                current = next_to_outlet[current]
                path.append(current)
                if len(path) > len(upstream_comids):
                    raise ValueError(f"Path from COMID {comid} contains a cycle")
            if any((left, right) not in edge_set for left, right in zip(path, path[1:])):
                raise ValueError(f"Path from COMID {comid} contains a missing edge")
            if dam.get("hydroelectric_purpose"):
                connected_hydroelectric += 1
        counts[classification] += 1
        path_text = ",".join(str(value) for value in path).encode("ascii")
        path_length_km = sum(lengths_km.get(value, 0.0) for value in path)
        output_record = dict(dam)
        output_record["watershed_path"] = {
            "classification": classification,
            "start_comid": comid,
            "outlet_comid": OUTLET_COMID if path else None,
            "path_edge_count": max(0, len(path) - 1),
            "path_length_km": round(path_length_km, 6) if path else None,
            "path_sha256": hashlib.sha256(path_text).hexdigest() if path else None,
            "path_comids": path,
            "position_receipt_sha256": evidence["sha256"],
            "position_http_status": evidence["http_status"],
        }
        output_records.append(output_record)
        packed.extend(
            struct.pack(
                "<ffff",
                float(dam["longitude"]),
                float(dam["latitude"]),
                1.0 if dam.get("hydroelectric_purpose") else 0.0,
                CLASS_CODES[classification],
            )
        )

    args.output_binary.parent.mkdir(parents=True, exist_ok=True)
    args.output_binary.write_bytes(packed)
    binary_hash = sha256(args.output_binary)
    table = {
        "schema_version": 1,
        "id": "usace-nid-snake-plain-dams-directed-v3",
        "truth_state": "observed-plus-network-derived",
        "source_dam_table": str(args.dam_table),
        "source_dam_table_sha256": sha256(args.dam_table),
        "dam_comid_receipt": str(args.dam_comid_receipt),
        "dam_comid_receipt_sha256": sha256(args.dam_comid_receipt),
        "network_receipt": str(args.network_receipt),
        "network_receipt_sha256": sha256(args.network_receipt),
        "target_outlet": {
            "nwis_site_id": "USGS-13269000",
            "outlet_comid": OUTLET_COMID,
            "name": "Snake River at Weiser ID",
        },
        "dam_count": len(output_records),
        "classification_counts": dict(sorted(counts.items())),
        "connected_hydroelectric_purpose_count": connected_hydroelectric,
        "network": {
            "nldi_upstream_comid_count": len(upstream_comids),
            "plusflow_edge_count_in_upstream_set": len(edge_set),
            "comids_with_verified_path_to_outlet": len(visited),
        },
        "records": output_records,
        "limitations": [
            "Connected means an NHDPlusV2 directed surface-water path reaches USGS-13269000; it does not prove a dam supplies Treasure Valley users.",
            "NHDPlus catchment assignment uses the published USACE NID point without positional correction.",
            "Hydroelectric purpose does not establish generator capacity or electrical interconnection; EIA matching remains separate.",
            "The NLDI upstream navigation uses an explicit 1500-kilometer bound and whole-reach indexing near the outlet.",
        ],
    }
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    args.output_table.write_text(
        json.dumps(table, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )
    table_hash = sha256(args.output_table)
    manifest = {
        "schema_version": 1,
        "id": "usace-nid-snake-plain-dam-points-v3",
        "truth_state": "observed-plus-network-derived",
        "normalized_table": str(args.output_table),
        "normalized_table_sha256": table_hash,
        "network_receipt": str(args.network_receipt),
        "network_receipt_sha256": sha256(args.network_receipt),
        "target_outlet": table["target_outlet"],
        "bbox_epsg_4326": dam_table["bbox_epsg_4326"],
        "dam_count": len(output_records),
        "hydroelectric_purpose_count": dam_table["hydroelectric_purpose_count"],
        "connected_dam_count": counts["upstream-connected-to-snake-at-weiser"],
        "connected_hydroelectric_purpose_count": connected_hydroelectric,
        "outside_dam_count": counts["nearby-not-upstream-of-outlet"],
        "unresolved_dam_count": (
            counts["unresolved-no-indexed-catchment"]
            + counts["unresolved-network-gap"]
        ),
        "connectivity_state": "directed-network-resolved-to-usgs-13269000",
        "binary": {
            "file": args.output_binary.name,
            "bytes": len(packed),
            "sha256": binary_hash,
            "encoding": "little-endian-float32",
            "stride": 4,
            "order": "longitude-latitude-hydroelectric-purpose-flag-connectivity-code",
            "connectivity_codes": {
                "1": "upstream-connected-to-snake-at-weiser",
                "0": "nearby-not-upstream-of-outlet",
                "-1": "unresolved-no-indexed-catchment",
                "-2": "unresolved-network-gap",
            },
        },
        "limitations": table["limitations"],
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(
        json.dumps(manifest, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        "Built directed dam paths: "
        + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())),
        flush=True,
    )
    print(
        f"Graph covers {len(visited)}/{len(upstream_comids)} upstream COMIDs; "
        f"binary {len(packed)} bytes; table SHA-256 {table_hash}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
