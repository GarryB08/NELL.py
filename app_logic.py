"""Pure business rules used by the Ailyn House app and its tests."""

TIER_TABLE = {
    0.1: {"Labor": 0.00, "Skill": 0.00, "Forman": 0.00},
    0.2: {"Labor": 62.50, "Skill": 81.25, "Forman": 100.00},
    0.3: {"Labor": 125.00, "Skill": 162.50, "Forman": 200.00},
    0.4: {"Labor": 187.50, "Skill": 243.75, "Forman": 300.00},
    0.5: {"Labor": 250.00, "Skill": 325.00, "Forman": 400.00},
    0.6: {"Labor": 312.50, "Skill": 406.25, "Forman": 500.00},
    0.7: {"Labor": 375.00, "Skill": 487.50, "Forman": 600.00},
    0.8: {"Labor": 437.50, "Skill": 568.75, "Forman": 700.00},
    0.9: {"Labor": 500.00, "Skill": 650.00, "Forman": 800.00},
}
FULL_DAY_RATES = {"Labor": 500.00, "Skill": 650.00, "Forman": 800.00}


def get_partial_rate(decimal_part, role):
    return TIER_TABLE.get(round(decimal_part, 1), {}).get(role, 0.0)


def calculate_labor_pay(worked_days, role):
    full_days = int(worked_days)
    partial_days = round(worked_days - full_days, 1)
    full_pay = full_days * FULL_DAY_RATES.get(role, 0.0)
    partial_pay = get_partial_rate(partial_days, role)
    return full_pay + partial_pay, full_pay, partial_pay


def monthly_totals(records, labor_records, payroll_expenses, month):
    materials = sum(float(r.get("amount", 0)) for r in records if r.get("type") == "material" and r.get("month") == month)
    construction = sum(float(r.get("amount", 0)) for r in records if r.get("type") == "expense" and r.get("month") == month)
    labor = sum(float(r.get("net", 0)) for r in labor_records if r.get("month") == month)
    payroll = sum(float(r.get("price", 0)) for r in payroll_expenses if r.get("month") == month)
    return {"materials": materials, "construction": construction, "labor": labor, "payroll": payroll,
            "total": materials + construction + labor + payroll}
