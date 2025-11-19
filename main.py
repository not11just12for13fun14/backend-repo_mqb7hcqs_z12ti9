import os
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents, update_document
from schemas import Task, Event, FocusBlock, Goal, HealthLog, MealPlan, FamilyItem, Contact, Note, Habit, AIRequest, User

app = FastAPI(title="Gestor de Alta Performance com IA")

# CORS: allow any https/http origin (needed for hosted frontend URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # use regex instead
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    name: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    user_id: str
    name: str


@app.get("/")
def read_root():
    return {"name": "Gestor de Alta Performance com IA", "status": "ok"}


# Auth (simplified for demo)
@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # For demo purposes, we use email as user_id token
    user_id = payload.email
    # Create user if not exists
    existing = db["user"].find_one({"email": payload.email}) if db is not None else None
    if existing is None and db is not None:
        create_document("user", {"name": (payload.name or payload.email.split("@")[0]), "email": payload.email})
    resolved_name = payload.name or (existing.get("name") if isinstance(existing, dict) else None) or payload.email.split("@")[0]
    return LoginResponse(token=user_id, user_id=user_id, name=resolved_name)


# Helper to ensure db
@app.get("/test")
def test_database():
    response = {"backend": "running", "db": (db is not None)}
    try:
        if db is not None:
            response["collections"] = db.list_collection_names()
            response["db_status"] = "connected"
        else:
            response["db_status"] = "not_configured"
    except Exception as e:
        response["db_status"] = f"error: {str(e)}"
    return response


# Generic create/list endpoints (per collection)
@app.post("/tasks")
def create_task(task: Task):
    _id = create_document("task", task)
    return {"id": _id}

@app.get("/tasks")
def list_tasks(user_id: str, scope: Optional[str] = None):
    filt = {"user_id": user_id}
    if scope:
        filt["scope"] = scope
    docs = get_documents("task", filt, limit=200)
    return docs

@app.post("/events")
def create_event(event: Event):
    _id = create_document("event", event)
    return {"id": _id}

@app.get("/events")
def list_events(user_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None):
    filt = {"user_id": user_id}
    if start and end:
        filt["start_time"] = {"$gte": start}
        filt["end_time"] = {"$lte": end}
    return get_documents("event", filt, limit=500)

class EventUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    title: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None

@app.patch("/events/{event_id}")
def update_event(event_id: str, payload: EventUpdate):
    modified = update_document("event", event_id, {k: v for k, v in payload.model_dump().items() if v is not None})
    if not modified:
        raise HTTPException(status_code=404, detail="Event not found or unchanged")
    return {"status": "ok", "id": event_id}

@app.post("/focus-blocks")
def create_focus_block(block: FocusBlock):
    _id = create_document("focusblock", block)
    return {"id": _id}

@app.get("/focus-blocks")
def list_focus_blocks(user_id: str):
    return get_documents("focusblock", {"user_id": user_id}, limit=200)

@app.post("/goals")
def create_goal(goal: Goal):
    _id = create_document("goal", goal)
    return {"id": _id}

@app.get("/goals")
def list_goals(user_id: str, horizon: Optional[str] = None):
    filt = {"user_id": user_id}
    if horizon:
        filt["horizon"] = horizon
    return get_documents("goal", filt, limit=200)

@app.post("/health")
def create_health(log: HealthLog):
    _id = create_document("healthlog", log)
    return {"id": _id}

@app.get("/health")
def list_health(user_id: str, type: Optional[str] = None):
    filt = {"user_id": user_id}
    if type:
        filt["type"] = type
    return get_documents("healthlog", filt, limit=500)

@app.post("/meals")
def create_meal_plan(mp: MealPlan):
    _id = create_document("mealplan", mp)
    return {"id": _id}

@app.get("/meals")
def list_meal_plans(user_id: str, day: Optional[date] = None):
    filt = {"user_id": user_id}
    if day:
        filt["date"] = day
    return get_documents("mealplan", filt, limit=30)

@app.post("/family")
def create_family_item(item: FamilyItem):
    _id = create_document("familyitem", item)
    return {"id": _id}

@app.get("/family")
def list_family_items(user_id: str, type: Optional[str] = None):
    filt = {"user_id": user_id}
    if type:
        filt["type"] = type
    return get_documents("familyitem", filt, limit=200)

@app.post("/contacts")
def create_contact(c: Contact):
    _id = create_document("contact", c)
    return {"id": _id}

@app.get("/contacts")
def list_contacts(user_id: str):
    return get_documents("contact", {"user_id": user_id}, limit=500)

@app.post("/notes")
def create_note(n: Note):
    _id = create_document("note", n)
    return {"id": _id}

@app.get("/notes")
def list_notes(user_id: str, type: Optional[str] = None):
    filt = {"user_id": user_id}
    if type:
        filt["type"] = type
    return get_documents("note", filt, limit=500)

@app.post("/habits")
def create_habit(h: Habit):
    _id = create_document("habit", h)
    return {"id": _id}

@app.get("/habits")
def list_habits(user_id: str):
    return get_documents("habit", {"user_id": user_id}, limit=200)


# AI helper endpoints (stubbed with simple logic for now)
class AICommand(BaseModel):
    user_id: str
    prompt: str

@app.post("/ai/center")
def ai_center(cmd: AICommand):
    # store request
    create_document("airequest", AIRequest(user_id=cmd.user_id, kind="center", parameters={"prompt": cmd.prompt}))

    p = cmd.prompt.lower()
    if "organiza a minha semana" in p:
        return {"plan": "Reorganizei a tua semana com blocos de foco nas manhãs e reuniões à tarde, priorizando tarefas urgentes e alinhadas com os teus objetivos."}
    if "plano alimentar" in p or "alimentar" in p:
        return {"meal_plan": "Plano alimentar gerado para foco mental e energia estável."}
    if "reformula" in p or "prioridades" in p:
        return {"priorities": ["1) Entregar proposta X", "2) Treino 45min", "3) Chamada com equipa"]}
    if "revisão mensal" in p or "revisao" in p:
        return {"review": "Revisão mensal: progresso de 68% nos objetivos trimestrais. Sugestões: reforçar consistência em hábitos chave."}

    return {"message": "Pedido recebido. Em breve, respostas mais inteligentes com base nos teus dados."}


# New focused AI endpoints
class AIPrioritize(BaseModel):
    user_id: str
    context: Optional[str] = None

class AIWeeklyPlan(BaseModel):
    user_id: str
    week_start: Optional[date] = None

class AIGoalsReview(BaseModel):
    user_id: str
    horizon: Optional[str] = None

@app.post("/ai/prioritize")
def ai_prioritize(payload: AIPrioritize):
    create_document("airequest", AIRequest(user_id=payload.user_id, kind="prioritize", parameters={"context": payload.context or ""}))
    tasks = get_documents("task", {"user_id": payload.user_id, "completed": False}, limit=100)
    # Very simple scoring by priority field then due_date
    prio_weight = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    def score(t):
        return (
            prio_weight.get((t.get("priority") or "medium").lower(), 2),
            0 if not t.get("due_date") else (9999999 - int(datetime.combine(t.get("due_date"), datetime.min.time()).timestamp()))
        )
    ordered = sorted(tasks, key=score, reverse=True)
    top = [{"_id": str(t.get("_id")), "title": t.get("title"), "priority": t.get("priority"), "due_date": t.get("due_date")} for t in ordered[:7]]
    return {"suggested_order": top}

@app.post("/ai/weekly-plan")
def ai_weekly_plan(payload: AIWeeklyPlan):
    start = payload.week_start or date.today()
    events = get_documents("event", {"user_id": payload.user_id}, limit=200)
    blocks = [
        {
            "day": (start + timedelta(days=i)).isoformat(),
            "focus": ["Bloco de foco 09:00-10:30", "Revisão 16:00-16:30"],
            "tips": "Reserva manhãs para deep work. Coloca reuniões depois das 14h."
        }
        for i in range(7)
    ]
    create_document("airequest", AIRequest(user_id=payload.user_id, kind="weekly_plan", parameters={"week_start": start.isoformat()}))
    return {"week_start": start.isoformat(), "plan": blocks, "events_considered": len(events)}

@app.post("/ai/goals-review")
def ai_goals_review(payload: AIGoalsReview):
    goals = get_documents("goal", {"user_id": payload.user_id}, limit=200)
    if not goals:
        return {"summary": "Sem objetivos registados ainda.", "actions": []}
    avg = round(sum(int(g.get("progress") or 0) for g in goals) / max(1, len(goals)))
    actions = []
    for g in goals[:3]:
        actions.append({"goal": g.get("title"), "next_actions": ["Definir ação clara para esta semana", "Agendar 2 blocos de foco", "Criar métrica de progresso"]})
    create_document("airequest", AIRequest(user_id=payload.user_id, kind="goals_review", parameters={"horizon": payload.horizon or "all"}))
    return {"average_progress": avg, "recommendations": actions}


# Dashboard aggregates
@app.get("/dashboard")
def dashboard(user_id: str):
    today = date.today()
    # Fetch summaries
    tasks = get_documents("task", {"user_id": user_id, "completed": False}, limit=20)
    events = get_documents("event", {"user_id": user_id}, limit=50)
    habits = get_documents("habit", {"user_id": user_id}, limit=20)
    health_today = get_documents("healthlog", {"user_id": user_id, "type": "energy"}, limit=5)
    alerts = []
    # birthdays from contacts
    contacts = get_documents("contact", {"user_id": user_id}, limit=500)
    for c in contacts:
        b = c.get("birthday")
        if b and isinstance(b, date):
            if b.month == today.month and b.day == today.day:
                alerts.append({"type": "birthday", "name": c.get("name")})
    # deadlines from tasks
    for t in tasks:
        if t.get("due_date") == today:
            alerts.append({"type": "deadline", "title": t.get("title")})

    recs = [
        "Foca nas 3 prioridades: proposta X, revisão OKRs, treino leve",
        "Agenda um bloco de foco de 90min às 9:00",
        "Hidrata-te: 2 copos de água agora"
    ]

    return {
        "tasks": tasks,
        "events": events,
        "habits": habits,
        "energy": health_today[-1]["value"] if health_today else 70,
        "alerts": alerts[:5],
        "recommendations": recs
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
