# Available Databases

Read this file to select the appropriate database before executing any workflow step.

---

## oncograph

**Domain**: Cancer genomics — patient-level multi-omics data
**Source**: The Cancer Genome Atlas (TCGA)
**Use when**: The question involves cancer patients, tumor samples, gene expression, copy number variation, DNA methylation, mutational signatures, or CRISPR gene essentiality across cancer types.

**Node types**: Gene, Patient (+ 33 TCGA cancer-type sub-labels: BRCA, GBM, LUAD, etc.), MutationalSignature, CellLine, GenomeRegion, Variant
**Relationship types**: EXPRESSES, HAS_COPY_NUMBER_VARIANT, HAS_GENE_ESSENTIALITY, HAS_MUTATIONAL_SIGNATURE, HAS_METHYLATION_* (6 types), HAS_CANCER_CELL_LINE_ENCYCLOPEDIA_EXPRESSION, LOCATED_IN, PROCEEDS

**Example questions**:
- Which patients express KRAS at high levels?
- What mutational signatures are prevalent in lung adenocarcinoma?
- Which genes are essential in glioblastoma cell lines?

---

## arch-v5

**Domain**: Drug discovery and translational pharmacology
**Source**: Internal knowledge graph (drugs, targets, diseases, pathways, preclinical/clinical data)
**Use when**: The question involves drugs, compounds, gene targets, mechanisms of action, side effects, drug-drug interactions, disease associations, pathways, or clinical/preclinical evidence.

**Node types**: Gene, Drug, Compound, Disease, HealthCondition, Pathway, CellLine, CellType, Tissue, Variant, Phenotype, Ingredient (+ measurement nodes: ADMETox, PK, BodyWeights, etc.)
**Relationship types**: AFFECTS_EXPRESSION, AFFECTS_INHIBITION, ASSOCIATED_WITH, HAS_SIDE_EFFECT, HAS_MOA, TARGETS_TELLIC, APPROVED_TREATMENT_FOR, PROTEIN_PROTEIN_INTERACTIONS, and many more

**Example questions**:
- What are the known side effects of drug X?
- Which genes does compound Y inhibit?
- What diseases is pathway Z associated with?

---

## Adding a new database

Add a new section above following the same structure:
- Database name as `## heading`
- Domain, source, use-when guidance
- Node types and relationship types (copy from `setup_complete.json → db_types`)
- 2–3 example questions
