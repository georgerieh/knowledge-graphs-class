# Graph Database Schema for an Academic Citation Network Modelization and Anti Genericity Appendix

Designing a robust graph database schema for an academic citation network requires balancing analytical performance (for graph algorithms like PageRank, community detection, and bibliographic coupling) with transactional flexibility. 

Below is an optimal property graph schema structured around core academic entities.

---

## 1. Node Types & Properties

The schema centers on five main node labels to capture researchers, publications, institutions, publishing venues, and thematic topics.

**Proposed by AI**
| Node Label | Key Unique Identifier | Core Properties | Description |
| :--- | :--- | :--- | :--- |
| **`Paper`** | `paperId` (DOI or UUID) | `title`, `abstract`, `year`, `doi`, `citationCount`, `pageRank` | Represents research articles, preprints, books, or conference proceedings. |
| **`Author`** | `authorId` (ORCID or UUID) | `name`, `hIndex`, `totalCitations`, `email` | Represents individual researchers. |
| **`Institution`** | `institutionId` | `name`, `country`, `type` (e.g., University, Corporate Lab) | Represents universities, research centers, or corporate entities. |
| **`Venue`** | `venueId` | `name`, `type` (Journal / Conference), `issn`, `publisher` | Represents where papers are published. |
| **`Topic`** | `topicId` | `name`, `category`, `level` (e.g., Subfield vs. Broad Field) | Represents academic fields, keywords, or semantic concepts. |

**Adapted by me**
| Node Label | Key Unique Identifier | Core Properties | Description |
| :--- | :--- | :--- | :--- |
| **`Article`** | `id` (given by dataset) | `title`, `rebuilt_abstract` (was given in inverted format), `year`, `doi`, ~~citationCount~~, ~~pageRank~~ (not used in the current project) | Represents research articles **only**, ~~preprints, books, or conference proceedings.~~ |
| **`Author`** | `id` (given by dataset) | `name`, ~~hIndex~~ (calculated in runtime), ~~totalCitations~~, `email`, `institution` | Represents individual researchers. |
| **`Institution`** | `institutionId` | `name`, ~~`country`, `type`~~. This is the only information available | Represents universities, research centers, or corporate entities. |
| **`Venue`** | `venueId` | `name`, `type` (Journal only ~~/ Conference~~), ~~`issn`~~, `publisher` | Represents where papers are published, but not used in the project for now. |
| **~~Topic~~ Keyword** | `id` | `name`, ~~`category`, `level`~~ (Extracted from fielf of science attribute) | Represents academic fields, keywords, or semantic concepts. |

---

## 2. Relationship Types & Properties

Relationships define how nodes interact, complete with directional semantics and optional weights for graph algorithms.
**By AI**
* **`(:Author)-[:WROTE {authorOrder: Integer}]->(:Paper)`**
  * *Properties:* `authorOrder` (sequence of authorship, e.g., 1 for first author), `correspondingAuthor` (Boolean).
* **`(:Author)-[:AFFILIATED_WITH {yearStart: Integer, yearEnd: Integer}]->(:Institution)`**
  * *Properties:* Temporal tracking of where authors worked during specific publishing windows.
* **`(:Paper)-[:PUBLISHED_IN]->(:Venue)`**
  * *Direction:* Paper points to Venue. Links a publication to its journal or conference.
* **`(:Paper)-[:CITES {context: String}]->(:Paper)`**
  * *Properties:* `context` (e.g., background, methodology, contradiction), `section` (e.g., introduction, related work). **This is the core citation backbone.**
* **`(:Paper)-[:BELONGS_TO {weight: Float}]->(:Topic)`**
  * *Properties:* `weight` or `relevanceScore` (0.0 to 1.0) derived from classification models (e.g., BERTopic or LDA).

**By me**
```
(:Article) ──[:WRITTEN_BY]──> (:Author)
   └──────[:REFERENCES] -> (:Article)
   └──────[:PUBLISHED_IN] -> (:Venue)
   └──────[:HAS_KEYWORD]──────> (:Keyword)
 (:Author) ──────[:WORKS_AT]──────> (:Institution)
```
The schema is much simplier to make the project light weight and based on the available data
---

## 3. Recommended Indexes and Constraints

For large citation networks (e.g., millions of papers and citations), graph traversals rely heavily on proper indexing. Set up the following database constraints and indexes (example using Cypher syntax):

**By AI**
```cypher
// Uniqueness Constraints
CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.paperId IS UNIQUE;
CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.authorId IS UNIQUE;
CREATE CONSTRAINT institution_id_unique IF NOT EXISTS FOR (i:Institution) REQUIRE i.institutionId IS UNIQUE;
CREATE CONSTRAINT venue_id_unique IF NOT EXISTS FOR (v:Venue) REQUIRE v.venueId IS UNIQUE;
CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.topicId IS UNIQUE;

// Performance Indexes for text search and filtering
CREATE INDEX paper_year_idx IF NOT EXISTS FOR (p:Paper) ON (p.year);
CREATE INDEX author_name_idx IF NOT EXISTS FOR (a:Author) ON (a.name);
```

**By me**
```
CREATE CONSTRAINT IF NOT EXISTS FOR (u:Author) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Article) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (v:Venue) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE;
CREATE INDEX author_idx FOR (u:Author) on (u.id);"
CREATE INDEX article_idx FOR (t:Article) on (t.id);
CREATE INDEX venue_idx FOR (v:Venue) on (v.id);
CREATE INDEX keywords_idx FOR (k:Keyword) on (k.id);
CREATE INDEX institution_idx FOR (i:Institution) on (i.id);
```