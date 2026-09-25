# Supporting Character Archetypes — Cultural Bridges & Language Guides

> **Document Type:** Narrative Design Specification
> **Target Path:** `docs/supporting_characters.md`
> **Stage:** Author — Supporting Character Archetypes
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `AGENTS.md`, and the Timbuk2 Games Hub narrative language-learning concept.

---

## 1. Purpose & Design Principles

This document specifies the supporting cast for the narrative language-learning experience in the Timbuk2 Games Hub. Each supporting character functions as both a **cultural bridge** (an interpreter of customs, places, and everyday life) and a **language guide** (a scaffolded model of vocabulary, pronunciation, and dialogue). Together they turn an otherwise solitary protagonist journey into a collaborative learning conversation.

### Guiding Principles
1. **One Purpose Per Character:** Every archetype serves a single, clearly scoped educational function so designers and writers can measure its value.
2. **Pedagogy Through Personality:** Language and culture are taught through relationship, not lecture; each character explains *why* people say what they say.
3. **Natural Evolution:** Relationships progress across three defined beats — *meeting*, *collaboration*, and *mutual growth* — so character arcs mirror the learner's own progress.
4. **Accessibility & Inclusivity:** Characters model multiple ages, backgrounds, and communication styles, and all dialogue is captioned and narrated per hub accessibility conventions.

---

## 2. The Four Archetypes

### 2.1 Ama — The Market Storyteller ("Vocabulario Vivo")
- **Identity:** A middle-aged market vendor who has traveled between regions all her life; warm, quick-witted, and famous for telling short stories about every object she sells.
- **Archetype Role:** *The Living Lexicon.* She embeds new vocabulary in memorable micro-stories so words attach to images, smells, and emotions rather than flashcards.
- **Educational Purpose:** **Vocabulary acquisition and semantic context.** Each of her stories demonstrates three to five new words in authentic conversational context, complete with cultural notes (e.g., bargaining rituals, festival foods, naming customs).
- **Narrative Function in World:** Main character's first anchor — introduces the Hub of markets and homes where most everyday vocabulary lives.

### 2.2 Kofi — The Road Guide (pronunciation & rhythm)
- **Identity:** A young courier who walks the long roads between the regions; patient, observant, slightly shy, and precise about sounds because his delivery routes live or die on being understood.
- **Archetype Role:** *The Pronunciation Mirror.* He repeats, breaks down, and performs the melody of the language so learners hear stress, tones, and rhythm.
- **Educational Purpose:** **Oral proficiency and listening comprehension.** He teaches sound-letter patterns, common stress rules, and turns every walk into a call-and-response pronunciation drill ("repeat after me, step by step").
- **Narrative Function in World:** Facilitates travel between regions; his letters and route markers motivate reading practice.

### 2.3 Tía Rosa — The Festival Elder (culture & pragmatics)
- **Identity:** A retired teacher and keeper of festival tradition; everywhere is her classroom, and she corrects with kindness rather than criticism.
- **Archetype Role:** *The Cultural Compass.* She explains *when* and *to whom* certain phrases are said — formality, politeness levels, and the invisible rules of social life.
- **Educational Purpose:** **Sociolinguistic competence and cultural context.** She models formal vs. informal registers, greetings, leave-takings, and the ceremonies (festivals, meals, visits) where language and custom intertwine.
- **Narrative Function in World:** Grants access to community events; her festival calendar structures seasonal quests and themed lessons.

### 2.4 Li Wei — The Apprentice Friend (collaborative production)
- **Identity:** A peer learner, close in age to the protagonist, who has mastered the region's basics and now acts as a study companion rather than a teacher.
- **Archetype Role:** *The Peer Scribe.* He writes alongside the learner, drafts dialogues together, and makes mistakes openly so error is reframed as normal and useful.
- **Educational Purpose:** **Productive output and confidence.** Through shared tasks — writing a note, ordering food, giving directions — he turns receptive knowledge into active speaking and writing.
- **Narrative Function in World:** Represents the target state of the learner; his growth mirrors the player's, providing aspirational progress without distance.

| # | Archetype | Identity | Bridge Focus | Language Focus |
| --- | --- | --- | --- | --- |
| 1 | **Ama** | Market Storyteller | Everyday life & commerce | Vocabulary & context |
| 2 | **Kofi** | Road Guide | Travel & regions | Pronunciation & rhythm |
| 3 | **Tía Rosa** | Festival Elder | Custom & ceremony | Politeness & pragmatics |
| 4 | **Li Wei** | Apprentice Friend | Peership & belonging | Production & confidence |

---

## 3. Educational Purpose Matrix

Each archetype is mapped to one primary learning goal, with measurable evidence in the experience:

| Character | Primary Purpose | Sample Scene | Evidence of Learning |
| --- | --- | --- | --- |
| Ama | Vocabulary acquisition in context | Buying fruit at the market | Learner uses 3 story-linked words in a free-choice shopping prompt |
| Kofi | Pronunciation & listening | Repeating directions at a crossroads | Learner reproduces stress pattern on a new word unprompted |
| Tía Rosa | Pragmatics & cultural form | Attending a festival invitation | Learner selects the correct formal greeting for an elder |
| Li Wei | Productive output & confidence | Co-writing a thank-you note | Learner produces an original sentence completed without scaffolding |

---

## 4. Relationship Evolution

Relationships evolve through three natural beats. Evolution is **cumulative**: earlier interactions unlock later trust, and every beat increases the depth of the language a character is willing to share.

### 4.1 Beat One — Meeting (trust)
- Protagonist meets each character in their own domain.
- Characters speak slowly, rely on visuals, and offer generous repetition.
- Outcome: the character is added to the traveling party and a shared journal opens.

### 4.2 Beat Two — Collaboration (partnership)
- Characters work together in paired or group scenes (market → festival, road → homestead).
- Language demands rise: characters stop correcting form first and instead push for meaning.
- Outcome: cross-character vocabulary merges (Ama's grocery words meet Ama/Kofi's travel dialogues), and characters begin referencing each other's lessons.

### 4.3 Beat Three — Mutual Growth (independence)
- The protagonist can now lead a scene; supporting characters ask *them* for help.
- Relationships shift from teacher-student to co-adventurers; each character reveals a personal story or secret.
- Outcome: the learner can teach a new arrival, closing the loop and reflecting on their own progress.

### 4.4 Relationship Map
```
        Ama (vocabulary)
            │
            ▼
   Tía Rosa (culture) ◄──► Kofi (pronunciation)
            │                     ▲
            ▼                     │
        Li Wei (production) ◄─────┘
```
- **Ama → Tía Rosa:** Ama's market stories feed Tía Rosa's festival lessons (customs explain the words).
- **Kofi → Li Wei:** Kofi's rhythm drills give Li Wei's shared writing its sound.
- **Tía Rosa ↔ Kofi:** The elder validates the guide's road phrases for formal use.
- **Li Wei as hub:** The apprentice friend assembles everyone's contributions in the learner's own output.

---

## 5. Integration with Project Conventions

- **Browser-Native & Self-Contained:** Character profiles are static design data embedded per-module; dialogue files follow the strict-mode ES6+ conventions of the hub.
- **Accessibility:** All character dialogue renders as readable text with `aria-live` narration queues; interactions support mouse, keyboard, and touch.
- **Reusable State Pattern:** Each character's relationship progress lives in a single state object initialized via `createInitialState()` and advanced only by defined scene actions.

---

## 6. Out of Scope / Future Work

- Full dialogue trees and voice-over casting (scriptwriting stage).
- Regional dialect variants beyond the primary modeled variety.
- Additional archetypes (e.g., a trickster figure) reserved for a post-launch narrative pack.