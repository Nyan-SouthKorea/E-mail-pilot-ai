"""Exports 계층의 템플릿 해석 계약을 노출한다."""

from .schema import (
    TEMPLATE_PROFILE_SCHEMA_VERSION,
    TemplateColumn,
    TemplateProfile,
    TemplateSheet,
)
from .record_projection import (
    RECORD_TEMPLATE_PROJECTION_SCHEMA_VERSION,
    ProjectedTemplateRow,
    ProjectedTemplateValue,
    ResolvedRecordProjection,
    ResolvedSemanticValue,
    default_extracted_record_aliases,
    project_record_to_template,
    resolve_record_semantic_values,
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
    "RECORD_TEMPLATE_PROJECTION_SCHEMA_VERSION",
    "TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION",
    "ProjectedTemplateRow",
    "ProjectedTemplateValue",
    "ResolvedRecordProjection",
    "ResolvedSemanticValue",
    "SemanticFieldDefinition",
    "TemplateColumn",
    "TemplateColumnSemanticMapping",
    "TemplateProfile",
    "TemplateSemanticMapping",
    "TemplateSheet",
    "TemplateWorkbookReader",
    "apply_template_semantic_mapping",
    "default_extracted_record_aliases",
    "default_semantic_field_definitions",
    "project_record_to_template",
    "read_template_profile",
    "resolve_record_semantic_values",
    "semantic_field_definition_map",
]
