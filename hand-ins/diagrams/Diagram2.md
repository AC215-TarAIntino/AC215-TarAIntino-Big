# 🎬 TarAIntino System Architecture

## Part 2 - Trailor Generation
```mermaid```
---
config:
  theme: neutral
---
flowchart RL
subgraph Z[" "]
  A{"Movie specification(json format)"} 
  end

subgraph ZK[" "]
A--> B["Trailor planning"]
B --> C{"Trailor Specification(json format)"}
C --> b1[Beat1]
b1 --> s1[shotA]
b1 --> s2[shotB]
b1 --> s3[shotC]
C--> b2[Beat2]
b2 --> s4[shotD]
b2 --> s5[shotE]
b2 --> s6[shotF]
C --> b3[Beat3]
b3 --> s7[......]
end

subgraph ZM[" "]
s1 --> OO[Generative vedio API]
s2 --> OO
s3 --> OO
s4 --> OO
s6 --> OO
s5 --> OO
s7 --> OO
OO --> DD{Clips}

end

subgraph ZM1[" "]
DD --> MK[Video processing library]
MK --Concatenate clips-->TR{Trailor}
TR -- LLM agent --> OK[Narration script with AI voice]
TR -- AI music generator --> BG[Background music]
OK --> FL{Final AI trailor}
BG --> FL
end
