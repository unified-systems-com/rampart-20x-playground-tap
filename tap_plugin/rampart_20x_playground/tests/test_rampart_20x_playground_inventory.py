"""The inventory build, read from the bundles as written (`req-rampart-20x-playground-inventory-*`).

These tests read the JSON files only, so they hold what the bundles declare, not what a grid returns:
that the nine tables exist and are wired, that every entity carries one valid `inventory` value, that no
secret material is recorded. What a table shows once imported is checked in the browser."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"

CATEGORIES = ("applications", "libraries", "packages", "os", "containers", "crypto", "secrets", "cloud", "saas")
# The panel slot (page `panel-id`) of each table, in page order.
SLOTS = {
    "applications": "applications",
    "libraries": "libraries",
    "packages": "packages",
    "os": "operating-systems",
    "containers": "containers",
    "crypto": "crypto",
    "secrets": "secrets",
    "cloud": "cloud-services",
    "saas": "saas",
}
# Conceptual containers and instances: no row anywhere (`-tables`, `-cloud`, `-rows`).
SOFTWARE = "inventory-software.grift.json"
# The page order of the tables (George, 2026-10-14).
PAGE_ORDER = (
    "applications", "libraries", "packages", "operating-systems", "containers", "crypto", "secrets",
    "cloud-services", "saas",
)
# The official edges the software bundle may use, with the node types each joins.
SOFTWARE_EDGES = {
    "INSTALLS_PACKAGE__computing_core": ({"computing_core__host"}, {"computing_core__package"}),
    "RUNS_OPERATING_SYSTEM__computing_core": ({"computing_core__host"}, {"computing_core__operating_system"}),
    "LOADS_LIBRARY__computing_core": ({"computing_core__program"}, {"computing_core__library"}),
    "CARRIES_CRYPTO_PROVIDER__computing_core": (
        {"computing_core__library", "computing_core__package", "computing_core__program"},
        {"computing_core__crypto_provider"},
    ),
    # The three the parser emits from the SBOM (`parse_cyclonedx`).
    "REQUIRES_PACKAGE__computing_core": ({"computing_core__package"}, {"computing_core__package"}),
    "DERIVES_FROM_SOURCE_PACKAGE__computing_core": (
        {"computing_core__package"},
        {"computing_core__source_package"},
    ),
    "DESCRIBES_HOST__computing_core": ({"computing_core__sbom_document"}, {"computing_core__host"}),
}
# The `inventory` value of each software node type.
SOFTWARE_CATEGORY = {
    "computing_core__package": "packages",
    "computing_core__library": "libraries",
    "computing_core__operating_system": "os",
    "computing_core__crypto_provider": "crypto",
    "computing_core__host": "containers",
}
# The types the SBOM adds: no table shows them, so they carry no `inventory` value.
SBOM_ONLY_TYPES = {"computing_core__source_package", "computing_core__sbom_document"}
UNLISTED_TYPES = (
    "aws_core__aws_vpc",
    "aws_core__aws_subnet",
    "aws_core__aws_account",
    "aws_core__aws_ecs_task",
)


def _load(name: str) -> dict:
    return json.loads((GRIFT / name).read_text(encoding="utf-8"))


def _nodes(name: str) -> list[dict]:
    return [node for batch in _load(name)["batches"] for node in batch["nodes"]]


def _edges(name: str) -> list[dict]:
    return [edge for batch in _load(name)["batches"] for edge in batch["edges"]]


def _id(entity: dict) -> str:
    """A row's identity inside its bundle: the entity id, or the batch-local ref a parser row carries."""
    return entity.get("entity_id") or entity["ref"]


def _end(body: dict, side: str) -> str:
    """One end of an edge: an entity id, or the ref of a row in the same batch."""
    return body.get(f"{side}_entity_id") or body[f"{side}_ref"]


def _stamped() -> list[dict]:
    return [
        n for f in ("mock-inventory.grift.json", "inventory-entities.grift.json", SOFTWARE) for n in _nodes(f)
    ]


class TestDimensionSplit:
    """`req-rampart-20x-playground-inventory-dimension`."""

    def test_inventory_categories_are_the_nine(self) -> None:
        names = {n["entity"]["name"] for n in _nodes("dimensions.grift.json")}
        assert {n for n in names if n.startswith("inventory.")} == {f"inventory.{c}" for c in CATEGORIES}

    def test_os_is_operating_systems_only(self) -> None:
        by_name = {n["entity"]["name"]: n["node"] for n in _nodes("dimensions.grift.json")}
        assert "container" not in by_name["inventory.os"]["description"]
        assert "container" in by_name["inventory.containers"]["description"]


class TestStamps:
    """`req-rampart-20x-playground-mock-inventory-4`: one category or none, and always on the design position."""

    def test_every_inventory_value_is_a_category(self) -> None:
        stamped = [n for n in _stamped() if "inventory" in n["entity"]["dimensions"]]
        assert stamped
        for node in stamped:
            assert node["entity"]["dimensions"]["inventory"] in CATEGORIES, node["entity"]["name"]

    def test_stamped_entities_are_on_the_design_position(self) -> None:
        for node in _stamped():
            if "inventory" in node["entity"]["dimensions"]:
                assert node["entity"]["dimensions"]["dcom"] == "design", node["entity"]["name"]

    def test_conceptual_containers_and_instances_have_no_row(self) -> None:
        for node in _stamped():
            if node["entity"]["entity_type"] in UNLISTED_TYPES:
                assert "inventory" not in node["entity"]["dimensions"], node["entity"]["name"]

    def test_the_container_table_holds_the_image_not_the_tasks(self) -> None:
        containers = [n for n in _stamped() if n["entity"]["dimensions"].get("inventory") == "containers"]
        assert sorted(n["entity"]["entity_type"] for n in containers) == [
            "computing_core__host",
            "github_core__github_package_version",
        ]

    def test_operating_systems_are_not_stamped_on_a_container(self) -> None:
        # The OS table holds operating-system nodes, never a host or an image.
        stamped = [n for n in _stamped() if n["entity"]["dimensions"].get("inventory") == "os"]
        assert stamped
        assert {n["entity"]["entity_type"] for n in stamped} == {"computing_core__operating_system"}


class TestInventoryEntities:
    """`grift/inventory-entities.grift.json`: existing computing_core types only, no edges, no secret values."""

    def test_existing_types_only(self) -> None:
        allowed = {
            "computing_core__program",
            "computing_core__file",
            "computing_core__public_key",
            "computing_core__private_key",
        }
        assert {n["entity"]["entity_type"] for n in _nodes("inventory-entities.grift.json")} <= allowed

    def test_no_edges_are_invented(self) -> None:
        assert _edges("inventory-entities.grift.json") == []

    def test_no_secret_value_or_fingerprint_is_recorded(self) -> None:
        for node in _nodes("inventory-entities.grift.json"):
            assert not node["node"].get("fingerprint"), node["entity"]["name"]
            assert "content" not in node["node"] and "value" not in node["node"], node["entity"]["name"]

    def test_certificate_halves_are_identified(self) -> None:
        by_type = {n["entity"]["entity_type"]: n["node"] for n in _nodes("inventory-entities.grift.json")}
        assert by_type["computing_core__public_key"]["algorithm"] == by_type["computing_core__private_key"]["algorithm"]


class TestInventorySoftware:
    """`req-rampart-20x-playground-inventory-software`, `-packages`, `-libraries`, `-os`, `-crypto`."""

    def setup_method(self) -> None:
        self.nodes = _nodes(SOFTWARE)
        self.edges = _edges(SOFTWARE)
        self.types = {_id(n["entity"]): n["entity"]["entity_type"] for n in self.nodes}
        # The edge from the TAP web program starts at a node in the inventory entities bundle.
        self.types.update(
            {n["entity"]["entity_id"]: n["entity"]["entity_type"] for n in _nodes("inventory-entities.grift.json")}
        )

    def _of(self, entity_type: str) -> list[dict]:
        return [n for n in self.nodes if n["entity"]["entity_type"] == entity_type]

    def test_only_the_computing_core_types(self) -> None:
        assert {n["entity"]["entity_type"] for n in self.nodes} == set(SOFTWARE_CATEGORY) | SBOM_ONLY_TYPES

    def test_every_node_is_stamped_with_its_category_and_the_design_position(self) -> None:
        for node in self.nodes:
            dims = node["entity"]["dimensions"]
            category = SOFTWARE_CATEGORY.get(node["entity"]["entity_type"])
            assert dims.get("inventory") == category, node["entity"]["name"]
            assert dims["dcom"] == "design", node["entity"]["name"]

    def test_nothing_is_on_the_overview(self) -> None:
        for node in self.nodes:
            assert "overview" not in node["entity"]["dimensions"], node["entity"]["name"]

    def test_only_official_edges_between_the_types_they_join(self) -> None:
        assert self.edges
        for edge in self.edges:
            body = edge["edge"]
            sources, targets = SOFTWARE_EDGES[body["edge_type"]]
            assert self.types[_end(body, "from")] in sources, body
            assert self.types[_end(body, "to")] in targets, body
            assert body["properties"] == {}

    def test_natural_keys_are_unique(self) -> None:
        keys = {
            "computing_core__package": ("ecosystem", "name", "version"),
            "computing_core__library": ("ecosystem", "name", "version"),
            "computing_core__operating_system": ("os_id", "version_id", "build_id"),
            "computing_core__host": ("realm", "stable_id"),
            "computing_core__crypto_provider": ("scope", "artifact", "provider"),
            "computing_core__source_package": ("ecosystem", "name", "version"),
            "computing_core__sbom_document": ("content_digest",),
        }
        seen = set()
        for node in self.nodes:
            etype = node["entity"]["entity_type"]
            key = (etype, *(node["node"].get(field, "") for field in keys[etype]))
            assert key not in seen, key
            seen.add(key)

    def test_required_fields_are_present(self) -> None:
        required = {
            "computing_core__package": ("ecosystem", "name", "version"),
            "computing_core__library": ("ecosystem", "name", "version"),
            "computing_core__operating_system": ("os_id", "version_id", "build_id"),
            "computing_core__host": ("realm", "stable_id"),
            "computing_core__crypto_provider": ("scope", "artifact", "provider", "provider_kind"),
            "computing_core__source_package": ("ecosystem", "name", "version"),
            "computing_core__sbom_document": ("content_digest", "verified", "signer", "subject_digest"),
        }
        for node in self.nodes:
            for field in required[node["entity"]["entity_type"]]:
                assert field in node["node"], (node["entity"]["name"], field)

    def test_packages_come_from_one_verified_sbom_in_the_three_ecosystems(self) -> None:
        packages = self._of("computing_core__package")
        assert {p["node"]["ecosystem"] for p in packages} == {"apk", "pypi", "npm"}
        assert {p["node"]["source_document"] for p in packages} == {"sbom"}
        (document,) = self._of("computing_core__sbom_document")
        body = document["node"]
        # The parser only reads a document whose attestation was verified, and records who signed it.
        assert body["verified"] is True and body["signer"].endswith("publish-images.yml@refs/heads/main")
        assert body["subject_digest"].startswith("sha256:") and len(body["subject_digest"]) == len("sha256:") + 64

    def test_every_package_names_the_source_package_it_was_built_from_or_is_a_python_or_js_package(self) -> None:
        sources = {_id(s["entity"]) for s in self._of("computing_core__source_package")}
        derived = {
            _end(e["edge"], "from")
            for e in self.edges
            if e["edge"]["edge_type"] == "DERIVES_FROM_SOURCE_PACKAGE__computing_core"
        }
        apk = {_id(p["entity"]) for p in self._of("computing_core__package") if p["node"]["ecosystem"] == "apk"}
        assert derived == apk
        assert sources

    def test_every_package_is_installed_by_the_web_image_host(self) -> None:
        (host,) = self._of("computing_core__host")
        installed = {
            _end(e["edge"], "to")
            for e in self.edges
            if e["edge"]["edge_type"] == "INSTALLS_PACKAGE__computing_core"
            and _end(e["edge"], "from") == host["entity"]["entity_id"]
        }
        assert installed == {_id(p["entity"]) for p in self._of("computing_core__package")}
        assert host["node"]["kind"] == "container"

    def test_the_libraries_are_what_is_built_or_copied_outside_a_package_manager(self) -> None:
        libraries = {lib["node"]["name"]: lib["node"] for lib in self._of("computing_core__library")}
        assert set(libraries) == {"openssl-fips-provider", "cryptography", "uv", "uvx"}
        assert libraries["openssl-fips-provider"]["source_kind"] == "self-built"
        assert libraries["cryptography"]["source_kind"] == "source-built"
        assert libraries["uv"]["source_kind"] == libraries["uvx"]["source_kind"] == "copied-image"

    def test_wolfi_is_identified_by_its_pinned_base_image_digest(self) -> None:
        (wolfi,) = self._of("computing_core__operating_system")
        body = wolfi["node"]
        assert body["os_id"] == "wolfi" and body["rolling"] is True
        assert body["build_id"].startswith("sha256:") and len(body["build_id"]) == len("sha256:") + 64
        assert body["base_image"].endswith("@" + body["build_id"])

    def test_the_host_runs_exactly_one_operating_system(self) -> None:
        runs = [e for e in self.edges if e["edge"]["edge_type"] == "RUNS_OPERATING_SYSTEM__computing_core"]
        assert len(runs) == 1

    def test_crypto_providers_are_the_web_scope_and_hold_no_key_material(self) -> None:
        providers = self._of("computing_core__crypto_provider")
        assert providers
        allowed = {"scope", "artifact", "provider", "provider_kind", "boundary", "rationale", "fips_validation"}
        for provider in providers:
            assert provider["node"]["scope"] == "tap-web"
            assert set(provider["node"]) <= allowed, provider["entity"]["name"]

    def test_each_provider_has_at_most_one_carrier(self) -> None:
        carriers: dict[str, int] = {}
        for edge in self.edges:
            if edge["edge"]["edge_type"] == "CARRIES_CRYPTO_PROVIDER__computing_core":
                target = _end(edge["edge"], "to")
                carriers[target] = carriers.get(target, 0) + 1
        assert set(carriers.values()) == {1}
        # The uv binary's provider is carried by the uv library; every provider has an owner.
        unowned = [
            p["node"]["artifact"]
            for p in self._of("computing_core__crypto_provider")
            if _id(p["entity"]) not in carriers
        ]
        assert unowned == []


class TestInventoryPage:
    """`req-rampart-20x-playground-inventory-tables` and `-page-inventory`."""

    def setup_method(self) -> None:
        self.nodes = _nodes("inventory-page.grift.json")
        self.edges = _edges("inventory-page.grift.json")
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}

    def _of(self, entity_type: str) -> list[dict]:
        return [n for n in self.nodes if n["entity"]["entity_type"] == entity_type]

    def test_route(self) -> None:
        (page,) = self._of("page")
        assert page["node"]["slug"] == "/playground/inventory"

    def test_nine_tables_each_over_its_category(self) -> None:
        searches = self._of("search")
        assert len(searches) == len(self._of("panel")) == 9
        queried = set()
        for search in searches:
            where = [line for line in search["node"]["definition"]["query"] if line.startswith("WHERE")]
            assert len(where) == 1 and where[0].startswith('WHERE n.dimensions["inventory"] = "'), where
            queried.add(where[0].split('"')[3])
        assert queried == set(CATEGORIES)

    def test_each_panel_is_a_table_bound_to_exactly_one_search(self) -> None:
        for panel in self._of("panel"):
            assert panel["node"]["view"] == "tap_web/panels/table_panel.html"
            links = [
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
            ]
            assert len(links) == 1, panel["entity"]["name"]
            assert self.by_id[links[0]["edge"]["to_entity_id"]]["entity"]["entity_type"] == "search"

    def test_page_slots_match_the_uses_panel_edges(self) -> None:
        (page,) = self._of("page")
        slots = [
            row["panel-id"]
            for col in page["node"]["layout"]["columns"].values()
            for row in col["rows"].values()
        ]
        hotlinks = [
            e["edge"]["properties"]["hotlink"]["value"] for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"
        ]
        assert sorted(slots) == sorted(hotlinks) == sorted(SLOTS.values())
        assert slots == list(PAGE_ORDER)

    def test_each_slot_mounts_the_panel_of_its_category(self) -> None:
        for category, slot in SLOTS.items():
            edge = next(
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["properties"]["hotlink"]["value"] == slot
            )
            panel = self.by_id[edge["edge"]["to_entity_id"]]
            assert panel["node"]["slug"] == f"playground-inventory-{slot}"
            search_edge = next(
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_SEARCH"
                and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
            )
            query = self.by_id[search_edge["edge"]["to_entity_id"]]["node"]["definition"]["query"]
            assert f'WHERE n.dimensions["inventory"] = "{category}"' in query

    def test_common_columns_on_every_table(self) -> None:
        for panel in self._of("panel"):
            fields = [c["field"] for c in panel["node"]["config"]["columns"] if "field" in c]
            assert fields[:2] == ["entity_id", "name"], panel["entity"]["name"]
            # No description column: the entity types hold no description field (a recorded gap in the spec).
            assert "data.description" not in fields, panel["entity"]["name"]

    def test_every_table_ends_with_the_two_data_classification_columns(self) -> None:
        """Q90a: the customer and infra data classifications, read by path from the node's dimensions; never blank."""
        for panel in self._of("panel"):
            customer, infra = panel["node"]["config"]["columns"][-2:]
            assert customer["field_path"] == ["dimensions", "dataclass.customer"] and customer["title"] == "Customer data"
            assert infra["field_path"] == ["dimensions", "dataclass.infra"] and infra["title"] == "Infra data"
            for column in (customer, infra):
                assert "field" not in column and column["empty_text"] == "not classified", panel["entity"]["name"]

    def test_entity_type_columns_use_the_tail_segment_formatter(self) -> None:
        for panel in self._of("panel"):
            for column in panel["node"]["config"]["columns"]:
                if column.get("field") == "entity_type":
                    assert column["formatter"] == "tailSegment", panel["entity"]["name"]
                    assert column["formatter_params"] == {"sep": "__"}, panel["entity"]["name"]

    def test_no_header_tooltip_frames_the_data_as_mock(self) -> None:
        for panel in self._of("panel"):
            for column in panel["node"]["config"]["columns"]:
                assert "mock" not in column["header_tooltip"].lower(), (panel["entity"]["name"], column["title"])

    def test_software_tables_show_their_columns(self) -> None:
        fields = {
            panel["entity"]["name"]: [c["field"] for c in panel["node"]["config"]["columns"] if "field" in c]
            for panel in self._of("panel")
        }
        for field in ("data.version", "data.ecosystem", "data.source_document", "data.architecture", "data.license", "data.purl"):
            assert field in fields["Packages"], field
        for field in ("data.provider", "data.provider_kind", "data.artifact", "data.boundary", "data.fips_validation", "data.scope", "data.rationale"):
            assert field in fields["Crypto"], field

    def test_no_free_text_comments_column_and_no_secret_columns(self) -> None:
        for panel in self._of("panel"):
            for column in panel["node"]["config"]["columns"]:
                name = column["field"] if "field" in column else ".".join(column["field_path"])
                assert "comment" not in name.lower() and "comment" not in column["title"].lower()
                assert "fingerprint" not in name.lower()

    def test_app_entities_carry_no_dcom_value(self) -> None:
        """`req-rampart-20x-playground-nongoals-4`: the page, panels, Searches and edges are the app, not the system."""
        for node in self.nodes:
            assert "dcom" not in node["entity"]["dimensions"], node["entity"]["name"]


class TestNewIds:
    def test_new_ids_are_unique_version_7_uuids(self) -> None:
        ids: list[str] = []
        for name in ("inventory-entities.grift.json", SOFTWARE, "inventory-page.grift.json"):
            for batch in _load(name)["batches"]:
                ids.append(batch["batch_entity"]["entity_id"])
                # A row the parser wrote names itself by a batch-local ref, not an id: the grid assigns its id.
                ids += [n["entity"]["entity_id"] for n in batch["nodes"] if "entity_id" in n["entity"]]
                ids += [e["entity"]["entity_id"] for e in batch["edges"] if "entity_id" in e["entity"]]
        assert len(ids) == len(set(ids))
        assert all(uuid.UUID(i).version == 7 for i in ids)
        existing = {
            n["entity"]["entity_id"] for f in ("mock-inventory.grift.json", "pages.grift.json") for n in _nodes(f)
        }
        assert not existing & set(ids)
