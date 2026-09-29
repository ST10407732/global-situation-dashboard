from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder

app = FastAPI()
emb = SentenceTransformer("tencent/R3-embedding-0.6b")
rr = CrossEncoder("tencent/R3-rerank-0.6b")

# Format per the model card: "name | description | skill_md"
SKILLS = [
    "earthquake-monitor | Reports earthquakes, magnitude and depth | Answers questions about USGS seismic activity",
    "volcano-monitor | Reports volcanic eruptions and activity | Answers questions about NASA EONET volcano events",
    "cyber-threat-monitor | Reports CVEs, CISA KEV and exploited vulnerabilities | Answers questions about cyber threats and severity",
    "ransomware-breach-monitor | Reports ransomware victims and data breaches | Answers questions about incidents and exposed records",
    "space-monitor | Reports ISS position, crew and space weather | Answers questions about orbit, KP index and solar activity",
    "global-risk-summary | Summarises the overall global risk level | Explains LOW, ELEVATED, HIGH or CRITICAL risk",
]
skill_vecs = emb.encode(SKILLS, normalize_embeddings=True)

class Q(BaseModel):
    question: str

@app.post("/route")
def route(q: Q):
    qv = emb.encode([q.question], normalize_embeddings=True)
    sims = (skill_vecs @ qv.T).flatten()
    top = sims.argsort()[::-1][:4]                      # stage 1: recall
    pairs = [(q.question, SKILLS[i]) for i in top]
    scores = rr.predict(pairs)                          # stage 2: rerank
    ranked = sorted(zip(top, scores), key=lambda x: -x[1])
    return {
        "model": "C-R3-Skill",
        "routed_to": SKILLS[ranked[0][0]].split(" | ")[0],
        "ranking": [{"skill": SKILLS[i].split(" | ")[0], "score": float(s)} for i, s in ranked],
    }