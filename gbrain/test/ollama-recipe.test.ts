/**
 * Ollama recipe — chat touchpoint shape.
 *
 * The extract-atoms phase registers config-selected chat models through the
 * gateway's extended-model path so local/user-managed providers (Ollama) can
 * serve the phase without hosted API keys. That wiring presumes the recipe
 * DECLARES a chat touchpoint with a non-empty allowlist — assertTouchpoint
 * rejects a provider whose touchpoint is missing, and an empty models list
 * would leave no default-eligible model at all.
 */

import { describe, test, expect } from 'bun:test';
import { getRecipe } from '../src/core/ai/recipes/index.ts';

describe('Ollama recipe — chat touchpoint', () => {
  test('declares a chat touchpoint', () => {
    const r = getRecipe('ollama');
    expect(r).toBeDefined();
    expect(r!.touchpoints.chat).toBeDefined();
  });

  test('chat models list is non-empty and every entry is a non-empty string', () => {
    const m = getRecipe('ollama')!.touchpoints.chat!.models;
    expect(Array.isArray(m)).toBe(true);
    expect(m.length).toBeGreaterThan(0);
    for (const model of m) {
      expect(typeof model).toBe('string');
      expect(model.length).toBeGreaterThan(0);
    }
  });

  test('local chat gates tool work per model, and never claims prompt caching', () => {
    // Tool + subagent support is declared as a per-model predicate: an Ollama
    // endpoint serves tool-capable families and completion-only ones alike, so
    // a recipe-wide boolean is wrong in both directions. Structured output IS
    // recipe-wide — constrained decoding is enforced by the server, not the
    // model. Prompt caching stays false: local inference re-reads each turn.
    const tp = getRecipe('ollama')!.touchpoints.chat!;
    expect(typeof tp.supports_tools).toBe('function');
    expect(typeof tp.supports_subagent_loop).toBe('function');
    expect((tp.supports_tools as (m: string) => boolean)('qwen3.5:4b')).toBe(true);
    expect((tp.supports_tools as (m: string) => boolean)('tinyllama')).toBe(false);
    expect((tp.supports_subagent_loop as (m: string) => boolean)('qwen3.5:4b')).toBe(true);
    expect((tp.supports_subagent_loop as (m: string) => boolean)('tinyllama')).toBe(false);
    expect(tp.supports_structured_outputs).toBe(true);
    expect(tp.supports_prompt_cache).toBe(false);
  });
});
