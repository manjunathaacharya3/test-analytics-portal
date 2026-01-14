# routers/reports.py
import json
import uuid
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.database import get_db
from database.tables.execution import Execution
from database.tables.module import Module
from database.tables.project import Project
from service.schema.report import ReportResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def compute_metrics(cucumber_json: List[dict]) -> Tuple[int, int, int, float, float]:
    """
    Compute metrics at the *scenario* level (not step level).
    Returns: (passed_count, failed_count, total_scenarios, total_duration_seconds, pass_rate_percent)
    """
    passed = 0
    failed = 0
    total_scenarios = 0
    total_duration_seconds = 0.0

    for feature in cucumber_json:
        elements = feature.get("elements", []) or []
        for element in elements:
            total_scenarios += 1
            steps = element.get("steps", []) or []

            # Determine scenario status:
            scenario_failed = False
            scenario_has_pass = False
            scenario_duration = 0.0

            for step in steps:
                res = step.get("result", {}) or {}
                step_status = (res.get("status") or "").lower()
                # duration in cucumber jvm is typically in nanoseconds; guard missing durations
                step_duration_ns = res.get("duration", 0) or 0
                try:
                    # treat numeric durations as nanoseconds (common), convert to seconds
                    step_duration = float(step_duration_ns) / 1e9
                except Exception:
                    step_duration = 0.0

                scenario_duration += step_duration

                if step_status == "failed":
                    scenario_failed = True
                elif step_status == "passed":
                    scenario_has_pass = True
                # other statuses (skipped, undefined) are ignored for pass/failed decision

            total_duration_seconds += scenario_duration

            if scenario_failed:
                failed += 1
            else:
                # If no failing step, consider it Passed if there was at least one passed step,
                # otherwise Skipped (we'll count skipped scenarios as neither passed nor failed).
                if scenario_has_pass:
                    passed += 1
                else:
                    # treat skipped as neither passed nor failed (still contributes to total)
                    # If you prefer to classify skipped as passed or failed adjust here.
                    pass

    pass_rate = (passed / total_scenarios * 100.0) if total_scenarios > 0 else 0.0
    return int(passed), int(failed), int(total_scenarios), float(total_duration_seconds), float(pass_rate)


def compute_status(pass_rate: float) -> str:
    """Map pass-rate percent to a status string used in the UI/backend."""
    if pass_rate >= 90:
        return "Green"
    elif pass_rate >= 70:
        return "Yellow"
    return "Red"


@router.post("/upload", response_model=ReportResponse, status_code=201)
async def publish_report_file(
    project_name: str = Form(...),
    module_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # 1. Read uploaded JSON file
    try:
        contents = await file.read()
        cucumber_json = json.loads(contents.decode("utf-8"))
        if not isinstance(cucumber_json, list):
            # some cucumber tooling might wrap results - but we expect list of features
            raise ValueError("Cucumber JSON must be a list of features")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(exc)}")

    # 2. Find project
    result = await db.execute(select(Project).where(Project.name == project_name))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 3. Find/create module
    result = await db.execute(
        select(Module).where(Module.name == module_name, Module.project_id == project.id)
    )
    module = result.scalar_one_or_none()
    if not module:
        module = Module(name=module_name, project_id=project.id)
        db.add(module)
        await db.commit()
        await db.refresh(module)

    # 4. Extract metrics at scenario level
    passed_count, failed_count, total_scenarios, total_duration_seconds, pass_rate = compute_metrics(cucumber_json)
    status = compute_status(pass_rate)

    # 5. Save execution (store scenario-level metrics; duration in seconds)
    execution = Execution(
        id=str(uuid.uuid4()),
        module_id=module.id,
        passed=passed_count,
        failed=failed_count,
        total=total_scenarios,
        duration=total_duration_seconds,
        status=status,
        # raw_report can be stored if you have a JSON column or separate storage
    )
    db.add(execution)

    # 6. Save scenarios for this execution
    from database.tables.scenario import Scenario

    for feature in cucumber_json:
        for element in feature.get("elements", []) or []:
            scenario_name = element.get("name", "Unnamed Scenario")

            # Determine scenario-level status for storing (consistent with above logic)
            steps = element.get("steps", []) or []
            scenario_failed = False
            scenario_has_pass = False
            failed_step = None
            error = None
            scenario_duration = 0.0

            for step in steps:
                res = step.get("result", {}) or {}
                step_status = (res.get("status") or "").lower()
                step_duration_ns = res.get("duration", 0) or 0
                try:
                    step_duration = float(step_duration_ns) / 1e9
                except Exception:
                    step_duration = 0.0
                scenario_duration += step_duration

                if step_status == "failed":
                    scenario_failed = True
                    failed_step = step.get("name")
                    # some Cucumber runners use "error_message" or "message"
                    error = res.get("error_message") or res.get("message") or None
                    # break on first failure (we record failed_step/error)
                    break
                elif step_status == "passed":
                    scenario_has_pass = True

            if scenario_failed:
                sc_status = "❌ Failed"
            elif scenario_has_pass:
                sc_status = "Passed"
            else:
                sc_status = "Skipped"

            tags = [t.get("name") for t in (element.get("tags") or []) if t.get("name")]

            # Attachments: cucumber JSON format may include 'embeddings' or similar
            attachments = element.get("embeddings") or []
            # convert attachments to a list of paths or identifiers as you expect in your app
            # For now store placeholder empty list if none
            attachments_out = []
            for emb in attachments:
                # embed objects vary by runner — keep a safe representation if present
                try:
                    if isinstance(emb, dict) and emb.get("name"):
                        attachments_out.append(emb.get("name"))
                except Exception:
                    pass

            scenario = Scenario(
                id=str(uuid.uuid4()),
                execution_id=execution.id,
                scenario=scenario_name,
                status=sc_status,
                tags=tags,
                duration=scenario_duration,
                failed_step=failed_step,
                error=error,
                attachments=attachments_out,
            )
            db.add(scenario)

    # 7. Commit everything
    await db.commit()
    await db.refresh(execution)

    # 8. Return a small summary
    return ReportResponse(
        execution_id=execution.id,
        status=execution.status,
        pass_rate=round(pass_rate, 2),
    )
