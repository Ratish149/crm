# Nepdora Sales CRM Backend — LLM Project Context

This document summarizes the Django backend project so another LLM can understand the architecture, business domain, data model, and integration points for building an Ollama-powered AI chatbot.

## 1. Project Overview

This is a Django 6 + Django REST Framework backend for a sales CRM product called Nepdora. The system manages:

- leads and sales pipeline
- discovery questionnaires and AI-generated analysis
- follow-ups and activity timelines
- invoices
- knowledge base articles
- email outreach
- a chatbot area for conversational AI

The backend exposes a REST API under the `/api/` prefix and uses JWT authentication.

## 2. Core Tech Stack

- Python 3.x
- Django 6.0.4
- Django REST Framework 3.17.1
- SimpleJWT for authentication
- django-filter for filtering
- django-cors-headers for frontend access
- django-unfold for admin UI customization
- SQLite for local development (see `db.sqlite3`)
- Optional AI integrations:
  - Google GenAI for discovery-stage analysis
  - Ollama-ready architecture for future chatbot integration

## 3. Project Structure

Key top-level files:

- `manage.py` — Django management entry point
- `requirements.txt` — Python dependencies
- `docker-compose.yaml` and `Dockerfile` — containerization support
- `start.sh` — startup script
- `db.sqlite3` — local SQLite database

Main Django apps:

- `accounts/` — authentication and user management
- `lead/` — core CRM lead management
- `discovery/` — sales discovery questions, answers, and AI analysis
- `knowledgebase/` — support knowledge articles and categories
- `invoice/` — invoice management and statistics
- `mail/` — outbound email flows
- `chatbot/` — chat/conversation scaffolding
- `crm/` — project configuration and shared utilities

## 4. App-by-App Summary

### 4.1 `accounts`

Purpose:
- user registration
- login/token issuance
- basic user profile retrieval and update

Key files:
- `accounts/serializers.py`
- `accounts/views.py`
- `accounts/urls.py`

Key behavior:
- Registers users with `create_user`
- Issues JWT access/refresh tokens
- Adds user metadata into JWT payload such as `id`, `username`, `first_name`, `last_name`, `email`, and `is_superuser`

Important endpoints:
- `POST /api/register/`
- `POST /api/login/`
- `POST /api/token/refresh/`
- `GET/PUT/DELETE /api/users/<id>/`

### 4.2 `lead`

Purpose:
- core CRM domain for leads
- lead lifecycle management
- notes, attachments, follow-ups, activity history
- lead import/export-style workflows

Key files:
- `lead/models.py`
- `lead/serializers.py`
- `lead/views.py`
- `lead/urls.py`
- `lead/tasks.py`
- `lead/utils.py`

Core domain model:
- `Lead` — main record for a sales prospect/customer
- `Tag` — labels for leads
- `Note` — freeform notes attached to a lead
- `LeadDocument` — uploaded files for a lead
- `ActivityTimeline` — audit trail of events
- `Followup` — scheduled follow-up task
- `FilterPreset` — saved filter configurations

Important lead fields:
- `full_name` (unique)
- `email`
- `phone_number` (unique)
- `source`
- `estimate_value`
- `status`
- `assigned_to`
- `created_by`
- `tags`
- `rating`

Lead statuses:
- `new`
- `not_interested`
- `discovery`
- `quoted`
- `negotiation`
- `closed`

Important API endpoints:
- `GET/POST /api/lead/`
- `GET/PUT/DELETE /api/lead/<id>/`
- `POST /api/notes/`
- `GET /api/lead-pipeline/`
- `GET /api/lead/<lead_id>/activities/`
- `POST /api/documents/`
- `GET /api/lead/<lead_id>/documents/`
- `GET/POST /api/lead/<lead_id>/followups/`
- `GET/POST /api/followups/`
- `GET /api/followups/incomplete/`
- `GET /api/check-followups/`
- `GET /api/tags/`
- `GET /api/lead/import-template/`
- `POST /api/lead/bulk-import/`
- `GET/POST /api/filter-presets/`

Business behavior:
- creating a lead also creates an activity log entry
- adding a note also logs activity
- uploading a document also logs activity
- follow-ups can automatically trigger email notifications

### 4.3 `discovery`

Purpose:
- configure a step-by-step sales discovery questionnaire
- collect lead answers per stage
- generate AI-based recommendations from responses

Key files:
- `discovery/models.py`
- `discovery/serializers.py`
- `discovery/views.py`
- `discovery/urls.py`

Core domain model:
- `SalesStage` — a discovery phase (e.g. discovery, qualification, etc.)
- `Category` — topic group for questions/answers
- `Question` — one question in a stage
- `Answer` — possible option/answer for a question
- `LeadResponse` — a lead’s answer to a question
- `LeadStageAnalysis` — AI-generated analysis for a lead/stage pair

Important relationships:
- `Question` belongs to a `SalesStage`
- `Answer` belongs to a `Question`
- `LeadResponse` belongs to a `Lead` and a `Question`
- `LeadStageAnalysis` links a `Lead` and a `SalesStage`

Important endpoints:
- `GET/POST /api/discovery/stages/`
- `GET/POST /api/discovery/categories/`
- `GET/POST /api/discovery/questions/`
- `GET/POST /api/discovery/answers/`
- `GET /api/discovery/config/` — returns full stage/question/answer structure
- `GET/POST /api/discovery/responses/`
- `POST /api/discovery/analyze/` — sends lead responses to an AI model
- `GET /api/discovery/analysis/` — retrieves prior analysis

AI behavior:
- The project already uses Google GenAI in `discovery/views.py`
- The AI prompt asks for a JSON response with:
  - `client_problems`
  - `recommended_approach`
- The result is saved into `LeadStageAnalysis`

### 4.4 `knowledgebase`

Purpose:
- store knowledge articles and categories for internal use or chatbot grounding

Key files:
- `knowledgebase/models.py`
- `knowledgebase/views.py`
- `knowledgebase/urls.py`

Core model:
- `KnowledgeCategory` — article category
- `KnowledgeBase` — article content with title and content

Important endpoints:
- `GET/POST /api/categories/`
- `GET/POST /api/articles/`

This app is especially relevant for an LLM chatbot because it is a structured knowledge source.

### 4.5 `invoice`

Purpose:
- invoice creation and management
- invoice item lines
- invoice statistics

Key files:
- `invoice/models.py`
- `invoice/views.py`
- `invoice/urls.py`

Core model:
- `Invoice` — invoice header with billing parties, dates, amounts, files, and status
- `InvoiceItem` — line items for an invoice

Important endpoints:
- `GET/POST /api/invoices/`
- `GET/PUT/DELETE /api/invoices/<id>/`
- `GET /api/invoices/statistics/`

### 4.6 `mail`

Purpose:
- send outbound emails using Resend
- render email templates for offers and recommendations

Key files:
- `mail/views.py`
- `mail/urls.py`

Important endpoints:
- `POST /api/lead/send-email/`
- `POST /api/lead/send-proposal/`
- `POST /api/lead/send-recommendation/`

Email behavior:
- uses templates under `assets/mail_template/` and `mail/templates/mail/`
- can attach a PDF proposal document
- logs email activity to the lead timeline when possible

### 4.7 `chatbot`

Purpose:
- intended space for conversational AI
- currently only scaffolding exists

Key files:
- `chatbot/models.py`
- `chatbot/urls.py`
- `chatbot/views.py`

Current models:
- `Conversation` — one chat thread per user
- `ChatMessage` — individual message records in a conversation

Current endpoint:
- `GET/POST /api/chat/` (configured in URL config)

Important note:
- The current `chatbot/views.py` does not define `chat_view`, so this endpoint is not yet fully implemented. This is a prime integration point for an Ollama-based chatbot.

## 5. Shared Project Configuration

### 5.1 `crm/settings.py`

Notable settings:
- installed apps include all CRM modules
- CORS is enabled for local frontend origins
- JWT authentication is the default authentication class
- media files are stored under `media/`
- static files under `static/`
- timezone is set to `Asia/Kathmandu`

Important constants:
- `SECRET_KEY` is hard-coded for development
- `DEBUG = True`
- `ALLOWED_HOSTS = ["*"]`
- `REST_FRAMEWORK` uses JWT auth as default
- `SIMPLE_JWT` uses access tokens for 1 day and refresh tokens for 3 days

### 5.2 `crm/urls.py`

All app routes are combined under the base `/api/` prefix.

## 6. Database Relationships Worth Knowing

The most important relationships are:

- `Lead` -> `Note`, `LeadDocument`, `ActivityTimeline`, `Followup`, `LeadResponse`
- `SalesStage` -> `Question`
- `Question` -> `Answer`
- `LeadResponse` -> `Question` and `Answer`
- `LeadStageAnalysis` -> `Lead` and `SalesStage`
- `KnowledgeBase` -> `KnowledgeCategory`
- `Invoice` -> `InvoiceItem`
- `Conversation` -> `ChatMessage`

These relationships matter for chatbot retrieval and summarization.

## 7. Business Workflow Summary

### Lead workflow
1. A lead is created.
2. Notes, documents, and follow-up tasks may be added.
3. Discovery questions are answered as the stage progresses.
4. AI analysis can be generated from the collected responses.
5. Emails may be sent to the lead or prospect.
6. The lead moves through sales stages.

### Discovery workflow
1. A sales stage and its questions are configured.
2. A lead answers questions.
3. Responses are stored in `LeadResponse`.
4. An AI analysis is generated and saved into `LeadStageAnalysis`.

### Knowledge workflow
1. Knowledge categories are created.
2. Articles are stored in `KnowledgeBase`.
3. A chatbot can retrieve these articles as grounding context.

## 8. What an Ollama Chatbot Should Know

If you want to build an Ollama-powered assistant for this project, the most valuable data sources are:

- `Lead` data: name, contact info, status, assignment, rating, tags
- `Followup` data: upcoming tasks and notes
- `ActivityTimeline`: recent lead actions and history
- `Discovery` data: stage-based sales questionnaire answers and AI analysis
- `KnowledgeBase`: internal knowledge articles for helpful answers
- `Invoice` data: invoice records and payment status

Good chatbot use cases include:
- summarize a lead's profile and recent activity
- answer questions about next follow-up actions
- explain past discovery insights for a lead
- search knowledge base articles
- draft outreach messaging or recommendations
- suggest the next best sales action based on CRM state

## 9. Recommended Integration Points for Chatbot Development

The current chatbot app is the ideal place to implement the feature:

- add a real `chat_view` endpoint
- store user conversations in `Conversation` and `ChatMessage`
- use `Ollama` as the LLM backend
- retrieve CRM context dynamically from leads, discovery responses, knowledge base, and invoices
- optionally use RAG (retrieval-augmented generation) over `KnowledgeBase`

Suggested context sources for the chatbot:
- current lead context when a lead ID is provided
- recent activities for that lead
- discovery analysis for the latest stage
- knowledge base article search results
- invoice summary if the user asks about billing

## 10. Notable Gaps / Implementation Notes

- `chatbot/views.py` is currently incomplete and does not implement `chat_view`.
- The `/api/chat/` endpoint is wired but not functional yet.
- The project already has AI-related infrastructure for discovery analysis, which can be adapted for chatbot use.
- The app has strong CRM domain data but no explicit chatbot orchestration layer yet.

## 11. Suggested Prompting Context for Another LLM

When another LLM tries to generate chatbot code for this project, it should be told:

- this is a Django REST backend for a sales CRM
- the main business objects are leads, discovery responses, follow-ups, invoices, knowledge base articles, and user accounts
- the chatbot should act as an assistant for sales operations and internal support
- the backend already has JWT auth and structured REST endpoints
- the chatbot should be able to work with both conversational state and business data

## 12. Quick Reference

Most important modules:
- `crm/settings.py` — project configuration
- `crm/urls.py` — API routing
- `lead/models.py` — main CRM domain
- `discovery/models.py` — sales discovery and AI analysis
- `knowledgebase/models.py` — support content
- `chatbot/models.py` — conversation storage

Most important API roots:
- `/api/register/`
- `/api/login/`
- `/api/lead/`
- `/api/discovery/config/`
- `/api/discovery/responses/`
- `/api/invoices/`
- `/api/articles/`
- `/api/chat/`
