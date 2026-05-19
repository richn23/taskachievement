// Vercel Serverless Function: proxies the browser to Anthropic Messages API
// using the CLAUDE_API_KEY env var. The browser never sees the key.
//
// Accepts an OpenAI-style request body (model, messages, max_tokens, temperature),
// translates it to Anthropic format, and returns an OpenAI-style response shape
// so the client `callOpenAI()` function doesn't need to know which provider it hit.
//
// Required env var (set via Vercel dashboard or `vercel env add`):
//   CLAUDE_API_KEY  - sk-ant-...

export const config = { runtime: "nodejs" };

const DEFAULT_ALLOWED_MODELS = [
  "claude-opus-4-6",
  "claude-sonnet-4-6",
  "claude-haiku-4-5-20251001",
];

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

  const apiKey = process.env.CLAUDE_API_KEY;
  if (!apiKey) {
    return res.status(500).json({
      error: "Server is missing CLAUDE_API_KEY. Set it in Vercel env vars and redeploy.",
    });
  }

  let body;
  try {
    body = await readJsonBody(req);
  } catch {
    return res.status(400).json({ error: "Invalid JSON body" });
  }

  const { model, messages, max_tokens, temperature } = body || {};
  if (!model || typeof model !== "string") {
    return res.status(400).json({ error: "Missing or invalid 'model'" });
  }
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: "Missing or invalid 'messages'" });
  }
  if (!DEFAULT_ALLOWED_MODELS.includes(model)) {
    return res.status(400).json({
      error: `Model '${model}' is not allowed`,
      allowed: DEFAULT_ALLOWED_MODELS,
    });
  }

  // Translate OpenAI-style messages -> Anthropic format
  //   OpenAI: { role: "system" | "user" | "assistant", content: "..." }
  //   Anthropic: top-level `system` string + messages array of user/assistant only
  let systemPrompt = "";
  const convo = [];
  for (const msg of messages) {
    if (!msg || typeof msg !== "object") continue;
    if (msg.role === "system") {
      // If multiple system messages, concatenate
      systemPrompt = systemPrompt
        ? `${systemPrompt}\n\n${msg.content}`
        : (msg.content || "");
    } else if (msg.role === "user" || msg.role === "assistant") {
      convo.push({ role: msg.role, content: msg.content || "" });
    }
  }

  if (convo.length === 0) {
    return res.status(400).json({ error: "No user/assistant messages after filtering" });
  }

  const upstreamBody = {
    model,
    max_tokens: typeof max_tokens === "number" ? max_tokens : 2000,
    messages: convo,
    ...(systemPrompt ? { system: systemPrompt } : {}),
    ...(typeof temperature === "number" ? { temperature } : {}),
  };

  try {
    const upstream = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(upstreamBody),
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      console.error("[api/claude] upstream error:", upstream.status, text.slice(0, 400));
      res.status(upstream.status);
      res.setHeader("Content-Type", "application/json");
      return res.send(text);
    }

    const data = await upstream.json();

    // Translate Anthropic response -> OpenAI-style shape so the client code
    // (which expects choices[0].message.content) works without changes.
    //   Anthropic: { content: [{type:"text", text:"..."}, ...], stop_reason, usage: {input_tokens, output_tokens}, ... }
    //   OpenAI:    { choices: [{message: {role, content}, finish_reason}], usage: {...} }
    const textContent = Array.isArray(data.content)
      ? data.content
          .filter((b) => b && b.type === "text")
          .map((b) => b.text || "")
          .join("")
      : "";

    const openAIShape = {
      id: data.id,
      model: data.model,
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: textContent },
          finish_reason: data.stop_reason || "stop",
        },
      ],
      usage: data.usage
        ? {
            prompt_tokens: data.usage.input_tokens,
            completion_tokens: data.usage.output_tokens,
            total_tokens:
              (data.usage.input_tokens || 0) + (data.usage.output_tokens || 0),
          }
        : undefined,
    };

    return res.status(200).json(openAIShape);
  } catch (err) {
    console.error("[api/claude] upstream fetch failed:", err);
    return res
      .status(502)
      .json({ error: "Upstream Anthropic request failed", detail: String(err?.message || err) });
  }
}
