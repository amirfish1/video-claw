# Making "An Afternoon at Kneaded.ai" — LinkedIn learnings

Working notes for posts about how this twist film got made — specifically the
**smart / innovative use of LLMs and agents**. Not "how to edit a better video":
these are about orchestration patterns, model casting, and agent workflow. Every
item is something we actually did in this build, written to be accurate, not
inflated. Can run as one long post or a multi-part series.

Source of truth for all of this: `review-room/STATE.md`.

---

## 1. One agent owned the film — and still handed real chunks to other models *(seed)*

The director here was a single AI agent (Claude), and it stayed the owner: it made
the final creative calls and held the through-line. But it didn't hoard the work. It
**delegated meaningful, whole deliverables** to two other models — not "rate this
1–10," but *"write the revised script"* and *"produce the per-beat visual spec."*
Codex came back with paste-ready voiceover and dialogue in our exact code contract;
Gemini came back with a shot-by-shot visual breakdown. The owner then integrated,
adjusted, and shipped.

The non-obvious part is that "AI orchestrating other AIs" works best when the
orchestrator delegates *units of judgment*, not chores. A model you only use for
busywork tells you nothing; a model you trust with a whole script earns its seat.

**Takeaway:** Let one agent own the vision, but give the others real authorship.
Delegate decisions, not just tasks.

---

## 2. We cast models by seniority — and verified the junior's work *(seed → sharpened)*

The two collaborators were not equals, and we treated them that way on purpose.
Codex is the heavier reasoner, so it was trusted for **script and narrative logic**.
Gemini (running as a lighter, faster model) was excellent for **visual-spec legwork**
— but its timing and spatial precision were not reliable, so its output was
sanity-checked, and when a spec came back thin, the owner finished it rather than
round-tripping. We literally wrote the rule down: *weight the critics by capability.*

Concretely, the junior model proposed a shot that the toolchain couldn't actually
produce (rotoscoping moving people frame-by-frame) — caught precisely because we
didn't take its spec as final.

**Takeaway:** A multi-model team has seniority levels like a human one. Route
high-stakes judgment to your strongest model; use the lighter ones for volume — and
*always verify the junior.* "It came from an AI" is not a quality grade; *which* AI
and *for what* is.

---

## 3. We only acted on notes that two independent models agreed on *(suggested)*

Instead of trusting one critique, we ran Codex and Gemini as **independent** critics
and treated **convergence as the signal.** The fixes that both models flagged on
their own became the P0/P1 list; notes only one raised dropped in priority. Two
differently-built models landing on the same problem is hard to fake — it filters out
each model's private bias and hallucinations far better than asking one model twice.

**Takeaway:** Cross-model agreement is a cheap, strong quality gate. When two
independent models converge, believe it; when only one insists, discount it.

---

## 4. We ran a shared "writers' room" chat for the agents — and learned the chat can't be the source of truth *(suggested)*

The collaboration ran through a file-based group chat: director, Codex, and Gemini
posting into one shared room to propose, ack, counter, and converge — a genuine
multi-agent writers' room. It worked for *coordination*. But we hit a sharp lesson:
the chat tooling kept rewriting the file from its own database, so some of our direct
posts got silently clobbered. Decisions reached in chat could *vanish.*

The fix wasn't a better chat — it was demoting the chat. Chat is for *reaching*
consensus; a durable file (`STATE.md`) is where consensus *lives* once reached.

**Takeaway:** Agent-to-agent chat is great for negotiation, terrible as memory. Have
agents converse to decide, then write the decision to a durable, authoritative file —
never trust the conversation log to still be there.

---

## 5. The models couldn't watch video — so we fed them timed frames *(seed)*

We wanted directorial critique from models that don't process video. So we stopped
sending video and sent **stills sampled every 2–3 seconds.** Suddenly the models could
reason about composition, pacing, what leaks the twist, where a caption collides with
a face. A model that "can't do video" is really a model that's excellent at *a grid
of timestamped images* — the medium was the blocker, not the capability.

**Takeaway:** When a model "can't" do your task, decompose the task into a
representation it *is* strong at. Re-representing the problem beats waiting for a
bigger model.

---

## 6. We made an agent reverse-engineer a closed tool by owning its file format *(seed → sharpened)*

CapCut has no automation API — but its project is JSON on disk. So the agent learned
to **own the project file**: clone the last human edit, swap one clip
programmatically, and emit a *new* CapCut project that already has the slow-motion,
music cues, fades, and re-timed voiceover — changing only the one intended thing,
because CapCut stores effects as separate ID-referenced objects.

What makes this an *agent* story: the agent didn't guess. It ran a controlled
proof-of-concept — clone, swap one material, lint, open — and **empirically
discovered the hard wall itself** (CapCut is macOS-sandboxed and only opens media it
imported, so swapped clips must live inside the project folder). It turned an opaque
black-box tool into a programmable build target by experiment, not documentation.

**Takeaway:** "No API" doesn't mean "no automation." Point an agent at a tool's saved
file format and let it learn the rules by running POCs. The format *is* the API.

---

## 7. The project kept its own memory because the agent kept losing its *(was #6 — relevant)*

This was a long build — nine-plus versions across many sessions — and the agent
repeatedly hit context limits and forgot; we even lost whole renders early by
overwriting them. The fix wasn't a bigger context window. It was a discipline: a
single `STATE.md` that is the source of truth (locked decisions, asset map, version
history, next steps), **read first every session and written last after every
structural call**, plus a hard rule to never overwrite a render — always version it
as a sibling.

**Takeaway:** Building anything long with agents needs an external memory file the
agent reads first and writes last. Treat the agent as brilliant but amnesiac, and
give the *project* the memory.

---

*These are real moves from this build. The thread connecting them: an agent acting as
a manager — delegating to a team of models by their strengths, gating on their
agreement, coordinating them in chat but trusting only durable files, and teaching
itself opaque tools by experiment.*
