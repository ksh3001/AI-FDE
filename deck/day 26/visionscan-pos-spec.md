---

## title: VisionScan POS — Software Design Document subtitle: Camera-Based Retail Checkout System version: "1.0" status: Draft author: Engineering Team platform: Web — React \+ FastAPI \+ Supabase

# VisionScan POS — Software Design Document

**Camera-Based Retail Checkout System**

|  |  |
| :---- | :---- |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Engineering Team |
| **Target Platform** | Web (React \+ FastAPI \+ Supabase) |

---

## 1\. Purpose

### Objective

VisionScan POS is a production-ready retail checkout application that uses computer vision to detect products during a shopping session.

Instead of barcode scanning, products are identified using an AI vision model (mocked initially), mapped to an inventory catalogue, accumulated in a customer session, and converted into a bill during checkout.

The application shall provide inventory management, session tracking, stock deduction, and audit history.

---

## 2\. Scope

### 2.1 In Scope — Version 1

- Inventory Management  
- Camera Scan Session Management  
- Product Detection API  
- Product Matching Engine  
- Checkout Engine  
- Inventory Updates  
- REST APIs  
- React Administration UI

### 2.2 Out of Scope — Version 1

- Payment Gateway  
- Authentication  
- Multiple Stores  
- Loyalty Program  
- Live Camera Integration  
- Offline Mode  
- Receipt Printing

---

## 3\. High-Level Architecture

React Frontend

       │

       │ REST

       ▼

FastAPI Backend

       │

Business Services

       │

Supabase PostgreSQL

### 3.1 Architectural Principles

| ID | Principle |
| :---- | :---- |
| AP-1 | React never communicates directly with Supabase. |
| AP-2 | FastAPI owns all business logic. |
| AP-3 | Database access is encapsulated in repository/service layers. |
| AP-4 | Services remain independent of HTTP routing. |
| AP-5 | APIs are stateless. |

---

## 4\. Functional Requirements

### FR-001 — Start Scan Session

The system shall allow creation of a new shopping session.

**Input:** None

**Processing**

1. Generate Session UUID.  
2. Record check-in timestamp.  
3. Set `status = ACTIVE`.

**Output**

{

  "session\_id": "uuid",

  "status": "ACTIVE",

  "check\_in\_time": "timestamp"

}

---

### FR-002 — Scan Product

The system shall accept detected products from a vision model.

**Input**

{

  "detected\_name": "string",

  "confidence": 0.0

}

**Processing**

1. Validate confidence.  
2. Match product to inventory (see [Section 10](#10-product-matching-logic)).  
3. Deduplicate within session.  
4. Increment quantity if the product already exists in the session.  
5. Otherwise insert a new scan item.

---

### FR-003 — View Session

The system shall return all scanned products for a session.

**Response includes**

- Product Name  
- SKU  
- Quantity  
- Unit Price  
- Total  
- Confidence

---

### FR-004 — End Session

Marks the session as finished. **Does not modify inventory.**

---

### FR-005 — Checkout

Checkout performs transactional inventory updates.

**Processing**

1. Validate stock.  
2. Calculate totals.  
3. Deduct inventory.  
4. Record inventory movements.  
5. Complete session.

**On any inventory validation failure**

- No inventory changes.  
- No checkout.  
- Transaction rollback.

---

### FR-006 — Inventory Management

Supports:

- Create Item  
- Update Item  
- View Inventory

Deletion is **not** supported.

---

## 5\. Non-Functional Requirements

| Requirement | Value |
| :---- | :---- |
| API Response Time | \< 300 ms |
| Database | PostgreSQL |
| Architecture | Layered |
| REST Standard | JSON |
| Code Coverage | ≥ 80% |
| Deployment | Docker Compatible |
| Logging | Structured |
| Validation | Pydantic |
| Database Transactions | Required |

---

## 6\. User Flow

Start Session

      │

      ▼

Scan Product

      │

      ▼

Match Inventory

      │

      ▼

Already Exists?

   ┌─────┴─────┐

   │           │

  Yes          No

   │           │

Increase     Insert

Quantity      Item

   └─────┬─────┘

         │

         ▼

      Repeat

         │

         ▼

      Checkout

         │

         ▼

   Validate Stock

         │

         ▼

  Deduct Inventory

         │

         ▼

   Generate Bill

         │

         ▼

 Complete Session

---

## 7\. Data Model

### 7.1 `inventory_master`

| Field | Type |
| :---- | :---- |
| id | UUID |
| sku | TEXT |
| name | TEXT |
| category | TEXT |
| price | NUMERIC |
| stock | INTEGER |
| aliases | TEXT\[\] |
| created\_at | TIMESTAMP |

### 7.2 `scan_sessions`

| Field | Type |
| :---- | :---- |
| id | UUID |
| status | ACTIVE / COMPLETED |
| check\_in\_time | TIMESTAMP |
| check\_out\_time | TIMESTAMP |

### 7.3 `scan_items`

| Field | Type |
| :---- | :---- |
| id | UUID |
| session\_id | UUID |
| inventory\_id | UUID |
| detected\_name | TEXT |
| confidence | FLOAT |
| quantity | INTEGER |
| first\_seen | TIMESTAMP |

### 7.4 `inventory_movements`

| Field | Type |
| :---- | :---- |
| id | UUID |
| inventory\_id | UUID |
| change\_qty | INTEGER |
| reason | SALE / RESTOCK |
| created\_at | TIMESTAMP |

---

## 8\. API Specification

### 8.1 Session APIs

| Method | Endpoint | Description |
| :---- | :---- | :---- |
| POST | `/sessions/start` | Create session |
| GET | `/sessions/{id}` | Session details |
| POST | `/sessions/{id}/end` | End session |

### 8.2 Scan APIs

| Method | Endpoint | Description |
| :---- | :---- | :---- |
| POST | `/sessions/{id}/scan` | Submit a detected product |
| GET | `/sessions/{id}/items` | List scanned items |

### 8.3 Inventory APIs

| Method | Endpoint | Description |
| :---- | :---- | :---- |
| GET | `/inventory` | List inventory |
| POST | `/inventory` | Create item |
| PUT | `/inventory/{id}` | Update item |

### 8.4 Checkout API

| Method | Endpoint | Description |
| :---- | :---- | :---- |
| POST | `/sessions/{id}/checkout` | Perform checkout |

---

## 9\. Business Rules

| ID | Rule |
| :---- | :---- |
| BR-001 | A session may only be checked out once. |
| BR-002 | Duplicate scans increase quantity instead of creating duplicate rows. |
| BR-003 | Inventory matching priority: (1) Exact Name, (2) Alias Match, (3) Fuzzy Match. |
| BR-004 | Checkout fails if `stock < requested quantity`. |
| BR-005 | Inventory movement records must be created for every successful checkout. |
| BR-006 | Checkout must execute within a single database transaction. |

---

## 10\. Product Matching Logic

Detected Product

        │

        ▼

   Exact Name? ──── Yes ──► Match

        │

        No

        ▼

  Alias Match? ──── Yes ──► Match

        │

        No

        ▼

   Fuzzy Match

        │

        ▼

Confidence \> Threshold? ── Yes ──► Match

        │

        No

        ▼

 Unknown Product

---

## 11\. Frontend Modules

### 11.1 Scan Session

- Start Session  
- Scan Product  
- Live Item List  
- Running Total  
- Checkout

### 11.2 Inventory

- View Inventory  
- Search Inventory  
- Add Product  
- Edit Product

---

## 12\. Backend Modules

app/

│

├── main.py

├── config.py

├── database.py

│

├── routers/

│     sessions.py

│     inventory.py

│     checkout.py

│

├── services/

│     session\_service.py

│     inventory\_service.py

│     checkout\_service.py

│     matching\_service.py

│

├── repositories/

│     inventory\_repository.py

│     session\_repository.py

│

├── models/

├── schemas/

├── middleware/

└── utils/

---

## 13\. Frontend Structure

src/

│

├── api/

├── components/

├── hooks/

├── pages/

│     ScanSession.tsx

│     Inventory.tsx

│

├── services/

├── types/

├── utils/

└── App.tsx

---

## 14\. Error Handling

| Error | HTTP |
| :---- | :---- |
| Validation Error | 400 |
| Session Not Found | 404 |
| Product Not Found | 404 |
| Insufficient Stock | 409 |
| Duplicate SKU | 409 |
| Internal Error | 500 |

All errors shall return a standard JSON structure:

{

  "error": {

    "code": "INSUFFICIENT\_STOCK",

    "message": "Available stock is less than requested quantity.",

    "details": {}

  }

}

---

## 15\. Security Considerations

- Validate all request payloads with Pydantic.  
- Prevent SQL injection through parameterized queries / ORM.  
- Enable CORS only for approved frontend origins.  
- Sanitize all user inputs.  
- Log API requests with correlation IDs.  
- Avoid exposing internal exception traces in production responses.

---

## 16\. Deployment Architecture

React (Vite/Next.js)

        │

        ▼

FastAPI (Uvicorn/Gunicorn)

        │

        ▼

Supabase PostgreSQL

The application shall be containerized with Docker, support environment-specific configuration via `.env` files, include health-check endpoints, and be suitable for deployment behind a reverse proxy such as Nginx or Traefik.

---

## 17\. Acceptance Criteria

| ID | Criterion |
| :---- | :---- |
| AC-001 | A user can start a new scan session. |
| AC-002 | Products can be scanned and added to the session. |
| AC-003 | Duplicate scans increment quantity instead of creating duplicate entries. |
| AC-004 | Product matching follows the priority: exact → alias → fuzzy. |
| AC-005 | Inventory can be created, viewed, and updated through the UI. |
| AC-006 | Checkout calculates totals accurately and completes within a single transaction. |
| AC-007 | Checkout is rejected when stock is insufficient, with no partial inventory updates. |
| AC-008 | Successful checkout updates inventory, records inventory movements, and marks the session as completed. |
| AC-009 | All frontend interactions occur exclusively through FastAPI REST APIs. |
| AC-010 | The solution is production-ready with layered architecture, validation, error handling, logging, and clear deployment instructions. |

---

## Appendix A — Traceability Matrix

> **Note:** This appendix is not part of the original document. It is derived from Sections 4, 8, 9 and 17 to make the spec executable task-by-task and to expose any requirement that lacks a verifying criterion. Verify it before relying on it.

| Requirement | Endpoint(s) | Business Rules | Acceptance Criteria |
| :---- | :---- | :---- | :---- |
| FR-001 Start Scan Session | `POST /sessions/start` | — | AC-001 |
| FR-002 Scan Product | `POST /sessions/{id}/scan` | BR-002, BR-003 | AC-002, AC-003, AC-004 |
| FR-003 View Session | `GET /sessions/{id}`, `GET /sessions/{id}/items` | — | AC-002 |
| FR-004 End Session | `POST /sessions/{id}/end` | — | — |
| FR-005 Checkout | `POST /sessions/{id}/checkout` | BR-001, BR-004, BR-005, BR-006 | AC-006, AC-007, AC-008 |
| FR-006 Inventory Management | `GET /inventory`, `POST /inventory`, `PUT /inventory/{id}` | — | AC-005 |
| Cross-cutting (AP-1, AP-2) | all | — | AC-009, AC-010 |

### Gaps surfaced by this matrix

1. **FR-004 has no acceptance criterion.** Ending a session is a distinct state transition from checkout, but no AC verifies it. Consider adding: *"A session can be ended without modifying inventory, and an ended session cannot accept further scans."*  
2. **BR-003's fuzzy-match threshold is unspecified.** Section 10 refers to "Confidence \> Threshold" without giving a value. This needs a number before implementation, and the number belongs in Section 5\.  
3. **FR-002 does not define the confidence validation rule.** Step 1 says "validate confidence" but the minimum acceptable value and the rejection behaviour are undefined.  
4. **No AC covers the error envelope.** Section 14 defines a standard error structure; no acceptance criterion asserts that all endpoints conform to it.  
5. **Authentication is out of scope but security assumes trusted callers.** Section 15 lists CORS and input validation, neither of which restricts *who* may call the API. This is acceptable for v1 only if the deployment is not publicly reachable — that constraint should be stated explicitly.

