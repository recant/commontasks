/**
 * SLM/local profile: tier defaults + the fail-loud subagent gate.
 *
 * Two behaviors are pinned here, and the second is a privacy invariant rather
 * than an ergonomic one:
 *
 *   1. A keyless install with a local runtime resolves tier defaults to that
 *      runtime instead of an Anthropic model whose key is absent — WITHOUT
 *      changing resolution for any install that does carry a cloud key.
 *   2. Under GBRAIN_LOCAL_ONLY, a subagent tier that resolves to a
 *      tool-incapable model must THROW. Upstream falls back to
 *      TIER_DEFAULTS.subagent with a stderr warn; under a local-only promise
 *      that fallback would ship the job's prompts and every retrieved page to
 *      a hosted API. A warning is not sufficient because the job still runs.
 */

import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import {
  resolveTierDefault,
  resolveModel,
  isLocalOnlyProfile,
  isLocalRuntimeModel,
  localTierDefault,
  TIER_DEFAULTS,
  DEFAULT_LOCAL_CHAT_MODEL,
  PROVIDER_TIER_DEFAULTS,
} from '../../src/core/model-config.ts';

const TOUCHED = ['GBRAIN_LOCAL_ONLY', 'GBRAIN_LOCAL_MODEL', 'GBRAIN_MODEL'] as const;
let saved: Record<string, string | undefined> = {};

beforeEach(() => {
  saved = Object.fromEntries(TOUCHED.map((k) => [k, process.env[k]]));
  for (const k of TOUCHED) delete process.env[k];
});

afterEach(() => {
  for (const k of TOUCHED) {
    if (saved[k] === undefined) delete process.env[k];
    else process.env[k] = saved[k] as string;
  }
});

describe('local tier defaults', () => {
  it('leaves keyed installs resolving exactly as before', () => {
    // The local entry is appended LAST, so a cloud-keyed install is untouched.
    expect(resolveTierDefault('subagent', { ANTHROPIC_API_KEY: 'x' })).toBe(TIER_DEFAULTS.subagent);
    expect(resolveTierDefault('deep', { ANTHROPIC_API_KEY: 'x' })).toBe(TIER_DEFAULTS.deep);
    expect(resolveTierDefault('subagent', { OPENAI_API_KEY: 'x' }).startsWith('openai:')).toBe(true);
    // No keys and no local runtime: unchanged honest-degradation behavior.
    expect(resolveTierDefault('subagent', {})).toBe(TIER_DEFAULTS.subagent);
  });

  it('routes a keyless install with a local runtime to that runtime', () => {
    const env = { OLLAMA_BASE_URL: 'http://localhost:11434/v1' };
    for (const tier of ['utility', 'reasoning', 'deep', 'subagent'] as const) {
      expect(resolveTierDefault(tier, env)).toBe(DEFAULT_LOCAL_CHAT_MODEL);
    }
  });

  it('keeps the local provider entry last in the precedence list', () => {
    expect(PROVIDER_TIER_DEFAULTS.at(-1)?.provider).toBe('ollama');
  });

  it('lets GBRAIN_LOCAL_ONLY outrank a stray cloud key', () => {
    // The flag is a promise that nothing leaves the box; a leftover key in the
    // environment must not silently reclaim the tier defaults.
    const env = { GBRAIN_LOCAL_ONLY: '1', ANTHROPIC_API_KEY: 'x', OPENAI_API_KEY: 'y' };
    expect(resolveTierDefault('subagent', env)).toBe(DEFAULT_LOCAL_CHAT_MODEL);
  });

  it('honors GBRAIN_LOCAL_MODEL and prefixes a bare tag', () => {
    expect(localTierDefault('subagent', { GBRAIN_LOCAL_MODEL: 'ollama:qwen3:8b' })).toBe('ollama:qwen3:8b');
    // A bare family name is still a valid thing to type; assume the local runtime.
    expect(localTierDefault('subagent', { GBRAIN_LOCAL_MODEL: 'mistral-nemo' })).toBe('ollama:mistral-nemo');
    expect(localTierDefault('subagent', { GBRAIN_LOCAL_MODEL: '   ' })).toBe(DEFAULT_LOCAL_CHAT_MODEL);
  });

  it('parses the local-only flag conservatively', () => {
    for (const v of ['1', 'true', 'TRUE', 'yes', 'on']) {
      expect(isLocalOnlyProfile({ GBRAIN_LOCAL_ONLY: v })).toBe(true);
    }
    for (const v of ['0', 'false', 'no', 'off', '', undefined]) {
      expect(isLocalOnlyProfile({ GBRAIN_LOCAL_ONLY: v })).toBe(false);
    }
  });
});

describe('local runtime detection', () => {
  it('recognizes the OpenAI-compatible local runtimes', () => {
    // These decide whether the subagent handler auto-enables the gateway loop:
    // the legacy Anthropic-direct path cannot speak to either, so requiring a
    // config flag first would only produce a confusing refusal.
    expect(isLocalRuntimeModel('ollama:qwen3.5:4b')).toBe(true);
    expect(isLocalRuntimeModel('llama-server:my-gguf')).toBe(true);
    expect(isLocalRuntimeModel('anthropic:claude-sonnet-4-6')).toBe(false);
    expect(isLocalRuntimeModel('openai:gpt-5.2')).toBe(false);
    // A bare id carries no provider, so it is not a local runtime by this test.
    expect(isLocalRuntimeModel('claude-sonnet-4-6')).toBe(false);
  });
});

describe('subagent gate under GBRAIN_LOCAL_ONLY', () => {
  // `fallback` is required by ResolveModelOpts but never reached here: every
  // case below resolves at the env-var step (6), which is the branch that runs
  // enforceSubagentCapable. A distinctive value makes it obvious if that ever
  // stops being true.
  const subagent = {
    tier: 'subagent',
    envVar: 'GBRAIN_MODEL',
    fallback: 'anthropic:unreachable-fallback-sentinel',
  } as const;

  it('still falls back to the cloud default when the flag is NOT set', async () => {
    // Upstream behavior must be preserved byte-for-byte for everyone else.
    process.env.GBRAIN_MODEL = 'ollama:tinyllama';
    expect(await resolveModel(null, subagent)).toBe(TIER_DEFAULTS.subagent);
  });

  it('throws instead of silently routing off-machine when the flag IS set', async () => {
    process.env.GBRAIN_LOCAL_ONLY = '1';
    process.env.GBRAIN_MODEL = 'ollama:tinyllama';
    const err = await resolveModel(null, subagent).then(
      (model) => new Error(`expected a throw, got "${model}"`),
      (e: Error) => e,
    );
    expect(err.message).toContain('lacks tool-calling support');
    expect(err.message).toContain('GBRAIN_LOCAL_ONLY');
    // The error must NOT be a quiet substitution of the cloud model.
    expect(err.message).not.toBe(TIER_DEFAULTS.subagent);
    expect((err as { fix?: string }).fix ?? '').toContain('models.tier.subagent');
  });

  it('throws on an unknown provider under the flag rather than falling back', async () => {
    process.env.GBRAIN_LOCAL_ONLY = 'true';
    process.env.GBRAIN_MODEL = 'not-a-provider:whatever';
    await expect(resolveModel(null, subagent)).rejects.toThrow(/unrecognized provider/);
  });

  it('passes a tool-capable local model straight through', async () => {
    process.env.GBRAIN_LOCAL_ONLY = '1';
    process.env.GBRAIN_MODEL = 'ollama:qwen3.5:4b';
    expect(await resolveModel(null, subagent)).toBe('ollama:qwen3.5:4b');
  });
});
