# pymgclient / Memgraph v3 quirks

Condensed debugging notes from building the agent shared knowledge graph.

## Import name mismatch

```bash
pip install pymgclient
```

```python
import mgclient  # NOT pymgclient
```

## Cursor is not iterable

Wrong:

```python
for row in cur:
    ...
```

Right:

```python
while True:
    row = cur.fetchone()
    if row is None:
        break
    ...
```

## Cursor is not a context manager

Wrong:

```python
with conn.cursor() as cur:
    ...
```

Right:

```python
cur = conn.cursor()
try:
    ...
finally:
    cur.close()
```

## Regex limitations

Memgraph `=~` regex does not support `(?i)` or zero-width assertions.

Wrong:

```cypher
WHERE n.content =~ '(?i).*foo.*'
```

Right-ish (case-sensitive but broad):

```cypher
WHERE n.content =~ '.*(?:foo|bar).*'
```

Combine with `CONTAINS` for a simple keyword fallback.

## No APOC in base image

The default `memgraph/memgraph` Docker image does not include APOC. Avoid:

```cypher
apoc.convert.fromJsonList(...)
```

Store JSON arrays as strings and parse in Python after retrieval.

## Constraint syntax

Memgraph v3 supports uniqueness constraints like:

```cypher
CREATE CONSTRAINT ON (n:Fact) ASSERT n.id IS UNIQUE;
```

Wrap in try/rollback; the constraint may already exist.
