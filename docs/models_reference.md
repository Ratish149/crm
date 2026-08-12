# CRM Models Reference

This document consolidates the Django models defined across the backend apps so another LLM can understand the data model quickly.

## Overview

The backend contains the following custom model groups:

- Lead management: Lead, Tag, Note, LeadDocument, ActivityTimeline, Followup, FilterPreset
- Discovery workflow: SalesStage, Category, Question, Answer, LeadResponse, LeadStageAnalysis
- Knowledge base: KnowledgeCategory, KnowledgeBase
- Invoicing: Invoice, InvoiceItem
- Chatbot: Conversation, ChatMessage
- Accounts and mail: no custom models defined yet

## Apps and Models

### Accounts

File: [accounts/models.py](../accounts/models.py)

Status: no custom models are currently defined in this file.

### Chatbot

File: [chatbot/models.py](../chatbot/models.py)

#### Conversation
- Purpose: represents a chat conversation/thread for a user.
- Fields:
  - user: ForeignKey to the Django user model
  - created_at: auto-added timestamp

#### ChatMessage
- Purpose: stores an individual message inside a conversation.
- Fields:
  - conversation: ForeignKey to Conversation
  - content: text body of the message
  - created_at: auto-added timestamp

### Discovery

File: [discovery/models.py](../discovery/models.py)

#### SalesStage
- Purpose: represents a discovery stage in the sales qualification flow.
- Fields:
  - name: CharField
  - order: PositiveIntegerField, default 0
  - description: TextField
- Relationships:
  - has many Question objects

#### Category
- Purpose: groups questions and answers by topic.
- Fields:
  - name: CharField
  - description: TextField, optional
- Relationships:
  - has many Question and Answer objects

#### Question
- Purpose: a question asked during a sales stage.
- Fields:
  - stage: ForeignKey to SalesStage
  - category: ForeignKey to Category, optional
  - text: TextField
  - description: TextField, optional
  - question_type: CharField with choices: checklist, single, text
  - order: PositiveIntegerField, default 0
- Relationships:
  - has many Answer objects
  - used by LeadResponse

#### Answer
- Purpose: a possible answer/option for a question.
- Fields:
  - question: ForeignKey to Question
  - category: ForeignKey to Category, optional
  - text: TextField
  - description: TextField, optional
- Relationships:
  - can be selected in LeadResponse

#### LeadResponse
- Purpose: stores a lead's answer to a specific question.
- Fields:
  - lead: ForeignKey to Lead
  - question: ForeignKey to Question
  - selected_answers: ManyToManyField to Answer
  - text_value: TextField, optional, used for free-text questions
  - created_at: timestamp

#### LeadStageAnalysis
- Purpose: stores AI-generated analysis for a lead and stage.
- Fields:
  - lead: ForeignKey to Lead
  - stage: ForeignKey to SalesStage
  - client_problems: TextField
  - recommended_approach: TextField
  - raw_ai_response: JSONField, optional
  - created_at: timestamp
- Constraints:
  - unique per lead + stage combination

### Invoice

File: [invoice/models.py](../invoice/models.py)

#### Invoice
- Purpose: invoice header record.
- Fields:
  - status: CharField with choices Draft, Pending, Paid, Received, Overdue
  - bill_from_name: CharField
  - bill_from_address: TextField, optional
  - bill_from_email: EmailField, optional
  - bill_from_phone: CharField, optional
  - bill_from_vat: CharField, optional
  - bill_to_name: CharField
  - bill_to_address: TextField, optional
  - bill_to_email: EmailField, optional
  - bill_to_phone: CharField, optional
  - bill_to_vat: CharField, optional
  - invoice_number: CharField, unique, optional
  - invoice_date: DateField
  - due_date: DateField, optional
  - currency: CharField, optional
  - logo: FileField, optional
  - discount: DecimalField
  - discount_type: CharField with choices Percentage/Amount
  - vat: DecimalField
  - total_amount: DecimalField
  - additional_notes: TextField, optional
  - payment_terms: TextField, optional
  - bank_name: CharField, optional
  - account_name: CharField, optional
  - account_number: CharField, optional
  - signature: FileField, optional
  - created_by: ForeignKey to Django user
  - created_at / updated_at: timestamps
- Relationships:
  - has many InvoiceItem objects

#### InvoiceItem
- Purpose: line item inside an invoice.
- Fields:
  - invoice: ForeignKey to Invoice
  - name: CharField
  - description: TextField, optional
  - quantity: IntegerField
  - rate: DecimalField
  - amount: DecimalField, optional

### Knowledgebase

File: [knowledgebase/models.py](../knowledgebase/models.py)

#### KnowledgeCategory
- Purpose: groups knowledge base articles into categories.
- Fields:
  - name: CharField

#### KnowledgeBase
- Purpose: an internal knowledge article.
- Fields:
  - category: ForeignKey to KnowledgeCategory, optional
  - title: CharField
  - content: TextField
  - created_at / updated_at: timestamps

### Lead

File: [lead/models.py](../lead/models.py)

#### Tag
- Purpose: labels that can be attached to leads.
- Fields:
  - name: CharField
  - created_at / updated_at: timestamps

#### Lead
- Purpose: the core sales CRM record.
- Fields:
  - full_name: CharField, unique
  - email: EmailField, optional
  - phone_number: CharField, unique
  - source: CharField, optional
  - estimate_value: CharField, optional
  - status: CharField with choices new, not_interested, discovery, quoted, negotiation, closed
  - assigned_to: ForeignKey to Django user, optional
  - created_by: ForeignKey to Django user, optional
  - tags: ManyToManyField to Tag
  - rating: PositiveIntegerField between 0 and 10
  - created_at / updated_at: timestamps
- Relationships:
  - has many Note, LeadDocument, ActivityTimeline, Followup, LeadResponse

#### LeadDocument
- Purpose: stores uploaded files related to a lead.
- Fields:
  - lead: ForeignKey to Lead
  - file: FileField
  - uploaded_by: ForeignKey to Django user, optional
  - uploaded_at / updated_at: timestamps

#### Note
- Purpose: freeform notes attached to a lead.
- Fields:
  - lead: ForeignKey to Lead
  - content: TextField
  - created_by: ForeignKey to Django user, optional
  - created_at / updated_at: timestamps

#### ActivityTimeline
- Purpose: records actions/events for a lead.
- Fields:
  - lead: ForeignKey to Lead
  - user: ForeignKey to Django user, optional
  - activity_type: CharField with choices lead_created, note_added, discovery_updated, document_uploaded, email_sent
  - description: JSONField
  - created_at: timestamp

#### Followup
- Purpose: tracks scheduled follow-up tasks for a lead.
- Fields:
  - lead: ForeignKey to Lead
  - followup_date: DateField, optional
  - followup_time: TimeField, optional
  - notes: TextField, optional
  - status: CharField with choices pending, completed, cancelled
  - created_by: ForeignKey to Django user, optional
  - created_at / updated_at: timestamps

#### FilterPreset
- Purpose: stores saved filter configuration for UI or reporting.
- Fields:
  - name: CharField
  - filters: JSONField
  - created_at / updated_at: timestamps

### Mail

File: [mail/models.py](../mail/models.py)

Status: no custom models are currently defined in this file.

## Relationship Summary

The most important cross-model relationships are:

- Lead -> Note / LeadDocument / ActivityTimeline / Followup / LeadResponse
- SalesStage -> Question
- Question -> Answer
- LeadResponse -> Lead + Question + Answer
- LeadStageAnalysis -> Lead + SalesStage
- KnowledgeBase -> KnowledgeCategory
- Invoice -> InvoiceItem
- Conversation -> ChatMessage

## Notes for LLM Use

If another LLM is generating CRM features or an AI assistant, these are the most relevant business entities:

1. Lead
2. Followup
3. ActivityTimeline
4. LeadResponse
5. LeadStageAnalysis
6. KnowledgeBase
7. Invoice
8. Conversation / ChatMessage
