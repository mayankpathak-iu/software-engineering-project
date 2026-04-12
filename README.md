# StudyFlow

**Academic workload planning for university students**

StudyFlow is a browser-based web application that helps students manage **subjects**, **assignments**, **class schedules**, and **study sessions** in one place. Instead of only showing deadlines, it combines timetable data with assignment urgency and estimated effort to suggest **when** study should happen.

## Demo Videos

- [Demo Video 1 – Full solution walkthrough](https://youtu.be/FVmYdKJPiBM)
- [Demo Video 2 – Additional walkthrough / interaction demo](https://youtu.be/7OWrmMLAPfM)

---

## Why StudyFlow?

University portals usually show course materials and timetables, but they rarely help students answer practical questions like:

- What should I start first?
- Which day is lighter for focused study?
- How do I fit assignments around lectures?
- How much work is still pending before the next deadline?

StudyFlow addresses that gap by combining:

- subject and assignment management
- `.ics` calendar import
- subject extraction from calendar events
- rule-based study recommendations
- planner-generated study sessions
- an interactive weekly calendar

---

## Quick Product View

### Dashboard

The dashboard gives a quick snapshot of overdue, due-soon, and completed assignments so the student can understand workload immediately after login.

![Test Dashboard](docs/Test/Test%20dashboard.png)

---

## Core Features

### 1. User Authentication

Students can sign up, log in, and use a personal workspace with isolated data. The signup flow also includes validation, such as duplicate email detection.

![Login Test](docs/Test/Login%20Test.jpg)

---

### 2. Subject Management

Subjects can be created manually or imported from timetable data. Each subject has a name, code, and color.

![Subjects Test](docs/Test/Subjects.png)

---

### 3. Assignment Management

Assignments are linked to subjects and include:
- title
- due date
- priority
- status
- estimated study hours
- description

If no subject exists yet, the application clearly guides the user to create one first.

![Assignments Test](docs/Test/Assignments.jpeg)

---

### 4. `.ics` Timetable Import

Students can upload a timetable exported from their university or calendar application. StudyFlow parses the `.ics` file and stores lecture events as fixed class events.

![Calendar Import Test](docs/Test/Calendar%20Import.jpeg)

---

### 5. Import Subjects from Calendar

After uploading a timetable, StudyFlow extracts candidate subjects from calendar titles. The user can review and edit the detected subject name and code before importing.

![Import from Calendar Test](docs/Test/Import%20from%20calendar.jpeg)

---

### 6. Study Recommendations

The recommendation engine looks at pending assignments, urgency, estimated hours, and class intensity, then suggests the next best steps.

It can highlight:
- the most urgent assignment
- total pending study hours
- lighter class days for focused work
- potential overload before deadlines

![Test Recommendation](docs/Test/Test%20Recommendation.png)

---

### 7. Planner + Study Sessions

StudyFlow generates suggested study sessions based on workload and time availability before deadlines.

![Planner Test](docs/Test/Planner.jpeg)

---

### 8. Weekly Calendar View

The weekly calendar combines:
- **blue blocks** → fixed class events
- **green blocks** → generated study sessions

Study sessions can be dragged or resized directly in the calendar.

![Calendar View Test](docs/Test/Calendar%20view.png)

---

## How It Works

```text
Upload .ics timetable
→ Parse class events
→ Import or create subjects
→ Create assignments
→ Analyze workload + due dates + class intensity
→ Generate recommendations
→ Generate study sessions
→ Show everything in a weekly calendar
→ Let the user adjust study sessions interactively
```

---

## Architecture Overview

StudyFlow follows a layered architecture.

### Building Block View

📄 [View diagram: studyflow_figure1_building_block.pdf](docs/studyflow_figure1_building_block.pdf)

---

### Technical Architecture

📄 [View diagram: studyflow_tech_architecture.pdf](docs/studyflow_tech_architecture.pdf)

---

### Data Model

📄 [View diagram: studyflow_figure2_data_model.pdf](docs/studyflow_figure2_data_model.pdf)

---

### Planning Process Flow

📄 [View diagram: studyflow_figure3_process_flow.pdf](docs/studyflow_figure3_process_flow.pdf)

---

## Layer Breakdown

### Presentation Layer

Server-rendered Jinja2 templates provide the user-facing views:
- Dashboard
- Subjects
- Assignments
- Calendar
- Import Subjects
- Recommendations
- Planner
- Weekly Calendar View

### Application Logic Layer

FastAPI route handlers and business logic modules handle:
- authentication
- subject management
- assignment management
- calendar import
- recommendation generation
- planner logic
- study session updates

### Persistence Layer

SQLAlchemy models persist the main entities:
- `User`
- `Subject`
- `Assignment`
- `ClassEvent`
- `StudySession`

### Supporting Libraries

- `icalendar` → parses `.ics` timetable files
- `FullCalendar` → renders the interactive weekly calendar
- `GitHub` → version and release control

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Templates / UI | Jinja2 |
| ORM | SQLAlchemy |
| Database | SQLite |
| Calendar Parsing | icalendar |
| Calendar UI | FullCalendar |
| Version Control | GitHub |
| Optional Containerization | Docker |

---

## Key Design Decisions

### Rule-Based Planning

Recommendations and planner output are intentionally rule-based instead of using a more opaque optimization model. That keeps the logic explainable and appropriate for a student planning tool.

### User-Reviewed Subject Import

Calendar titles can vary a lot, so subject extraction is not fully automatic. The user reviews candidate subjects before they are created.

### Fixed Classes, Flexible Study Sessions

Lectures remain fixed in the calendar, while study sessions are editable. This matches real academic behavior: classes are scheduled commitments, study blocks are adjustable.

### Server-Rendered UI

A server-rendered approach keeps the system simpler and easier to reason about while still supporting a usable browser experience.

---

## Main Routes

| Route | Purpose |
|---|---|
| `/auth/signup` | User registration |
| `/auth/login` | User login |
| `/auth/logout` | User logout |
| `/dashboard` | Assignment summaries |
| `/subjects` | Subject list + CRUD |
| `/assignments` | Assignment list, filters, CRUD |
| `/calendar` | `.ics` upload |
| `/calendar/import-subjects` | Review and import timetable-derived subjects |
| `/recommendations` | Study recommendations |
| `/planner` | Generated study sessions |
| `/calendar-view` | Weekly calendar view |
| `/study-sessions/{id}` | Update study session time |

---

## Local Setup

### Option 1: Run with Python

```bash
git clone https://github.com/mayankpathak-iu/software-engineering-project
cd software-engineering-project

python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```
http://localhost:8000
```

## Suggested User Flow

1. Sign up or log in
2. Upload an `.ics` timetable
3. Import subjects from parsed calendar entries
4. Create assignments
5. Review recommendations
6. Generate study sessions
7. Open the weekly calendar
8. Adjust study sessions as needed

---

## Current Limitations

- SQLite is fine for development and demos, but PostgreSQL would be better for production.
- Recommendation logic is rule-based and not personalized over time.
- No mobile-first layout yet.
- External calendar sync is not implemented yet.
- Planner logic can still be expanded for more advanced balancing and conflict detection.

---

## Future Enhancements

- PostgreSQL migration
- direct Google Calendar / Outlook sync
- mobile-responsive layout
- smarter recommendation model
- schedule conflict detection
- export to PDF / image
- automated tests for planner and recommendation logic

## Project Summary

StudyFlow was built as a software engineering course project and evolved across three phases:
- **Phase 1:** problem framing, scope, requirements, and initial design
- **Phase 2:** implementation, technological approach, and architecture refinement
- **Phase 3:** final report, testing evidence, screenshots, and project consolidation

The final system demonstrates that a focused academic planning tool can provide more practical value than a simple task list by combining **deadlines**, **estimated effort**, and **timetable awareness** in one workflow.
