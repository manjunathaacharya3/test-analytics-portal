# Fix: Count Unique Scenarios Instead of Summing Execution Counts

## Problem

**Current Behavior:**
- If a module has 4 scenarios and is executed twice, the count shows **8**
- This is because we're using `SUM(Report.total_scenarios)` which adds up counts from all executions

**Expected Behavior:**
- Should show **4** (the number of unique test scenarios)
- Scenario count should represent unique test cases, not total executions

## Root Cause

### Current Implementation

```python
# backend/app/projects/repository.py (line 105)
func.coalesce(func.sum(Report.total_scenarios), 0).label("total_tests")
```

This sums the `total_scenarios` field from ALL reports:
- Report 1 (Execution 1): total_scenarios = 4
- Report 2 (Execution 2): total_scenarios = 4
- **SUM = 8** ❌

### Correct Approach

Count **distinct scenario names** from the Scenario table:
```python
func.count(func.distinct(Scenario.name)).label("total_tests")
```

This counts unique scenario names:
- Scenario 1: "User Login"
- Scenario 2: "User Logout"
- Scenario 3: "Password Reset"
- Scenario 4: "User Registration"
- **COUNT DISTINCT = 4** ✅

## Database Schema

```
Project (1) ──┬──→ (N) Module (1) ──┬──→ (N) Report
              │                      │       │
              │                      │       ├── total_scenarios: int
              │                      │       ├── passed_scenarios: int
              │                      │       ├── failed_scenarios: int
              │                      │       │
              │                      │       └──→ (N) Scenario
              │                      │              ├── name: str (NOT UNIQUE)
              │                      │              ├── status: str
              │                      │              ├── feature: str
              │                      │              └── ...
              │                      │
              │                      └── Unique scenarios = COUNT(DISTINCT Scenario.name)
              │
              └── Total unique scenarios = COUNT(DISTINCT Scenario.name) across all modules
```

**Note:** `Scenario.name` is NOT unique in the database because the same scenario can be executed multiple times. We need to use `COUNT(DISTINCT Scenario.name)` to get unique counts.

## Files to Fix

### 1. Projects Repository (Primary Fix)

**File:** `backend/app/projects/repository.py`

**Line 105-107:** Change from SUM to COUNT DISTINCT

```python
# BEFORE (WRONG):
func.coalesce(func.sum(Report.total_scenarios), 0).label("total_tests"),
func.coalesce(func.sum(Report.passed_scenarios), 0).label("passed_tests"),
func.coalesce(func.sum(Report.failed_scenarios), 0).label("failed_tests"),

# AFTER (CORRECT):
# Import Scenario model
from app.modules.reports.models import Report, Scenario

# Count unique scenarios by name
func.count(func.distinct(Scenario.name)).label("total_tests"),
func.sum(
    func.case(
        (Scenario.status == 'passed', 1),
        else_=0
    )
).label("passed_tests"),
func.sum(
    func.case(
        (Scenario.status == 'failed', 1),
        else_=0
    )
).label("failed_tests"),
```

**Line 113:** Add Scenario join

```python
# BEFORE:
.outerjoin(Module, Module.project_id == Project.id)
.outerjoin(Report, Report.module_id == Module.id)

# AFTER:
.outerjoin(Module, Module.project_id == Project.id)
.outerjoin(Report, Report.module_id == Module.id)
.outerjoin(Scenario, Scenario.report_id == Report.id)  # Add this line
```

### 2. Analytics Router (Secondary Fix)

**File:** `backend/app/modules/analytics/router.py`

**Lines 128-130:** Same fix as above

```python
# BEFORE:
func.sum(Report.total_scenarios).label("total_tests"),
func.sum(Report.passed_scenarios).label("passed_tests"),
func.sum(Report.failed_scenarios).label("failed_tests"),

# AFTER:
func.count(func.distinct(Scenario.name)).label("total_tests"),
func.sum(func.case((Scenario.status == 'passed', 1), else_=0)).label("passed_tests"),
func.sum(func.case((Scenario.status == 'failed', 1), else_=0)).label("failed_tests"),
```

### 3. Analytics Service (Secondary Fix)

**File:** `backend/app/modules/analytics/service.py`

**Lines 104-106:** Same fix as above

## Alternative Approach: Use Latest Report Only

If you want to show metrics from the **latest execution** instead of unique scenarios:

```python
# Subquery to get latest report per module
latest_reports = (
    select(
        Report.module_id,
        func.max(Report.created_at).label("latest_execution")
    )
    .group_by(Report.module_id)
).subquery()

# Main query using only latest reports
stmt = (
    select(
        Project,
        func.count(func.distinct(Module.id)).label("modules_count"),
        func.sum(Report.total_scenarios).label("total_tests"),
        func.sum(Report.passed_scenarios).label("passed_tests"),
        func.sum(Report.failed_scenarios).label("failed_tests"),
    )
    .outerjoin(Module, Module.project_id == Project.id)
    .outerjoin(
        Report,
        and_(
            Report.module_id == Module.id,
            Report.created_at == latest_reports.c.latest_execution
        )
    )
    .group_by(Project.id)
)
```

This approach uses `total_scenarios` from the latest report only, avoiding duplicates.

## Recommended Solution

**Use COUNT DISTINCT for unique scenarios** (first approach) because:

1. ✅ Accurately represents the number of test scenarios in a module
2. ✅ Doesn't depend on execution timing
3. ✅ Matches user expectations ("I have 4 test scenarios")
4. ✅ More resilient to data inconsistencies

## Testing

### Test Scenario

1. Create a module with 4 scenarios
2. Execute the module twice
3. Verify counts:

**Expected Results:**
- Total Scenarios: **4** (not 8)
- If all passed both times:
  - Passed: **4** (scenarios that passed in latest execution)
  - Failed: **0**

### Verification Queries

```sql
-- Check scenario counts
SELECT 
    m.name as module_name,
    COUNT(DISTINCT s.name) as unique_scenarios,
    COUNT(s.id) as total_executions
FROM modules m
JOIN reports r ON r.module_id = m.id
JOIN scenarios s ON s.report_id = r.id
GROUP BY m.id, m.name;

-- Expected:
-- module_name    | unique_scenarios | total_executions
-- Auth Module    | 4                | 8 (4 scenarios × 2 runs)
```

## Migration Notes

1. **No database migration needed** - only query changes
2. **Backward compatible** - doesn't change data structure
3. **Performance impact:** Minimal - adds one more join
4. **Cache invalidation:** Clear Redis cache after deployment

## Related Issues

This fix also resolves:
- Incorrect total test counts in Projects page
- Incorrect metrics in Execution Summary
- Incorrect analytics in Module Details
- Confusing numbers in Trends page

## Implementation Checklist

- [ ] Update `backend/app/projects/repository.py`
- [ ] Update `backend/app/modules/analytics/router.py`
- [ ] Update `backend/app/modules/analytics/service.py`
- [ ] Add Scenario import where needed
- [ ] Test with multiple executions
- [ ] Verify frontend displays correct counts
- [ ] Clear Redis cache
- [ ] Update documentation
- [ ] Run integration tests
