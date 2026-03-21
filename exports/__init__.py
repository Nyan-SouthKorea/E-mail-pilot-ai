"""Exports 계층의 템플릿 해석 계약을 노출한다."""

from .schema import (
    TEMPLATE_PROFILE_SCHEMA_VERSION,
    TemplateColumn,
    TemplateProfile,
    TemplateSheet,
)
from .llm_mapping import (
    UNRESOLVED_TEMPLATE_HEADER_SENTINEL,
    UnresolvedTemplateHeader,
    apply_hybrid_template_mapping,
    build_hybrid_template_mapping,
    build_llm_fallback_template_mapping,
    build_llm_template_mapping_input,
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
from .rule_mapping import (
    RuleSemanticMatch,
    apply_rule_based_template_mapping,
    build_rule_based_template_mapping,
)
from .semantic_mapping import (
    TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION,
    SemanticFieldDefinition,
    TemplateColumnSemanticMapping,
    TemplateSemanticMapping,
    apply_template_semantic_mapping,
    default_semantic_field_definitions,
    merge_template_semantic_mappings,
    semantic_field_definition_map,
)
from .template_profile import TemplateWorkbookReader, read_template_profile
from .workbook_writer import WorkbookAppendResult, append_projected_row_to_workbook

__all__ = [
    "TEMPLATE_PROFILE_SCHEMA_VERSION",
    "RECORD_TEMPLATE_PROJECTION_SCHEMA_VERSION",
    "TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION",
    "ProjectedTemplateRow",
    "ProjectedTemplateValue",
    "ResolvedRecordProjection",
    "ResolvedSemanticValue",
    "RuleSemanticMatch",
    "SemanticFieldDefinition",
    "TemplateColumn",
    "TemplateColumnSemanticMapping",
    "TemplateProfile",
    "TemplateSemanticMapping",
    "TemplateSheet",
    "TemplateWorkbookReader",
    "UNRESOLVED_TEMPLATE_HEADER_SENTINEL",
    "UnresolvedTemplateHeader",
    "WorkbookAppendResult",
    "apply_hybrid_template_mapping",
    "apply_template_semantic_mapping",
    "apply_rule_based_template_mapping",
    "append_projected_row_to_workbook",
    "build_hybrid_template_mapping",
    "build_llm_fallback_template_mapping",
    "build_llm_template_mapping_input",
    "build_rule_based_template_mapping",
    "default_extracted_record_aliases",
    "default_semantic_field_definitions",
    "merge_template_semantic_mappings",
    "project_record_to_template",
    "read_template_profile",
    "resolve_record_semantic_values",
    "semantic_field_definition_map",
]
