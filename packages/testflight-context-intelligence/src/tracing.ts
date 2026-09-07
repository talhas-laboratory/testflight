import { createHash } from "node:crypto";
import {
  appendFile,
  mkdir,
  readFile,
  readdir,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import { resolve } from "node:path";
import type {
  ContextRunTrace,
  ContextTraceEvent,
  ContextTraceHeader,
  ContextTraceStore,
  RetrievedKnowledge,
  TraceEvidenceReference,
} from "./contracts.js";

const RUN_ID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class JsonFileContextTraceStore implements ContextTraceStore {
  readonly #directory: string;
  readonly #maxRuns: number;
  readonly #maxAgeMs: number;
  readonly #sequences = new Map<string, number>();
  readonly #writes = new Map<string, Promise<void>>();

  constructor(
    directory: string,
    retention: { maxRuns?: number; maxAgeDays?: number } = {},
  ) {
    this.#directory = resolve(directory);
    this.#maxRuns = retention.maxRuns ?? 200;
    this.#maxAgeMs = (retention.maxAgeDays ?? 30) * 86_400_000;
  }

  #runDirectory(runId: string): string {
    if (!RUN_ID.test(runId)) throw new Error("invalid context trace run id");
    return resolve(this.#directory, runId);
  }

  async start(header: ContextTraceHeader): Promise<void> {
    await mkdir(this.#directory, { recursive: true, mode: 0o700 });
    const runDirectory = this.#runDirectory(header.runId);
    await mkdir(runDirectory, { mode: 0o700 });
    await mkdir(resolve(runDirectory, "evidence"), { mode: 0o700 });
    await writeFile(
      resolve(runDirectory, "header.json"),
      `${JSON.stringify(header, null, 2)}\n`,
      { encoding: "utf8", flag: "wx", mode: 0o600 },
    );
    await writeFile(resolve(runDirectory, "events.jsonl"), "", {
      encoding: "utf8",
      flag: "wx",
      mode: 0o600,
    });
    this.#sequences.set(header.runId, 0);
    await this.#prune(header.runId);
  }

  async append(runId: string, event: ContextTraceEvent): Promise<void> {
    const previous = this.#writes.get(runId) ?? Promise.resolve();
    const next = previous.then(async () => {
      const sequence = this.#sequences.get(runId);
      if (sequence === undefined)
        throw new Error("context trace was not started");
      const stored = {
        ...event,
        sequence,
        at: event.at ?? new Date().toISOString(),
      };
      await appendFile(
        resolve(this.#runDirectory(runId), "events.jsonl"),
        `${JSON.stringify(stored)}\n`,
        { encoding: "utf8", mode: 0o600 },
      );
      this.#sequences.set(runId, sequence + 1);
    });
    this.#writes.set(runId, next);
    try {
      await next;
    } finally {
      if (this.#writes.get(runId) === next) this.#writes.delete(runId);
    }
  }

  async putEvidence(
    runId: string,
    item: RetrievedKnowledge,
  ): Promise<TraceEvidenceReference> {
    const serialized = JSON.stringify(item);
    const hash = createHash("sha256").update(serialized).digest("hex");
    const path = resolve(this.#runDirectory(runId), "evidence", `${hash}.json`);
    try {
      await writeFile(path, `${JSON.stringify(item, null, 2)}\n`, {
        encoding: "utf8",
        flag: "wx",
        mode: 0o600,
      });
    } catch (error) {
      if (
        !(error instanceof Error && "code" in error && error.code === "EEXIST")
      )
        throw error;
    }
    return {
      hash,
      retrievalId: item.id,
      ...(item.sourceUrl ? { sourceUrl: item.sourceUrl } : {}),
      entityIds: item.entityIds ?? [],
    };
  }

  async read(runId: string): Promise<ContextRunTrace> {
    const runDirectory = this.#runDirectory(runId);
    const [headerText, eventsText, evidenceFiles] = await Promise.all([
      readFile(resolve(runDirectory, "header.json"), "utf8"),
      readFile(resolve(runDirectory, "events.jsonl"), "utf8"),
      readdir(resolve(runDirectory, "evidence")),
    ]);
    const evidenceEntries = await Promise.all(
      evidenceFiles
        .filter((name) => /^[0-9a-f]{64}\.json$/.test(name))
        .map(
          async (name) =>
            [
              name.slice(0, -5),
              JSON.parse(
                await readFile(resolve(runDirectory, "evidence", name), "utf8"),
              ) as RetrievedKnowledge,
            ] as const,
        ),
    );
    return {
      header: JSON.parse(headerText) as ContextTraceHeader,
      events: eventsText
        .split("\n")
        .filter(Boolean)
        .map((line) => JSON.parse(line) as ContextTraceEvent),
      evidence: Object.fromEntries(evidenceEntries),
    };
  }

  async #prune(currentRunId: string): Promise<void> {
    const now = Date.now();
    const candidates = await Promise.all(
      (await readdir(this.#directory, { withFileTypes: true }))
        .filter((entry) => entry.isDirectory() && RUN_ID.test(entry.name))
        .map(async (entry) => ({
          runId: entry.name,
          modified: (await stat(resolve(this.#directory, entry.name))).mtimeMs,
        })),
    );
    candidates.sort((left, right) => right.modified - left.modified);
    const expired = candidates.filter(
      (candidate, index) =>
        candidate.runId !== currentRunId &&
        (index >= this.#maxRuns || now - candidate.modified > this.#maxAgeMs),
    );
    await Promise.all(
      expired.map((candidate) =>
        rm(this.#runDirectory(candidate.runId), {
          recursive: true,
          force: true,
        }),
      ),
    );
  }
}
