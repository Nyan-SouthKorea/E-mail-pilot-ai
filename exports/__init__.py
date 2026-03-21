"""Exports 계층의 템플릿 해석 계약을 노출한다."""

from .schema import (
    TEMPLATE_PROFILE_SCHEMA_VERSION,
    TemplateColumn,
    TemplateProfile,
    TemplateSheet,
)
from .semantic_mapping import (
    TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION,
    SemanticFieldDefinition,
    TemplateColumnSemanticMapping,
    TemplateSemanticMapping,
    apply_template_semantic_mapping,
    default_semantic_field_definitions,
    semantic_field_definition_map,
)
from .template_profile import TemplateWorkbookReader, read_template_profile

__all__ = [
    "TEMPLATE_PROFILE_SCHEMA_VERSION",
    "TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION",
    "SemanticFieldDefinition",
    "TemplateColumn",
    "TemplateColumnSemanticMapping",
    "TemplateProfile",
    "TemplateSemanticMapping",
    "TemplateSheet",
    "TemplateWorkbookReader",
    "apply_template_semantic_mapping",
    "default_semantic_field_definitions",
    "read_template_profile",
    "semantic_field_definition_map",
]
