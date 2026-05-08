// Vercel Serverless Function: proxies the browser to OpenAI Chat Completions
// using the OPENAI_API_KEY env var. The browser never sees the key.
//
// Required env var (set via Vercel dashboard or `vercel env add`):
//   OPENAI_API_KEY  � sk-...
//
// Optional env vars:
//   OPENAI_ALLOWED_MODELS  � comma-separated allowlist (default includes gpt-5, gpt-5-mini, gpt-4o family)

export const config = { runtime: "nodejs" };

const DEFAULT_ALLOWED_MODELS = [
  "gpt-5",
  "gpt-5-mini",
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4.1",
  "gpt-4.1-mini",
];

function getAllowedModels() {
  const raw = process.env.OPENAI_ALLOWED_MODELS;
  if (!raw) return DEFAULT_ALLOWED_MODELS;
  return raw.split(",").map((s) => s.trim()).filter(Boolean);
}

/**
 * GPT-5 chat completions differ from gpt-4o:
 * - use max_completion_tokens (not max_tokens)
 * - temperature cannot be 0; API only accepts default (1), so we omit the field.
 */
function isGpt5ChatModel(model) {
  return /^gpt-5/i.test(model);
}

async function readJsonBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") {
    try { return JSON.parse(req.body); } catch { return null; }
  }
  return await new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => { data += c; });
    req.on("end", () => {
      if (!data) return resolve({});
      try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
    });
    req.on("error", reject);
  });
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return res
      .status(500)
      .json({ error: "Server is missing OPENAI_API_KEY. Set it in Vercel env vars and redeploy." });
  }

  let body;
  try {
    body = await readJsonBody(req);
  } catch {
    return res.status(400).json({ error: "Invalid JSON body" });
  }

  const {
    model,
    messages,
    max_tokens,
    max_completion_tokens,
    temperature,
    response_format,
  } = body || {};
  if (!model || typeof model !== "string") {
    return res.status(400).json({ error: "Missing or invalid 'model'" });
  }
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: "Missing or invalid 'messages'" });
  }

  const allowed = getAllowedModels();
  if (!allowed.includes(model)) {
    return res.status(400).json({ error: `Model '${model}' is not allowed`, allowed });
  }

  const tokenBudget =
    typeof max_completion_tokens === "number"
      ? max_completion_tokens
      : typeof max_tokens === "number"
        ? max_tokens
        : 2000;

  try {
    const limitKey = isGpt5ChatModel(model)
      ? { max_completion_tokens: tokenBudget }
      : { max_tokens: tokenBudget };

    const temp =
      typeof temperature === "number" ? temperature : 0;
    const upstreamBody = {
      model,
      messages,
      ...limitKey,
      ...(isGpt5ChatModel(model) ? {} : { temperature: temp }),
      ...(response_format ? { response_format } : {}),
    };

    const upstream = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(upstreamBody),
    });

    const text = await upstream.text();
    res.status(upstream.status);
    res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
    return res.send(text);
  } catch (err) {
    console.error("[api/openai] upstream fetch failed:", err);
    return res.status(502).json({ error: "Upstream OpenAI request failed", detail: String(err?.message || err) });
  }
}
