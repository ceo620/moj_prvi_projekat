from decimal import Decimal

from fastapi.templating import Jinja2Templates

from app.models import Project

templates = Jinja2Templates(directory="app/templates")


def build_report_context(project: Project) -> dict:
    total_expenses = sum((e.amount for e in project.expenses), Decimal("0.00"))
    milestone_count = len(project.milestones)
    completed_milestones = sum(1 for m in project.milestones if m.status.value == "completed")

    return {
        "project": project,
        "total_expenses": total_expenses,
        "milestone_count": milestone_count,
        "completed_milestones": completed_milestones,
    }
