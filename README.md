# Banking RAG Assistant (LlamaIndex)

A small retail-banking assistant that answers customer and staff questions from two sources: bank policy documents and a customer database. It combines techniques from the "Gen AI - RAG Application Development using LlamaIndex" course.

## Problem

Bank staff and customers need quick answers that come from two very different places:

1. **Policy questions** ("What is the overdraft fee?", "How many days do I have to dispute a card transaction?"). The answers live in long policy documents. Reading them manually is slow, and a general-purpose chatbot may invent fees or rules that do not exist.
2. **Customer data questions** ("What is Amit's savings balance?", "Which account had the largest salary credit?"). The answers live in a database. Non-technical users cannot write SQL, and a plain language model has no access to the data.

A single search or single model call cannot handle both. Policy text does not contain balances, and a database does not contain fee rules. Sensitive data also needs to be handled carefully, so the assistant must not reveal OTPs or card numbers.

## Solution

The project splits the work across three parts, and an agent decides which one to use:

| Part | How it solves a piece of the problem | Where it lives |
|---|---|---|
| **Policy search (RAG)** | Policy documents are split into chunks and converted to embeddings with `text-embedding-3-small`, then stored in a `VectorStoreIndex`. For each question, the most relevant chunks are retrieved and the LLM answers only from them, which keeps answers tied to the actual policy text. | `docs/`, `rag_app.py` (`build_policy_tool`) |
| **Customer data (text-to-SQL)** | `NLSQLTableQueryEngine` gives the LLM the schema of the `customers`, `accounts` and `transactions` tables. It writes a SQL query, runs it on `bank.db`, and returns a plain-language answer. Users never see or write SQL. | `setup_db.py`, `rag_app.py` (`build_sql_tool`) |
| **Agent routing** | A `ReActAgent` receives both tools, each with a description. For each question it reasons about which tool fits, calls it, and combines results when needed. Policy questions go to `policy_search`, and balance or transaction questions go to `customer_data`. | `rag_app.py` (`build_agent`) |
| **Safety instructions** | The agent's system prompt forbids revealing one-time passwords or full card numbers, and tells it to admit when it does not know. | `rag_app.py` (`build_agent`) |
| **User interface** | A Streamlit chat page lets users ask questions in plain language. The model, index, database connection and agent are cached so they load once per session. | `rag_app.py` (`main`) |

### Why this design

- **RAG grounds policy answers in documents**, so the assistant quotes real fees and rules instead of guessing.
- **Text-to-SQL lets non-technical users query data** in natural language.
- **An agent with tool descriptions** avoids a hand-written if/else router. Adding a new source later only requires a new tool.
- **Caching with `st.cache_resource`** avoids re-embedding documents and reconnecting to the database on every message.

## Course topics used

| Course topic | Where it is used |
|---|---|
| Language embeddings and vector databases | `VectorStoreIndex` over `docs/` (policy search) |
| LlamaIndex with SQL database | `NLSQLTableQueryEngine` over `bank.db` (customer data) |
| Query pipelines / tools | `QueryEngineTool` wrappers for each engine |
| Working with agents and tools | `ReActAgent` that chooses the right tool |
| Build a code checker with Streamlit UI | `rag_app.py` chat interface |

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
python setup_db.py          # creates bank.db with sample data
streamlit run rag_app.py
```

## Example questions

- "What is the overdraft fee?" → answered from `docs/account_policies.md`
- "Can I get a personal loan of 50,000 if I earn 4,000 a month?" → policy rule (up to 10× monthly net salary)
- "What is the current balance of Amit's savings account?" → SQL query
- "Which customer has the highest current account balance?" → SQL query

## Project layout

```
banking_rag_project/
├── docs/account_policies.md   # sample policy documents to index
├── setup_db.py                # builds the sample SQLite database
├── rag_app.py                 # RAG + SQL agent with Streamlit UI
├── requirements.txt
└── README.md
```

## Limitations

- The assistant has not been run end to end in this project yet, so answer quality still needs testing.
- The sample data is fictitious.
- The no-disclosure rule is a prompt-level instruction, not a real security control. A production system needs PII masking, access control and audit logging.

## Extending the project

- Add more `.md` or `.pdf` policy files to `docs/` and rebuild the index.
- Add guardrails such as PII masking before answers are shown.
- Replace SQLite with a production database and restrict the SQL tool to read-only access.
