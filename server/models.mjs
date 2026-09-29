import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

const OLLAMA = "http://localhost:11434/api/generate";
const SYS = "You are an analyst for a global awareness dashboard. Use only the data given. Be brief.\n\n";

async function ask(question, data, options) {
  const prompt = SYS + "DATA:\n" + JSON.stringify(data) + "\n\nQUESTION: " + question;
  const r = await fetch(OLLAMA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "llama3.1", prompt, stream: false, options }),
  });
  return (await r.json()).response;
}

// Model A: deterministic (greedy decoding, fixed seed)
app.post("/model-a", async (req, res) => {
  const { question, data } = req.body;
  const answer = await ask(question, data, { temperature: 0, top_k: 1, seed: 42 });
  res.json({ model: "A-deterministic", answer });
});

// Model B: probabilistic (sampling, no seed)
app.post("/model-b", async (req, res) => {
  const { question, data } = req.body;
  const answer = await ask(question, data, { temperature: 0.9, top_p: 0.95, top_k: 40 });
  res.json({ model: "B-probabilistic", answer });
});

// Model C: forwards to the Python R3-Skill service
app.post("/model-c", async (req, res) => {
  const r = await fetch("http://localhost:8060/route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: req.body.question }),
  });
  res.json(await r.json());
});

app.listen(5051, () => console.log("Models server on http://localhost:5051"));
