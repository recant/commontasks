import type { Recipe } from '../types.ts';

/**
 * Model families whose Ollama chat template defines tool calling.
 *
 * Tool support on Ollama is a property of the MODEL, not the endpoint: the
 * server can only emit tool calls for a model whose template declares them.
 * One Ollama install serves both tool-capable families and completion-only
 * ones (tinyllama, phi-2, plain llama3, base non-instruct tags), so a
 * recipe-wide boolean is wrong in both directions — `false` locks every local
 * user out of the subagent loop, `true` starts loops that can never dispatch.
 *
 * Matching is on the family (the part before the `:` size/quant tag), anchored
 * so a family is never a prefix of a longer unrelated one. Version-sensitive
 * on purpose: `llama3` did NOT ship tool calling and `llama3.1` did, so the
 * pattern must not treat "llama3" as a prefix match for "llama3.1".
 *
 * Unlisted families answer false — fail-closed, matching the pre-existing
 * conservative posture. A user running a tool-capable model this list hasn't
 * caught up with can still route it explicitly; the honest long-term fix is a
 * runtime probe (`gbrain models doctor`) rather than a hardcoded list, since
 * this list WILL go stale exactly as the blanket `false` did.
 */
const TOOL_CAPABLE_LOCAL_FAMILIES = [
  /^qwen(2\.5|3|3\.5)(-coder|-instruct)?$/,
  /^qwq$/,
  /^llama(3\.[123]|4)(\.\d+)?$/,
  /^mistral(-nemo|-small|-large)?$/,
  /^mixtral$/,
  /^devstral$/,
  /^magistral$/,
  /^command-r(-plus|7b)?$/,
  /^firefunction-v2$/,
  /^hermes3$/,
  /^granite(3|3\.\d+)(-dense|-moe)?$/,
  /^nemotron(-mini)?$/,
  /^athene-v2$/,
  /^gpt-oss$/,
];

/**
 * Does this Ollama model id name a family known to support tool calling?
 *
 * @internal exported for tests.
 */
export function isToolCapableOllamaModel(modelId: string): boolean {
  const family = String(modelId).split(':')[0]?.trim().toLowerCase() ?? '';
  if (family === '') return false;
  return TOOL_CAPABLE_LOCAL_FAMILIES.some((re) => re.test(family));
}

export const ollama: Recipe = {
  id: 'ollama',
  name: 'Ollama (local)',
  tier: 'openai-compat',
  implementation: 'openai-compatible',
  base_url_default: 'http://localhost:11434/v1',
  auth_env: {
    required: [], // Ollama runs unauthenticated locally; users pass `ollama` as the key.
    optional: ['OLLAMA_BASE_URL', 'OLLAMA_API_KEY'],
    setup_url: 'https://ollama.ai',
  },
  touchpoints: {
    embedding: {
      // #2271: modern local embed models added so assertTouchpoint accepts them.
      models: [
        'nomic-embed-text',
        'mxbai-embed-large',
        'all-minilm',
        // Real Ollama library tags (verified 2026-08-08): the family is
        // published as `qwen3-embedding` with size tags, and Arctic Embed
        // 2.0 as `snowflake-arctic-embed2`. The earlier `qwen3-embed-8b` /
        // HF-style `snowflake-arctic-embed-l-v2` spellings stay listed so
        // brains initialized with them keep validating, but they never
        // matched a pullable Ollama tag.
        'qwen3-embedding:8b',
        'qwen3-embed-8b',
        'snowflake-arctic-embed2',
        'snowflake-arctic-embed-l-v2',
        'bge-m3',
      ],
      // #2051: per-model native dims. Ollama serves models spanning 384..4096,
      // so the recipe-wide default_dims below is only correct for nomic. Without
      // this map `init --embedding-model ollama:bge-m3` built a 768-wide column
      // for a model that emits 1024, and the mismatch only surfaced at first
      // insert. Resolved via `embeddingDimsForModel()`; unlisted models still
      // fall back to default_dims, and trust_custom_dims keeps an explicit
      // --embedding-dimensions override working for models not named here.
      model_dims: {
        'nomic-embed-text': 768,
        'mxbai-embed-large': 1024,
        'all-minilm': 384,
        'qwen3-embedding:8b': 4096,
        'qwen3-embed-8b': 4096,
        'snowflake-arctic-embed2': 1024,
        'snowflake-arctic-embed-l-v2': 1024,
        'bge-m3': 1024,
      },
      default_dims: 768, // nomic-embed-text native dim
      trust_custom_dims: true, // #2271: local models carry varied native dims
      cost_per_1m_tokens_usd: 0,
      price_last_verified: '2026-04-20',
      // Ollama's batch capacity depends on the locally loaded model + the
      // OLLAMA_NUM_PARALLEL config; no static cap to declare. v0.32 (#779).
      no_batch_cap: true,
    },
    expansion: {
      models: ['qwen2.5-coder:14b'],
      cost_per_1m_tokens_usd: 0,
      price_last_verified: '2026-06-26',
    },
    chat: {
      // Model ids are user-managed; this informational default makes the chat
      // capability visible in provider discovery without constraining custom tags.
      models: ['qwen3.5:4b', 'qwen3:8b', 'qwen2.5-coder:14b', 'mistral-nemo', 'llama3.3'],
      // Chat completion is provider-wide, but tool support varies by loaded
      // model — so the gate is per-model rather than a recipe-wide boolean.
      // A blanket `false` here made every local model `unusable:no_tools` at
      // the three subagent gates (minions/queue.ts, minions/handlers/subagent.ts,
      // doctor's search-eval check), which locked local-only installs out of
      // the agent loop entirely.
      supports_tools: isToolCapableOllamaModel,
      // Same gate: v0.38 moved stable tool_call_id generation gbrain-side
      // (ordinal + uuid v7 persisted in subagent_tool_executions), so loop
      // safety no longer depends on a provider's own id stability — only on
      // whether the model can emit tool calls at all.
      supports_subagent_loop: isToolCapableOllamaModel,
      // No prompt-prefix caching: local inference re-reads the prompt each
      // turn. Costs nothing but wall-clock, so the loop still runs (the
      // capability gate treats this as `degraded:no_caching`, not unusable).
      supports_prompt_cache: false,
      // Constrained decoding is a SERVER property here, not a model one:
      // Ollama's OpenAI-compatible layer honors a strict `json_schema`
      // response_format for whatever model is loaded, so this is recipe-wide.
      // If a backend ever rejects it at call time, gateway.expand() already
      // records the rejection and falls back to the schemaless text path.
      supports_structured_outputs: true,
      // Provider-wide routing ceiling only; Ollama still enforces each loaded
      // model's actual context window at request time.
      max_context_tokens: 128_000,
      cost_per_1m_input_usd: 0,
      cost_per_1m_output_usd: 0,
      price_last_verified: '2026-08-18',
      // Local cold starts can exceed the generic 5-second provider probe.
      default_timeout_ms: 180_000,
    },
  },
  setup_hint: 'Install Ollama from https://ollama.ai, then `ollama pull nomic-embed-text` for embeddings and `ollama pull qwen3.5:4b` for local chat. Start it with `ollama serve`. Custom local model tags are accepted; the agent/subagent loop additionally needs a model whose template defines tool calling (qwen2.5+/qwen3+, llama3.1+, mistral-nemo, command-r, hermes3, granite3 — see isToolCapableOllamaModel).',
};
