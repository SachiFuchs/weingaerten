"""Computes a loaded model: element rules, schemas, foundation and all storeys."""
import logging
from typing import Any, Dict

from ..constants import TOLERANCE
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..model.tga_products import TgaProducts
from ..validation.connection_validator import ConnectionValidator
from ..validation.document_validator import DocumentValidator
from ..validation.element_validator import ElementValidator
from ..validation.schema_validator import SchemaValidator
from .foundation_builder import FoundationBuilder
from .shaft_builder import ShaftBuilder
from .storey_builder import StoreyBuilder
from .waste_water_builder import WasteWaterBuilder
from .water_supply_builder import WaterSupplyBuilder
from .electrical_builder import ElectricalBuilder
from .part_builder import PartBuilder

logger = logging.getLogger(__name__)


class ModelComputer:
    """Fills errors, warnings, `foundation` and `storeys_out` of a loaded model."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the raw model of ModelLoader; it is completed in place.
        """
        self._model = model
        self._issues = IssueLog(model)

    def compute(self) -> None:
        """Validate every element and the house files, then compute foundation and storeys."""
        model = self._model
        validator = ElementValidator(model)
        for ref, element in model["elements"].items():
            for message in validator.errors(ref, element):
                self._issues.error(ref, message)
        documents = DocumentValidator(model)
        for ref, element in model["elements"].items():
            if ref.startswith("document:"):
                for message in documents.warnings(element):
                    self._issues.warning(ref, message)
        self._check_house_schemas()
        self._check_connections(validator)
        foundation = FoundationBuilder(model, self._issues)
        foundation.read_spec()
        shafts = ShaftBuilder(model, self._issues)
        shafts.plan()
        model["storeys_out"] = []
        ground_ref = self._ground_ref()
        for storey_ref, storey in model["storeys"].items():
            model["storeys_out"].append(StoreyBuilder(model, self._issues).build(storey_ref, storey,
                                                                                 storey_ref == ground_ref))
        # a rect foundation without any storey is still built
        spec = model["foundation_spec"]
        if model["foundation"] is None and spec and spec["poly"]:
            foundation.build(spec["poly"])
        model["waste_water"] = WasteWaterBuilder(model, self._issues).build()
        model["water_supply"] = WaterSupplyBuilder(model, self._issues).build()
        model["electrical"] = ElectricalBuilder(model, self._issues).build()
        model["installation"] = PartBuilder(model, self._issues).build()
        shafts.finish()
        self._check_room_numbers()
        logger.debug("model computed: %d errors, %d warnings", len(model["errors"]), len(model["warnings"]))

    def _check_connections(self, validator: ElementValidator) -> None:
        # TGA catalog (schema + connection rules) and the end points / slopes of the runs
        connections = ConnectionValidator(self._model)
        products = TgaProducts(self._model)
        for ref, element in sorted(((self._model.get("tga") or {}).get("elements") or {}).items()):
            for message in validator.errors(ref, element):
                self._issues.error(ref, message)
            if ref.startswith("tga-component:") and not element.get("abstract") and not element.get("assembly") \
                    and connections.missing(element):
                self._issues.warning(ref, "Verbindungsdaten fehlen")
            if ref.startswith("tga-component:") and products.double_offers(element):
                self._issues.warning(ref, "Angebote doppelt (Material + TGA) - es gelten die des Materials")
        issues = connections.run_issues()
        for issue in issues:
            self._issues.warning(issue["where"], issue["message"])
        self._model["connections"] = {"issues": issues}

    def _check_room_numbers(self) -> None:
        # room numbers identify a room in the whole house (plans, IFC export)
        seen = set()
        for storey in self._model["storeys_out"]:
            for room in storey["rooms"]:
                if room["number"] is not None and room["number"] in seen:
                    self._issues.error("%s.%s" % (storey["ref"], room["id"]), "doppelte Raumnummer: %s" % room["number"])
                seen.add(room["number"])

    def _ground_ref(self) -> Any:
        # the ground storey stands on the foundation; a basement below it is listed anywhere in house.storeys
        refs = list(self._model["storeys"])
        spec = self._model["foundation_spec"]
        if spec:
            for ref in refs:
                elevation = self._model["storeys"][ref].get("elevation", 0.0)
                if JsonValues.is_number(elevation) and abs(float(elevation) - spec["top"]) <= TOLERANCE:
                    return ref
        return refs[0] if refs else None

    def _check_house_schemas(self) -> None:
        schemas = self._model["schemas"]
        house = self._model["house"]
        if isinstance(house, dict) and "house" in schemas:
            for where, message in SchemaValidator(schemas["house"]).check(house, "house"):
                self._issues.error(where, message)
        if "storey" in schemas:
            validator = SchemaValidator(schemas["storey"])
            for storey_ref, storey in self._model["storeys"].items():
                for where, message in validator.check(storey, storey_ref):
                    self._issues.error(where, message)
