# Example: Parallel Code Analysis Across Modules

This example demonstrates parallel independent analysis where 6 workers analyze different code modules simultaneously.

## User Request

```
"Review code quality across the authentication system modules:
- auth.py
- user_manager.py
- session.py
- permissions.py
- token_handler.py
- oauth_provider.py

Focus on security vulnerabilities, code quality, and best practices."
```

## Phase 0: Request Understanding

**Sequential-Thinking Analysis**:
```json
{
  "goal": "Comprehensive code quality review of authentication system",
  "success_criteria": [
    "Security vulnerabilities identified",
    "Code quality issues documented",
    "Best practice violations noted",
    "Actionable recommendations provided"
  ],
  "requirements": [
    "Review all 6 modules",
    "Focus on security",
    "Assess code quality",
    "Check best practices"
  ],
  "constraints": ["No modifications, analysis only"],
  "output_format": "Security and quality report per module",
  "task_type": "analysis",
  "complexity": "medium"
}
```

## Phase 1: Task Decomposition

**AI-Generated Task Plan**:
```json
{
  "subtasks": [
    {
      "id": "analyze_auth_py",
      "description": "Security and quality analysis of auth.py",
      "complexity": "medium",
      "output_format": "Markdown report with sections: Security, Quality, Recommendations",
      "worker_type": "analysis",
      "data_context": "auth.py source code"
    },
    {
      "id": "analyze_user_manager",
      "description": "Security and quality analysis of user_manager.py",
      "complexity": "medium",
      "output_format": "Markdown report",
      "worker_type": "analysis",
      "data_context": "user_manager.py source code"
    },
    {
      "id": "analyze_session",
      "description": "Security and quality analysis of session.py",
      "complexity": "medium",
      "output_format": "Markdown report",
      "worker_type": "analysis",
      "data_context": "session.py source code"
    },
    {
      "id": "analyze_permissions",
      "description": "Security and quality analysis of permissions.py",
      "complexity": "medium",
      "output_format": "Markdown report",
      "worker_type": "analysis",
      "data_context": "permissions.py source code"
    },
    {
      "id": "analyze_token_handler",
      "description": "Security and quality analysis of token_handler.py",
      "complexity": "high",
      "output_format": "Markdown report",
      "worker_type": "analysis",
      "data_context": "token_handler.py source code"
    },
    {
      "id": "analyze_oauth_provider",
      "description": "Security and quality analysis of oauth_provider.py",
      "complexity": "high",
      "output_format": "Markdown report",
      "worker_type": "analysis",
      "data_context": "oauth_provider.py source code"
    }
  ],
  "dependencies": {},
  "execution_order": ["all_parallel"],
  "reasoning": "All modules can be analyzed independently. No dependencies between analyses."
}
```

## Phase 2: Parallelization Strategy

**Algorithm Application**:
```python
parallel_tasks = 6
avg_complexity = "medium"  # 4 medium, 2 high → medium dominant
has_dependencies = False   # No dependencies

# Apply algorithm:
# has_dependencies = False → continue
# parallel_tasks = 6 → not <= 2, not <= 5
# avg_complexity = "medium" → not "high"
# → return min(5, 6) = 5 workers

worker_count = 5
```

**Parallelization Config**:
```json
{
  "worker_count": 5,
  "parallel_groups": [
    ["analyze_auth_py"],
    ["analyze_user_manager"],
    ["analyze_session"],
    ["analyze_permissions"],
    ["analyze_token_handler", "analyze_oauth_provider"]
  ],
  "sequential_tasks": [],
  "parallel_tasks_count": 6,
  "sequential_tasks_count": 0
}
```

**Note**: Worker 5 handles 2 tasks sequentially (token_handler, then oauth_provider) since we have 6 tasks but 5 workers.

## Phase 3: Worker Prompt Generation

**Example Prompt for Worker 1** (analyze_auth_py):

```
=== SYSTEM CONTEXT ===
You are Worker 1 of 5 in a parallel multi-agent code analysis orchestration.

Your role: Analyze auth.py for security vulnerabilities and code quality issues.

Coordination mode: PARALLEL
- Your results will be synthesized alongside 4 other workers
- Each worker analyzes a different module independently
- Do not make assumptions about other modules (other workers handle those)

Total orchestration goal: Comprehensive security and quality review of authentication system

=== TASK DEFINITION ===
TASK ID: analyze_auth_py
DESCRIPTION: Security and quality analysis of auth.py

COMPLEXITY: Medium (requires security expertise and code review skills)

EXPECTED OUTPUT:
- Security vulnerabilities identified with severity
- Code quality issues documented
- Best practice violations noted
- Actionable recommendations with priority

=== METHODOLOGY ===
Follow this systematic code review approach:

1. Security Analysis
   - Check for SQL injection vulnerabilities
   - Verify input validation and sanitization
   - Review authentication logic for bypasses
   - Check password handling (hashing, storage)
   - Assess session management security
   - Review error handling (no info leakage)

2. Code Quality Assessment
   - Evaluate code complexity (cyclomatic complexity)
   - Check for code duplication
   - Assess naming conventions and readability
   - Review error handling completeness
   - Check for deprecated patterns

3. Best Practices Review
   - Verify adherence to OWASP guidelines
   - Check for proper logging (without secrets)
   - Assess test coverage implications
   - Review dependency security

=== DATA/CONTENT ===
DATA SOURCE: auth.py

FILE CONTEXT:
- Core authentication module for web application
- Handles user login, logout, password reset
- Integrates with user_manager.py and session.py
- ~450 lines of Python code

SCOPE:
- Focus on this module only (other workers handle other modules)
- Flag issues requiring cross-module review
- Include both critical and minor issues

[auth.py source code would be inserted here]

=== OUTPUT FORMAT ===
OUTPUT FORMAT: Markdown report

Required sections:
1. Executive Summary (2-3 sentences)
2. Security Findings (table format)
3. Code Quality Issues (bulleted list)
4. Best Practice Violations (bulleted list)
5. Recommendations (prioritized: Critical, High, Medium, Low)

Example security finding:
| Issue | Severity | Location | Description | Recommendation |
|-------|----------|----------|-------------|----------------|
| SQL Injection | Critical | Line 127 | User input directly concatenated in query | Use parameterized queries |

AVOID:
- Generic advice without specific line numbers
- Theoretical vulnerabilities not present in code
- Comparisons to other modules (stay focused on auth.py)

=== QUALITY CRITERIA ===
Your output will be evaluated on:

1. Security Depth (40% weight)
   ✓ All OWASP Top 10 categories checked
   ✓ Specific vulnerabilities with line numbers
   ✓ Severity assessment justified

2. Actionability (35% weight)
   ✓ Recommendations include specific code changes
   ✓ Issues prioritized by severity
   ✓ No vague suggestions

3. Completeness (25% weight)
   ✓ All required sections present
   ✓ Both critical and minor issues covered
   ✓ Code quality and security both addressed

SUCCESS CRITERIA:
- At least 3 security findings (or explicit "no vulnerabilities found")
- All findings include line numbers and specific evidence
- Recommendations are actionable (not just "improve security")

=== CRITICAL CONSTRAINTS ===

1. NO HALLUCINATION
   ✗ Do not invent vulnerabilities not present in code
   ✗ Do not cite non-existent line numbers
   ✗ Do not claim issues exist without evidence
   ✓ Only report what you actually find in auth.py

2. EXACT CITATIONS REQUIRED
   - Every issue must include line number
   - Every finding must quote relevant code snippet
   - Format: "Issue at line X: `code_snippet`"

3. STAY ON TASK
   ✗ Do not analyze other modules (that's other workers' jobs)
   ✗ Do not make system-wide architectural recommendations
   ✓ Focus exclusively on auth.py

4. USER CONSTRAINTS
   - This is analysis only (no code modifications)
   - Flag cross-module issues but don't analyze them deeply
```

## Phase 4: Parallel Worker Execution

**Execution Timeline**:
```
T+0s:  Workers 1-5 start in parallel
T+45s: Worker 2 completes (user_manager.py)
T+62s: Worker 3 completes (session.py)
T+78s: Worker 1 completes (auth.py)
T+83s: Worker 4 completes (permissions.py)
T+91s: Worker 5 completes task 1 (token_handler.py)
T+91s: Worker 5 starts task 2 (oauth_provider.py)
T+134s: Worker 5 completes task 2 (oauth_provider.py)

Total execution time: 134 seconds (vs ~450s if sequential)
```

## Phase 5: Response Evaluation

**Worker 1 Evaluation** (analyze_auth_py):

**Layer 1 - Structural**: 100/100
- ✓ 847 characters, well-structured with headers and tables

**Layer 2 - Completeness**: 95/100
- ✓ All keywords present (security, vulnerabilities, quality)
- ✓ All required sections present
- ✗ Missing explicit test coverage discussion → -5

**Layer 3 - Hallucination**: 100/100
- ✓ All findings include line numbers
- ✓ Code snippets provided
- ✓ No vague claims

**Final Score**: (100×0.25) + (95×0.45) + (100×0.30) = **97.75/100**
**Quality Gate**: ACCEPT

**Summary Across All Workers**:
```json
{
  "individual_evaluations": {
    "worker_1": {"score": 97.75, "quality_gate": "accept"},
    "worker_2": {"score": 89.5, "quality_gate": "accept"},
    "worker_3": {"score": 91.0, "quality_gate": "accept"},
    "worker_4": {"score": 76.5, "quality_gate": "flag"},
    "worker_5_task1": {"score": 93.0, "quality_gate": "accept"},
    "worker_5_task2": {"score": 88.0, "quality_gate": "accept"}
  },
  "overall_quality": {
    "average_score": 89.3,
    "quality": "good"
  },
  "passed_workers": 5,
  "flagged_workers": 1,
  "failed_workers": 0
}
```

## Phase 6: Result Synthesis

**Strategy Selected**: Aggregation (independent parallel tasks)

**Synthesis Approach**:
1. Executive summary across all modules
2. Individual module sections (full worker outputs)
3. Cross-module security patterns identified
4. System-wide recommendations

**Example Synthesis Output** (excerpt):

```markdown
# Authentication System Code Review - Multi-Module Analysis

## Executive Summary

Analyzed 6 modules of the authentication system (auth.py, user_manager.py,
session.py, permissions.py, token_handler.py, oauth_provider.py).

**Critical Findings**:
- 3 high-severity security vulnerabilities requiring immediate attention
- 12 medium-severity issues across modules
- 8 best practice violations

**Common Patterns**:
- Input validation inconsistent across modules (4/6 modules affected)
- Password hashing uses bcrypt consistently (good)
- Session token generation varies in entropy (security concern)

**Overall System Security**: MODERATE (critical issues require fixes)

---

## Module 1: auth.py (Worker 1 - Quality: 98/100)

### Executive Summary
Core authentication logic is generally sound but contains 1 critical SQL
injection vulnerability and several minor quality issues.

### Security Findings

| Issue | Severity | Location | Description | Recommendation |
|-------|----------|----------|-------------|----------------|
| SQL Injection | Critical | Line 127 | User input directly concatenated | Use parameterized queries |
| Weak Password Policy | Medium | Line 89 | Minimum 6 chars, no complexity | Require 12+ chars, mixed case |
| Error Info Leakage | Low | Line 201 | Stack trace exposed to user | Generic error messages |

### Code Quality Issues
- High cyclomatic complexity in `authenticate()` (complexity: 14) [Line 112-145]
- Duplicate password validation logic (also in user_manager.py) [Line 87-94]
- Magic number for session timeout (use constant) [Line 156]

### Recommendations

**Critical** (Fix within 24 hours):
1. Fix SQL injection at line 127:
   ```python
   # CURRENT (VULNERABLE):
   query = f"SELECT * FROM users WHERE email = '{email}'"

   # RECOMMENDED:
   query = "SELECT * FROM users WHERE email = %s"
   cursor.execute(query, (email,))
   ```

**High** (Fix within 1 week):
2. Strengthen password policy at line 89...

---

## Module 2: user_manager.py (Worker 2 - Quality: 90/100)

### Executive Summary
User management logic is well-structured but lacks input sanitization in
user creation flow.

### Security Findings

| Issue | Severity | Location | Description | Recommendation |
|-------|----------|----------|-------------|----------------|
| XSS Vulnerability | High | Line 67 | User input not escaped in error msg | HTML-escape all user input |
| No Rate Limiting | Medium | Line 34 | Account creation unlimited | Add rate limiting |

[... continues for all modules ...]

---

## Cross-Module Security Analysis

### Pattern 1: Input Validation Inconsistency (4 modules affected)
- **auth.py**: Uses regex validation
- **user_manager.py**: Uses length checks only
- **permissions.py**: No validation
- **oauth_provider.py**: Uses regex validation

**Recommendation**: Establish common validation library used by all modules

### Pattern 2: Session Token Generation Entropy
- **auth.py**: Uses `os.urandom(32)` ✓ Good (256 bits)
- **session.py**: Uses `random.randint()` ✗ Weak (predictable)
- **oauth_provider.py**: Uses `secrets.token_urlsafe()` ✓ Good

**Recommendation**: Standardize on `secrets` module across all token generation

### Pattern 3: Error Handling
- 5/6 modules expose stack traces in error responses
- Only oauth_provider.py uses generic error messages consistently

**Recommendation**: Implement centralized error handler with generic messages

---

## System-Wide Recommendations

### Critical (Immediate Action)
1. **Fix SQL Injection in auth.py** (Line 127) - HIGHEST PRIORITY
2. **Replace weak RNG in session.py** (Line 45) - Security risk
3. **Sanitize user input in user_manager.py** (Line 67) - XSS risk

### High Priority (This Sprint)
4. Create shared input validation library
5. Implement centralized error handling
6. Add rate limiting to user creation and authentication
7. Standardize session token generation

### Medium Priority (Next Sprint)
8. Refactor `auth.authenticate()` to reduce complexity
9. Add comprehensive logging (without secrets)
10. Improve test coverage (currently ~60%, target 80%)

### Low Priority (Backlog)
11. Modernize deprecated patterns in permissions.py
12. Extract duplicate password validation logic
13. Document security assumptions in each module

---

## Quality Assessment

| Module | Security Score | Quality Score | Overall | Issues |
|--------|----------------|---------------|---------|--------|
| auth.py | 6/10 | 8/10 | 7/10 | 1 critical, 2 medium |
| user_manager.py | 7/10 | 9/10 | 8/10 | 1 high, 1 medium |
| session.py | 5/10 | 7/10 | 6/10 | 1 critical, 3 medium |
| permissions.py | 8/10 | 6/10 | 7/10 | 0 critical, 4 medium |
| token_handler.py | 9/10 | 9/10 | 9/10 | 0 critical, 1 medium |
| oauth_provider.py | 8/10 | 8/10 | 8/10 | 0 critical, 2 medium |

**System Overall**: 7.1/10 (Good with critical issues to address)

---

## Appendix: Worker Contributions

- **Worker 1**: auth.py analysis (Quality: 98/100)
- **Worker 2**: user_manager.py analysis (Quality: 90/100)
- **Worker 3**: session.py analysis (Quality: 91/100)
- **Worker 4**: permissions.py analysis (Quality: 77/100, flagged for review)
- **Worker 5**: token_handler.py + oauth_provider.py analysis (Quality: 93/100, 88/100)

**Synthesis Strategy**: Aggregation (independent modules)
**Total Analysis Time**: 134 seconds
**Modules Analyzed**: 6
**Total Issues Identified**: 23 (3 critical, 7 high, 13 medium/low)
```

## Key Takeaways

1. **Parallelization Benefit**: 134s vs ~450s sequential (70% time savings)
2. **Strategy Selection**: Aggregation chosen automatically (independent tasks)
3. **Quality Control**: 1 worker flagged (permissions.py), others accepted
4. **Cross-Pattern Detection**: Synthesis identified system-wide patterns (input validation, RNG)
5. **Load Balancing**: Worker 5 handled 2 tasks (6 tasks, 5 workers)
6. **Actionable Output**: Prioritized recommendations with specific code changes

This example demonstrates how parallel independent analysis scales efficiently while maintaining high quality through multi-layer evaluation.
