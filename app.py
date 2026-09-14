from __future__ import annotations

import csv
import hashlib
import io
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import (
    create_engine, String, Integer, DateTime, ForeignKey, LargeBinary,
    select, func, case, cast, delete, update
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB = BASE_DIR / "data" / "eleccion.db"
LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)

raw_db_url = os.environ.get("DATABASE_URL", "").strip()
if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        raw_db_url = "postgresql+psycopg://" + raw_db_url[len("postgres://"):]
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = "postgresql+psycopg://" + raw_db_url[len("postgresql://"):]
    DATABASE_URL = raw_db_url
else:
    DATABASE_URL = f"sqlite:///{LOCAL_DB.as_posix()}"

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(2000), nullable=False)


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    voted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    list_number: Mapped[str] = mapped_column(String(30), nullable=False)
    list_name: Mapped[str] = mapped_column(String(200), nullable=False)
    candidate_name: Mapped[str] = mapped_column(String(300), nullable=False)
    symbol_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    symbol_mime: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    @property
    def symbol_path(self):
        return f"candidate-symbol/{self.id}" if self.symbol_data else None


class Vote(Base):
    __tablename__ = "votes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), nullable=True, index=True)
    cast_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


app = FastAPI(title="Elecciones Escolares FBC")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("ELECCIONES_SECRET", "fbc-local-secret-cambiar-en-produccion"),
    same_site="lax",
    https_only=os.environ.get("RENDER", "").lower() == "true",
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def now_dt():
    return datetime.now()


def password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    Base.metadata.create_all(engine)
    defaults = {
        "school_name": "I.E. Francisco Bolognesi Cervantes",
        "election_title": "Elecciones Municipales Escolares 2026",
        "election_open": "0",
        "show_results_live": "0",
        "admin_password_hash": password_hash("FBC2026!"),
        "first_run": "1",
    }
    with SessionLocal.begin() as db:
        existing = set(db.scalars(select(Setting.key)).all())
        for k, v in defaults.items():
            if k not in existing:
                db.add(Setting(key=k, value=v))


def setting(key: str, default: str = "") -> str:
    with SessionLocal() as db:
        row = db.get(Setting, key)
        return row.value if row else default


def set_setting(key: str, value: str):
    with SessionLocal.begin() as db:
        row = db.get(Setting, key)
        if row:
            row.value = value
        else:
            db.add(Setting(key=key, value=value))


def base_context(request: Request, **extra):
    ctx = {
        "request": request,
        "school_name": setting("school_name"),
        "election_title": setting("election_title"),
        "election_open": setting("election_open") == "1",
        "is_admin": bool(request.session.get("admin")),
    }
    ctx.update(extra)
    return ctx


def admin_required(request: Request):
    return bool(request.session.get("admin"))


init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with SessionLocal() as db:
        grades = db.scalars(select(Student.grade).distinct().order_by(cast(Student.grade, Integer), Student.grade)).all()
        total = db.scalar(select(func.count(Student.id))) or 0
        candidates = db.scalar(select(func.count(Candidate.id)).where(Candidate.active == 1)) or 0
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=base_context(request, grades=grades, total_students=total, candidate_count=candidates),
    )


@app.get("/api/sections")
def api_sections(grade: str):
    with SessionLocal() as db:
        rows = db.scalars(select(Student.section).where(Student.grade == grade).distinct().order_by(Student.section)).all()
    return JSONResponse(list(rows))


@app.get("/api/students")
def api_students(grade: str, section: str):
    with SessionLocal() as db:
        rows = db.scalars(
            select(Student).where(Student.grade == grade, Student.section == section).order_by(Student.full_name)
        ).all()
    return JSONResponse([{"id": r.id, "name": r.full_name, "voted": bool(r.voted_at)} for r in rows])


@app.post("/identify")
def identify(request: Request, student_id: int = Form(...)):
    if setting("election_open") != "1":
        return RedirectResponse("/?msg=La+votación+está+cerrada", status_code=303)
    with SessionLocal() as db:
        row = db.get(Student, student_id)
        if not row:
            return RedirectResponse("/?msg=Estudiante+no+encontrado", status_code=303)
        if row.voted_at:
            return RedirectResponse("/?msg=Este+estudiante+ya+registró+su+participación", status_code=303)
        request.session["student_id"] = row.id
        request.session.pop("selected_candidate", None)
    return RedirectResponse("/vote", status_code=303)


@app.get("/vote", response_class=HTMLResponse)
def vote_page(request: Request):
    sid = request.session.get("student_id")
    if not sid:
        return RedirectResponse("/", status_code=303)
    if setting("election_open") != "1":
        request.session.pop("student_id", None)
        return RedirectResponse("/?msg=La+votación+está+cerrada", status_code=303)
    with SessionLocal() as db:
        student = db.get(Student, sid)
        candidates = db.scalars(
            select(Candidate).where(Candidate.active == 1).order_by(cast(Candidate.list_number, Integer), Candidate.list_number, Candidate.id)
        ).all()
        if not student or student.voted_at:
            request.session.pop("student_id", None)
            return RedirectResponse("/?msg=Este+estudiante+ya+votó", status_code=303)
        db.expunge(student)
        for c in candidates:
            db.expunge(c)
    return templates.TemplateResponse(request=request, name="vote.html", context=base_context(request, student=student, candidates=candidates))


@app.post("/vote/select", response_class=HTMLResponse)
def select_vote(request: Request, candidate_id: str = Form(...)):
    sid = request.session.get("student_id")
    if not sid:
        return RedirectResponse("/", status_code=303)
    is_blank = candidate_id == "blank"
    with SessionLocal() as db:
        student = db.get(Student, sid)
        candidate = None if is_blank else db.get(Candidate, int(candidate_id))
        if not student or student.voted_at:
            request.session.pop("student_id", None)
            return RedirectResponse("/?msg=Este+estudiante+ya+votó", status_code=303)
        if not is_blank and (not candidate or not candidate.active):
            return RedirectResponse("/vote", status_code=303)
        request.session["selected_candidate"] = "blank" if is_blank else int(candidate.id)
        db.expunge(student)
        if candidate:
            db.expunge(candidate)
    return templates.TemplateResponse(
        request=request,
        name="confirm.html",
        context=base_context(request, student=student, candidate=candidate, is_blank=is_blank),
    )


@app.post("/vote/confirm", response_class=HTMLResponse)
def confirm_vote(request: Request):
    sid = request.session.get("student_id")
    selected = request.session.get("selected_candidate")
    if not sid or selected is None:
        return RedirectResponse("/", status_code=303)
    if setting("election_open") != "1":
        request.session.clear()
        return RedirectResponse("/?msg=La+votación+está+cerrada", status_code=303)

    try:
        with SessionLocal.begin() as db:
            # En PostgreSQL bloquea la fila del estudiante durante la transacción.
            student = db.scalar(select(Student).where(Student.id == sid).with_for_update())
            if not student or student.voted_at:
                request.session.clear()
                return RedirectResponse("/?msg=Este+estudiante+ya+registró+su+participación", status_code=303)

            candidate_id = None if selected == "blank" else int(selected)
            if candidate_id is not None:
                candidate = db.get(Candidate, candidate_id)
                if not candidate or not candidate.active:
                    return RedirectResponse("/vote", status_code=303)

            db.add(Vote(candidate_id=candidate_id, cast_at=now_dt()))
            student.voted_at = now_dt()
    except Exception:
        request.session.clear()
        raise

    request.session.clear()
    return templates.TemplateResponse(request=request, name="thanks.html", context=base_context(request))


@app.get("/candidate-symbol/{candidate_id}")
def candidate_symbol(candidate_id: int):
    with SessionLocal() as db:
        c = db.get(Candidate, candidate_id)
        if not c or not c.symbol_data:
            raise HTTPException(status_code=404)
        return Response(content=c.symbol_data, media_type=c.symbol_mime or "image/png", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html", context=base_context(request))


@app.post("/admin/login")
def admin_login(request: Request, password: str = Form(...)):
    if password_hash(password) == setting("admin_password_hash"):
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login?error=1", status_code=303)


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


def dashboard_data():
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Student.id))) or 0
        voted = db.scalar(select(func.count(Student.id)).where(Student.voted_at.is_not(None))) or 0
        turnout = round((voted / total * 100), 1) if total else 0

        classrooms = db.execute(
            select(
                Student.grade,
                Student.section,
                func.count(Student.id).label("total"),
                func.sum(case((Student.voted_at.is_not(None), 1), else_=0)).label("voted"),
            )
            .group_by(Student.grade, Student.section)
            .order_by(cast(Student.grade, Integer), Student.grade, Student.section)
        ).all()

        candidates = db.scalars(
            select(Candidate).where(Candidate.active == 1).order_by(cast(Candidate.list_number, Integer), Candidate.list_number, Candidate.id)
        ).all()
        vote_counts = dict(db.execute(
            select(Vote.candidate_id, func.count(Vote.id)).where(Vote.candidate_id.is_not(None)).group_by(Vote.candidate_id)
        ).all())
        blank = db.scalar(select(func.count(Vote.id)).where(Vote.candidate_id.is_(None))) or 0
        total_votes = db.scalar(select(func.count(Vote.id))) or 0

        results = []
        for c in candidates:
            votes = int(vote_counts.get(c.id, 0))
            results.append({
                "id": c.id,
                "list_number": c.list_number,
                "list_name": c.list_name,
                "candidate_name": c.candidate_name,
                "symbol_path": c.symbol_path,
                "votes": votes,
                "pct": round((votes / total_votes * 100), 1) if total_votes else 0,
            })
        results.sort(key=lambda x: (-x["votes"], x["list_number"]))

        classrooms_out = []
        for r in classrooms:
            v = int(r.voted or 0)
            t = int(r.total or 0)
            classrooms_out.append({
                "grade": r.grade,
                "section": r.section,
                "total": t,
                "voted": v,
                "missing": t - v,
                "pct": round((v / t * 100), 1) if t else 0,
            })

    blank_result = {
        "list_number": "—",
        "list_name": "Voto en blanco",
        "candidate_name": "",
        "symbol_path": None,
        "votes": blank,
        "pct": round((blank / total_votes * 100), 1) if total_votes else 0,
    }
    return total, voted, turnout, classrooms_out, results, blank_result, total_votes


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    total, voted, turnout, classrooms, results, blank_result, total_votes = dashboard_data()
    with SessionLocal() as db:
        candidates = db.scalars(select(Candidate).order_by(cast(Candidate.list_number, Integer), Candidate.list_number, Candidate.id)).all()
        for c in candidates:
            db.expunge(c)
    show_results = setting("show_results_live") == "1" or setting("election_open") != "1"
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context=base_context(
            request,
            total=total,
            voted=voted,
            missing=total - voted,
            turnout=turnout,
            classrooms=classrooms,
            results=results,
            blank_result=blank_result,
            total_votes=total_votes,
            candidates=candidates,
            show_results=show_results,
            show_results_live=setting("show_results_live") == "1",
            first_run=setting("first_run") == "1",
        ),
    )


@app.post("/admin/settings")
def admin_settings(
    request: Request,
    school_name: str = Form(...),
    election_title: str = Form(...),
    show_results_live: Optional[str] = Form(None),
):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    set_setting("school_name", school_name.strip())
    set_setting("election_title", election_title.strip())
    set_setting("show_results_live", "1" if show_results_live else "0")
    set_setting("first_run", "0")
    return RedirectResponse("/admin#configuracion", status_code=303)


@app.post("/admin/password")
def admin_password(request: Request, current_password: str = Form(...), new_password: str = Form(...)):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    if password_hash(current_password) != setting("admin_password_hash"):
        return RedirectResponse("/admin?msg=Contraseña+actual+incorrecta#configuracion", status_code=303)
    if len(new_password) < 8:
        return RedirectResponse("/admin?msg=La+nueva+contraseña+debe+tener+al+menos+8+caracteres#configuracion", status_code=303)
    set_setting("admin_password_hash", password_hash(new_password))
    return RedirectResponse("/admin?msg=Contraseña+actualizada#configuracion", status_code=303)


@app.post("/admin/toggle-election")
def admin_toggle_election(request: Request, action: str = Form(...)):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    set_setting("election_open", "1" if action == "open" else "0")
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/candidates/add")
async def admin_candidate_add(
    request: Request,
    list_number: str = Form(...),
    list_name: str = Form(...),
    candidate_name: str = Form(...),
    symbol: Optional[UploadFile] = File(None),
):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)

    symbol_data = None
    symbol_mime = None
    if symbol and symbol.filename:
        ext = Path(symbol.filename).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            return RedirectResponse("/admin?msg=Formato+de+imagen+no+permitido#candidatos", status_code=303)
        symbol_data = await symbol.read()
        if len(symbol_data) > 4 * 1024 * 1024:
            return RedirectResponse("/admin?msg=La+imagen+supera+4MB#candidatos", status_code=303)
        symbol_mime = symbol.content_type or {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[ext]

    with SessionLocal.begin() as db:
        db.add(Candidate(
            list_number=list_number.strip(),
            list_name=list_name.strip(),
            candidate_name=candidate_name.strip(),
            symbol_data=symbol_data,
            symbol_mime=symbol_mime,
            created_at=now_dt(),
            active=1,
        ))
    return RedirectResponse("/admin#candidatos", status_code=303)


@app.post("/admin/candidates/{candidate_id}/toggle")
def admin_candidate_toggle(candidate_id: int, request: Request):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    with SessionLocal.begin() as db:
        row = db.get(Candidate, candidate_id)
        if row:
            row.active = 0 if row.active else 1
    return RedirectResponse("/admin#candidatos", status_code=303)


@app.post("/admin/roster/upload")
async def admin_roster_upload(request: Request, roster: UploadFile = File(...), mode: str = Form("append")):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    filename = roster.filename or ""
    data = await roster.read()
    records = []
    try:
        if filename.lower().endswith(".csv"):
            text = data.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                grade = str(row.get("grado") or row.get("grade") or "").strip()
                section = str(row.get("seccion") or row.get("sección") or row.get("section") or "").strip().upper()
                name = str(row.get("apellidos_nombres") or row.get("nombre") or row.get("nombres") or row.get("full_name") or "").strip()
                if grade and section and name:
                    records.append((grade, section, name))
        elif filename.lower().endswith(".xlsx"):
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            ws = wb.active
            headers = [str(c.value or "").strip().lower() for c in next(ws.iter_rows(min_row=1, max_row=1))]
            idx = {h: i for i, h in enumerate(headers)}
            def find_index(options):
                for o in options:
                    if o in idx:
                        return idx[o]
                return None
            gi = find_index(["grado", "grade"])
            si = find_index(["seccion", "sección", "section"])
            ni = find_index(["apellidos_nombres", "nombre", "nombres", "full_name", "apellidos y nombres"])
            if gi is None or si is None or ni is None:
                raise ValueError("Faltan columnas")
            for row in ws.iter_rows(min_row=2, values_only=True):
                grade = str(row[gi] or "").strip()
                section = str(row[si] or "").strip().upper()
                name = str(row[ni] or "").strip()
                if grade and section and name:
                    records.append((grade, section, name))
        else:
            return RedirectResponse("/admin?msg=Solo+se+admite+CSV+o+XLSX#padron", status_code=303)
    except Exception:
        return RedirectResponse("/admin?msg=No+se+pudo+leer+el+archivo.+Verifica+las+columnas#padron", status_code=303)

    if not records:
        return RedirectResponse("/admin?msg=No+se+encontraron+estudiantes+válidos#padron", status_code=303)

    # elimina duplicados del archivo manteniendo orden
    unique_records = list(dict.fromkeys(records))
    with SessionLocal.begin() as db:
        if mode == "replace":
            votes = db.scalar(select(func.count(Vote.id))) or 0
            if votes:
                return RedirectResponse("/admin?msg=No+se+puede+reemplazar+el+padrón+si+ya+existen+votos#padron", status_code=303)
            db.execute(delete(Student))

        existing = set(db.execute(select(Student.grade, Student.section, Student.full_name)).all())
        added = 0
        for grade, section, name in unique_records:
            if (grade, section, name) not in existing:
                db.add(Student(grade=grade, section=section, full_name=name))
                existing.add((grade, section, name))
                added += 1
    return RedirectResponse(f"/admin?msg=Se+cargaron+{added}+estudiantes#padron", status_code=303)


@app.post("/admin/reset")
def admin_reset(request: Request, confirmation: str = Form(...)):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    if confirmation.strip().upper() != "REINICIAR":
        return RedirectResponse("/admin?msg=Escribe+REINICIAR+para+confirmar#reinicio", status_code=303)
    with SessionLocal.begin() as db:
        db.execute(delete(Vote))
        db.execute(update(Student).values(voted_at=None))
    set_setting("election_open", "0")
    return RedirectResponse("/admin?msg=Votación+reiniciada.+El+padrón+y+los+candidatos+se+conservaron#reinicio", status_code=303)


@app.get("/admin/export/turnout.csv")
def export_turnout(request: Request):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    with SessionLocal() as db:
        rows = db.scalars(select(Student).order_by(cast(Student.grade, Integer), Student.grade, Student.section, Student.full_name)).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["grado", "seccion", "apellidos_nombres", "participo"])
    for r in rows:
        w.writerow([r.grade, r.section, r.full_name, "SI" if r.voted_at else "NO"])
    data = out.getvalue().encode("utf-8-sig")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=participacion_elecciones.csv"})


@app.get("/admin/export/results.csv")
def export_results(request: Request):
    if not admin_required(request):
        return RedirectResponse("/admin/login", status_code=303)
    if setting("election_open") == "1" and setting("show_results_live") != "1":
        return RedirectResponse("/admin?msg=Los+resultados+están+ocultos+mientras+la+elección+está+abierta", status_code=303)
    _, _, _, _, results, blank_result, _ = dashboard_data()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["lista", "nombre_lista", "candidato", "votos", "porcentaje"])
    for r in results:
        w.writerow([r["list_number"], r["list_name"], r["candidate_name"], r["votes"], r["pct"]])
    w.writerow(["", "Voto en blanco", "", blank_result["votes"], blank_result["pct"]])
    data = out.getvalue().encode("utf-8-sig")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=resultados_elecciones.csv"})


@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(select(1))
        return {"status": "ok", "database": "postgresql" if "postgresql" in DATABASE_URL else "sqlite"}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
