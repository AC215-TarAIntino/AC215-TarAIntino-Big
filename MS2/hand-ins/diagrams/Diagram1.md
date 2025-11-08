# 🎬 TarAIntino System Architecture

## Part 1 – Taste Vector & Recommendation

```mermaid

---
config:
  theme: neutral
---
flowchart LR
subgraph Z[" "]
  A["Initialize user taste vector"] --> B["Preference quiz"]
  M(["Tinder-swiping interface with preference sorting algorithm"]) -.- B
  B -- update by step --> C{"User taste vector"}
end

subgraph ZA[" "]
  C --> D["Similarity match"]
  O["Movie DB + Tag Genome"] -.- D
  D --> R{Preferred movie anchors}
  R --> K["PCA (or other ML approach for recommendation/similarity)"]
  K --> Q{Extended movie recommendations}
  Q --> MCP["Model Context Protocol (MCP)"]
  IMDB[("IMDB Database")] -.- MCP
  MCP --> V[LLM story generation agent]

  O@{ shape: db}
  IMDB@{ shape: db}
  style M fill:transparent
  style O fill:transparent
  style IMDB fill:transparent
end