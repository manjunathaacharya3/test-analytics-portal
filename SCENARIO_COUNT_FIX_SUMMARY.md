# Scenario Count Fix - Summary

## ✅ Problem Solved

**Before:**  
If a module has 4 scenarios and is executed twice → Shows **8 scenarios** ❌

**After:**  
If a module has 4 scenarios and is executed twice → Shows **4 unique scenarios** ✅

## 📝 What Was Changed

### File: `backend/app/projects/repository.py`

**Changed Lines 105-107 from:**
```python
func.coalesce(func.sum(Report.total_scenarios), 0).label("total_tests"),
func.coalesce(func.sum(Report.passed_scenarios), 0).label("passed_tests"),
func.coalesce(func.sum(Report.failed_scenarios), 0).label("failed_tests"),
```

**To:**
```python
func.count(func.distinct(Scenario.name)).label("total_tests"),
func.sum(
    case(
        ((Scenario.status == 'passed') & (Report.created_at == latest_report_subquery.c.latest_created_at), 1),
        else_=0
    )
).label("passed_tests"),
func.sum(
    case(
        ((Scenario.status == 'failed') & (Report.created_at == latest_report_subquery.c.latest_created_at), 1),
        else_=0
    )
).label("failed_tests"),
```

**Key Changes:**
1. ✅ Count `DISTINCT Scenario.name` instead of summing `Report.total_scenarios`
2. ✅ Added join to `Scenario` table
3. ✅ Use latest execution for passed/failed counts
4. ✅ Filter by status directly from `Scenario.status` field

## 🎯 Expected Behavior

### Example Scenario

**Setup:**
- Module: "User Authentication"
- Scenarios: 
  1. "User can login with valid credentials"
  2. "User cannot login with invalid password"
  3. "User can logout successfully"
  4. "User can reset password"

**Execution 1 (2024-01-15 10:00):**
- All 4 scenarios: PASSED ✅
- Report.total_scenarios = 4
- Report.passed_scenarios = 4
- Report.failed_scenarios = 0

**Execution 2 (2024-01-15 14:00):**
- Scenario 2 FAILED (password validation broke)
- Report.total_scenarios = 4
- Report.passed_scenarios = 3
- Report.failed_scenarios = 1

### Old Behavior (WRONG) ❌

```
Projects Page:
- Total Test Cases: 8  (4 + 4)
- Passed: 7  (4 + 3)
- Failed: 1  (0 + 1)
```

### New Behavior (CORRECT) ✅

```
Projects Page:
- Total Test Cases: 4  (unique scenarios)
- Passed: 3  (from latest execution)
- Failed: 1  (from latest execution)
```

## 📊 Where This Applies

### Projects Page
- **Total Test Cases** card → Shows unique scenarios
- **Each project card** → "Total Tests" shows unique count

### Execution Summary Page
- Stats are **per execution**, so no change needed (already correct)

### Module Details Page
- Module header stats → Will show unique scenario count

### Analytics
- Dashboard metrics → Already counting individual executions (correct for analytics)
- Trends → Already using execution-based counts (correct for trends)

## 🔍 Verification

### Test Case 1: Single Execution

```sql
-- Create module with 4 scenarios, execute once
INSERT INTO modules (name, project_id) VALUES ('Auth', 'proj-123');
INSERT INTO reports (module_id, total_scenarios, passed_scenarios) 
VALUES ('mod-1', 4, 4);
INSERT INTO scenarios (report_id, name, status) VALUES
  ('rep-1', 'Login', 'passed'),
  ('rep-1', 'Logout', 'passed'),
  ('rep-1', 'Reset Password', 'passed'),
  ('rep-1', 'Register', 'passed');

-- Expected: total_tests = 4 ✅
```

### Test Case 2: Multiple Executions (Same Scenarios)

```sql
-- Execute module again (same 4 scenarios)
INSERT INTO reports (module_id, total_scenarios, passed_scenarios, failed_scenarios) 
VALUES ('mod-1', 4, 3, 1);
INSERT INTO scenarios (report_id, name, status) VALUES
  ('rep-2', 'Login', 'passed'),
  ('rep-2', 'Logout', 'passed'),
  ('rep-2', 'Reset Password', 'failed'),  -- Now failed
  ('rep-2', 'Register', 'passed');

-- Expected: 
-- total_tests = 4 (4 unique scenario names)
-- passed_tests = 3 (from latest execution)
-- failed_tests = 1 (from latest execution)
```

### Test Case 3: Multiple Modules

```sql
-- Project with 2 modules
Module 1: 4 unique scenarios, executed 2 times = 8 scenario records
Module 2: 3 unique scenarios, executed 3 times = 9 scenario records

-- Expected:
-- total_tests = 7 (4 + 3 unique scenario names)
-- NOT 17 (8 + 9 scenario records)
```

## ⚙️ Technical Details

### SQL Query (Simplified)

```sql
SELECT 
    p.id,
    p.name,
    COUNT(DISTINCT s.name) as total_tests,  -- Unique scenarios
    SUM(CASE 
        WHEN s.status = 'passed' AND r.created_at = latest.created_at 
        THEN 1 ELSE 0 
    END) as passed_tests,  -- From latest execution
    SUM(CASE 
        WHEN s.status = 'failed' AND r.created_at = latest.created_at 
        THEN 1 ELSE 0 
    END) as failed_tests   -- From latest execution
FROM projects p
LEFT JOIN modules m ON m.project_id = p.id
LEFT JOIN reports r ON r.module_id = m.id
LEFT JOIN (
    SELECT module_id, MAX(created_at) as created_at
    FROM reports
    GROUP BY module_id
) latest ON latest.module_id = m.id
LEFT JOIN scenarios s ON s.report_id = r.id
GROUP BY p.id, p.name;
```

### Why Use `DISTINCT Scenario.name`?

1. **Scenario.name is NOT unique** in the database
   - Same scenario "User Login" exists multiple times (one per execution)
   - We need `DISTINCT` to count each scenario name once

2. **Alternative: Use Scenario.id with filtering**
   - Could filter to latest execution first, then count
   - More complex query, same result

3. **Why not use Report.total_scenarios?**
   - It's an aggregated number per report
   - SUM adds them up across executions (wrong for unique count)

## 🚀 Deployment Steps

1. ✅ Code changes deployed (repository.py updated)
2. ⚠️ **Clear Redis cache** (important!)
   ```bash
   docker exec -it test-analytics-portal-redis-1 redis-cli FLUSHALL
   ```
3. ✅ Restart backend
4. ✅ Verify on frontend:
   - Check Projects page → Total Test Cases
   - Check individual project cards → Total Tests
   - Compare with database query

## 📋 Post-Deployment Checklist

- [ ] Projects page shows correct unique scenario count
- [ ] Total Test Cases card matches database COUNT DISTINCT query
- [ ] Passed/Failed counts reflect latest execution
- [ ] Multiple executions don't inflate the count
- [ ] Analytics still work (execution-based counts)
- [ ] Trends still show daily execution stats

## 🔄 Related Pages That May Need Updates

1. **Execution Summary** - ✅ Already correct (per-execution stats)
2. **Module Details** - May need similar fix if using SUM
3. **Trends** - ✅ Already correct (time-series of executions)
4. **AI Failure Analysis** - ✅ Counts failed scenarios (correct)

## 📚 References

- [FIX_UNIQUE_SCENARIO_COUNT.md](FIX_UNIQUE_SCENARIO_COUNT.md) - Detailed technical documentation
- [backend/app/projects/repository.py](backend/app/projects/repository.py) - Updated code

## ✨ Benefits

1. ✅ **Accurate metrics** - Shows actual number of test scenarios
2. ✅ **User expectations** - "I wrote 4 tests" → sees 4, not 8
3. ✅ **Consistent** - Count doesn't change just because you run tests more often
4. ✅ **Meaningful** - Total tests = test coverage, not execution count
