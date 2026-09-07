"""System-theoretic Brand domain contracts."""

from .fixtures import BrandFixture, load_brand_fixture, validate_brand_fixture
from .models import (
    AssertionStatus,
    BrandArtifact,
    BrandAssertion,
    BrandComponent,
    BrandStateSnapshot,
    BrandSystem,
)
from .modules import (
    BrandOntologyModule,
    BrandOntologyRelease,
    ModuleRelationshipDefinition,
    ModuleTypeDefinition,
    OntologyModuleSource,
    load_brand_ontology_release,
)
from .ontology import (
    BrandOntology,
    ComponentTypeDefinition,
    OntologySource,
    RelationshipTypeDefinition,
    load_brand_ontology,
)
from .policies import RelationshipWeightDimensions, RelationshipWeightPolicy

__all__ = [
    "AssertionStatus",
    "BrandArtifact",
    "BrandAssertion",
    "BrandComponent",
    "BrandFixture",
    "BrandOntology",
    "BrandStateSnapshot",
    "BrandSystem",
    "BrandOntologyModule",
    "BrandOntologyRelease",
    "ComponentTypeDefinition",
    "OntologySource",
    "OntologyModuleSource",
    "RelationshipTypeDefinition",
    "RelationshipWeightDimensions",
    "RelationshipWeightPolicy",
    "ModuleRelationshipDefinition",
    "ModuleTypeDefinition",
    "load_brand_fixture",
    "load_brand_ontology",
    "load_brand_ontology_release",
    "validate_brand_fixture",
]
