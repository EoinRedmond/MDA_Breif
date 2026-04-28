ALLOWED_NODE_TYPES = [
    "financial_metric",
    "business_segment",
    "geography",
    "product",
    "risk_factor",
    "cost_driver",
    "growth_driver",
    "strategic_initiative",
    "macroeconomic_factor"
]

ALLOWED_RELATIONSHIPS = [
    "increases",
    "decreases",
    "drives",
    "constrains",
    "is_component_of",
    "impacts",
    "offsets",
    "depends_on",
    "compared_with"
]


def build_graph_prompt(record):
    return f"""
You are extracting a knowledge graph from a company's MD&A section.

Company ticker: {record["ticker"]}
Filing year: {record["year"]}

Task:
Extract the major business and financial ideas from the MD&A as nodes, and extract the relationships between them as edges.

Allowed node types:
{ALLOWED_NODE_TYPES}

Allowed relationship types:
{ALLOWED_RELATIONSHIPS}

Return ONLY valid JSON with this structure:

{{
  "nodes": [
    {{
      "id": "Revenue",
      "type": "financial_metric",
      "evidence": "short quote from the MD&A"
    }}
  ],
  "edges": [
    {{
      "source": "Revenue",
      "target": "Profitability",
      "relationship": "drives",
      "evidence": "short quote from the MD&A"
    }}
  ]
}}

Rules:
- Use only information supported by the MD&A.
- Keep node ids short and readable.
- Do not invent relationships.
- Include 8 to 15 nodes.
- Include 8 to 20 edges.
- Evidence must be copied from the MD&A.
- Return JSON only.

MD&A text:
\"\"\"
{record["text"][:12000]}
\"\"\"
"""