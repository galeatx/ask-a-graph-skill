# Troubleshooting — Diagnosing bad query results

Use this guide when Step 5 returns suspicious results: 0 records, all-NULL columns, or far fewer results than expected. Run these diagnostic queries via `execute_cypher` to identify the root cause before re-generating.

---

## 1. Relationship properties returning NULL

**Symptom**: query executes successfully but a column that should have values (e.g. `essentiality_score`, `expression_level`) is entirely NULL.

**Cause**: wrong property name on the relationship — `generate_cypher` guesses property names because the schema prompt does not include them.

**Fix**: discover the actual property keys from the graph:

```cypher
MATCH ()-[r:<REL_TYPE>]->() RETURN keys(r) LIMIT 1
```

Example:
```cypher
MATCH ()-[r:HAS_GENE_ESSENTIALITY]->() RETURN keys(r) LIMIT 1
// → ["ESSENTIALITY_SCORE"]

MATCH ()-[r:EXPRESSES]->() RETURN keys(r) LIMIT 1
// → ["nTPM", "weight"]
```

Then correct the property name in the Cypher query, log the revision to `$output_dir/step4_cypher.revised.json`, and re-execute.

---

## 2. Filter returns 0 rows

**Symptom**: a `WHERE` clause with a threshold (e.g. `r.ESSENTIALITY_SCORE <= -0.5`) returns 0 results, but removing the filter returns rows.

**Diagnose the value distribution** for the specific entity:

```cypher
MATCH (src)-[r:<REL_TYPE>]->(target)
WHERE id(target) = $node_id
RETURN count(r) AS total, min(r.<PROPERTY>) AS min_val, max(r.<PROPERTY>) AS max_val, avg(r.<PROPERTY>) AS avg_val
```

If `total` is 0, the entity has no relationships of that type — see Section 3. If `total` > 0 but the threshold filters everything out, report the actual range to the user and ask them to adjust.

---

## 3. Specific entity has no relationships

**Symptom**: query returns 0 rows even without filters; the entity was successfully resolved in Step 3.

**Check whether relationships exist for this node at all:**

```cypher
MATCH (n) WHERE id(n) = $node_id
RETURN labels(n) AS labels, keys(n) AS props
```

```cypher
MATCH (n)-[r]->(m) WHERE id(n) = $node_id
RETURN type(r) AS rel_type, count(*) AS cnt

MATCH (n)<-[r]-(m) WHERE id(n) = $node_id
RETURN type(r) AS rel_type, count(*) AS cnt
```

This reveals which relationship types actually exist for the node and in which direction, which may differ from what the query assumed.

---

## 4. Wrong relationship direction

**Symptom**: query returns 0 rows; relationship type and property names are correct.

**Neo4j is direction-sensitive.** Test both directions:

```cypher
MATCH (a)-[r:<REL_TYPE>]->(b) WHERE id(a) = $node_id RETURN count(r) LIMIT 1
MATCH (a)<-[r:<REL_TYPE>]-(b) WHERE id(a) = $node_id RETURN count(r) LIMIT 1
```

Use whichever direction returns results in the corrected query.

---

## 5. Node property names returning NULL

**Symptom**: a node property column (e.g. `patient.PRIMARYIDENTIFIER`) is NULL.

**Discover actual node property keys:**

```cypher
MATCH (n:<Label>) RETURN keys(n) LIMIT 1
```

Example:
```cypher
MATCH (n:Patient) RETURN keys(n) LIMIT 1
MATCH (n:Gene) RETURN keys(n) LIMIT 1
```

Correct the property name and revise the query accordingly.
