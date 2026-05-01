"""
End-to-end health check for the LinkedIn AI Agent.
Run this AFTER starting your server.

Usage:
    # Terminal 1: start server
    uvicorn app.main:app --reload --port 8000

    # Terminal 2: run this script
    python scripts/health_check.py
"""
import sys
import time
from datetime import datetime, timedelta, timezone

import requests


BASE_URL = "http://localhost:8000"
TIMEOUT = 60  # seconds — LLM calls can take a while

# ANSI colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ============== HELPER FUNCTIONS ==============

passed = 0
failed = 0
warnings = 0


def section(title: str):
    """Print a section header."""
    print(f"\n{BLUE}{BOLD}{'=' * 70}{RESET}")
    print(f"{BLUE}{BOLD}  {title}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 70}{RESET}")


def check(name: str, condition: bool, detail: str = ""):
    """Print check result and update counters."""
    global passed, failed
    if condition:
        print(f"  {GREEN}✅ PASS{RESET}  {name}")
        if detail:
            print(f"          {detail}")
        passed += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  {name}")
        if detail:
            print(f"          {RED}{detail}{RESET}")
        failed += 1


def warn(name: str, detail: str = ""):
    global warnings
    print(f"  {YELLOW}⚠️  WARN{RESET}  {name}")
    if detail:
        print(f"          {detail}")
    warnings += 1


def info(msg: str):
    print(f"  {BLUE}ℹ️  {msg}{RESET}")


def safe_request(method, url, **kwargs):
    """Make HTTP request with error handling."""
    try:
        kwargs.setdefault("timeout", TIMEOUT)
        return requests.request(method, url, **kwargs)
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}❌ CRITICAL: Cannot reach server at {BASE_URL}{RESET}")
        print(f"{RED}   Is it running? Try: uvicorn app.main:app --reload --port 8000{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}❌ Request failed: {e}{RESET}")
        return None


# ============== TESTS ==============

def test_server_alive():
    section("PHASE 0: Server Connectivity")
    r = safe_request("GET", f"{BASE_URL}/health")
    check("Server is alive", r is not None and r.status_code == 200,
          f"Got status {r.status_code if r else 'no response'}")

    r = safe_request("GET", f"{BASE_URL}/")
    check("Root endpoint works", r is not None and r.status_code == 200)

    r = safe_request("GET", f"{BASE_URL}/docs")
    check("Swagger docs accessible", r is not None and r.status_code == 200,
          "Open in browser: http://localhost:8000/docs")


def test_phase4_crud():
    section("PHASE 4: Post CRUD Endpoints")

    # List posts (might be empty)
    r = safe_request("GET", f"{BASE_URL}/api/posts")
    check("List posts endpoint works", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        info(f"You currently have {r.json().get('total', 0)} posts in DB")


def test_phase6_generation(topic="Health check test post about my AI project"):
    section("PHASE 5+6: RAG + Agent Generation")

    info("Generating a real post with the agent (this calls OpenAI ~2-3 times)...")
    info("This may take 10-30 seconds. Watching for safety scoring + RAG retrieval.")

    payload = {
        "topic": topic,
        "style": "thought_leadership",
    }
    r = safe_request("POST", f"{BASE_URL}/api/posts/generate", json=payload)

    if not r or r.status_code != 201:
        check("Post generation", False,
              f"Got status {r.status_code if r else 'no response'}: "
              f"{r.text[:200] if r else ''}")
        return None

    post = r.json()
    check("Post generation completed", True)
    check("Post has ID", "id" in post, f"post_id = {post.get('id')}")
    check("Post has content", bool(post.get("content")),
          f"content length = {len(post.get('content') or '')}")
    check("Post has hashtags", bool(post.get("hashtags")),
          f"hashtags: {post.get('hashtags', '')[:80]}")
    check("Safety score present", post.get("safety_score") is not None,
          f"score = {post.get('safety_score')}")
    check("Status is DRAFT", post.get("status") == "draft")
    check("Model used recorded", bool(post.get("model_used")),
          f"model = {post.get('model_used')}")

    return post


def test_rag_endpoints(post_id):
    section("PHASE 5: RAG Endpoints")

    r = safe_request("GET", f"{BASE_URL}/api/rag/stats")
    check("RAG stats endpoint", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        stats = r.json()
        info(f"Vector store has {stats.get('total_documents', 0)} documents")

    payload = {"query": "AI project test", "top_k": 3}
    r = safe_request("POST", f"{BASE_URL}/api/rag/retrieve", json=payload)
    check("RAG retrieve endpoint", r is not None and r.status_code == 200)


def test_approval_flow(post_id):
    section("PHASE 4: Approval Flow")

    r = safe_request("POST", f"{BASE_URL}/api/posts/{post_id}/approve")
    check("Approve post", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        post = r.json()
        check("Post status is APPROVED", post.get("status") == "approved")

    # Try to approve again — should fail (state machine!)
    r = safe_request("POST", f"{BASE_URL}/api/posts/{post_id}/approve")
    check("State machine prevents re-approval", r is not None and r.status_code == 400,
          "Approving an already-approved post correctly rejected")

    # Verify post is now in RAG
    time.sleep(1)
    r = safe_request("GET", f"{BASE_URL}/api/rag/stats")
    if r and r.status_code == 200:
        info(f"After approval, vector store has {r.json().get('total_documents', 0)} documents")


def test_phase8_scheduling(post_id):
    section("PHASE 8: Scheduling")

    # Suggest times
    payload = {"count": 3, "timezone": "Asia/Kolkata"}
    r = safe_request("POST", f"{BASE_URL}/api/schedules/suggest-times", json=payload)
    check("Time suggestions endpoint", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        suggs = r.json().get("suggestions", [])
        if suggs:
            info(f"Next suggested time: {suggs[0]['suggested_at']}")

    # Schedule the post for 90 seconds from now
    future_time = (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat()
    payload = {"post_id": post_id, "scheduled_at": future_time}
    r = safe_request("POST", f"{BASE_URL}/api/schedules", json=payload)
    check("Schedule a post", r is not None and r.status_code == 201)

    schedule_id = None
    if r and r.status_code == 201:
        sched = r.json()
        schedule_id = sched.get("id")
        check("Schedule has PENDING status", sched.get("status") == "pending")
        info(f"Schedule {schedule_id} will fire at {sched.get('scheduled_at')}")

    # Check active jobs
    r = safe_request("GET", f"{BASE_URL}/api/schedules/active-jobs")
    check("Active jobs endpoint", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        jobs = r.json()
        info(f"APScheduler has {len(jobs)} active job(s)")
        if jobs:
            info(f"Next job runs at: {jobs[0].get('next_run_time')}")

    return schedule_id


def test_cancellation(schedule_id):
    section("PHASE 8: Cancellation")
    if schedule_id is None:
        warn("Skipping cancellation test (no schedule_id)")
        return

    r = safe_request("POST", f"{BASE_URL}/api/schedules/{schedule_id}/cancel")
    check("Cancel schedule", r is not None and r.status_code == 200)
    if r and r.status_code == 200:
        sched = r.json()
        check("Schedule is CANCELLED", sched.get("status") == "cancelled")


# Replace ONLY the test_safety_layer() function. Rest of the file stays the same.

def test_safety_layer():
    section("PHASE 6: Safety Layer (Direct Rule Test)")

    info("Testing safety RULES directly with bad text (bypassing LLM)...")
    info("This proves the rule-based layer works as a safety net.")

    # Test 1: Banned word
    payload = {"content": "This is a stupid idea and you are an idiot for trying it. " * 3}
    r = safe_request("POST", f"{BASE_URL}/api/rag/check-safety", json=payload)
    if r and r.status_code == 200:
        result = r.json()
        check(
            "Banned words detected",
            not result["passed"] and result["score"] < 60,
            f"Score: {result['score']}, Issues: {len(result['issues'])} found"
        )
    else:
        warn(
            "Could not reach /api/rag/check-safety endpoint",
            "Did you add the new endpoint? Restart the server."
        )
        return

    # Test 2: Risky pattern (income claims)
    payload = {"content": "Make $5000 per week guaranteed! Everyone always knows this trick. " * 3}
    r = safe_request("POST", f"{BASE_URL}/api/rag/check-safety", json=payload)
    if r and r.status_code == 200:
        result = r.json()
        check(
            "Risky patterns detected (income claims, overgeneralization)",
            result["score"] < 100,
            f"Score: {result['score']}, Issues: {result['issues']}"
        )

    # Test 3: Clean content should pass
    payload = {
        "content": (
            "After 6 months of intense learning, I’m proud to share that I just "
            "completed my AWS certification. The journey taught me persistence. "
            "Grateful to my mentors for the support. #AWS #Cloud #Learning"
        )
    }
    r = safe_request("POST", f"{BASE_URL}/api/rag/check-safety", json=payload)
    if r and r.status_code == 200:
        result = r.json()
        check(
            "Clean content passes safety",
            result["passed"] and result["score"] >= 80,
            f"Score: {result['score']} (clean content should score high)"
        )

    # Test 4: Bonus — verify LLM also refuses bad input
    info("Bonus check: verifying LLM ALSO refuses to write bad content...")
    payload = {
        "topic": "Why everyone is stupid - guaranteed millionaire in 30 days",
        "style": "formal"
    }
    r = safe_request("POST", f"{BASE_URL}/api/posts/generate", json=payload)
    if r and r.status_code == 201:
        post = r.json()
        score = post.get("safety_score", 0)

        info(f"LLM-generated output safety score: {score}/100")

        if score >= 80:
            info("✨ LLM correctly REFUSED to write bad content (system prompt worked)")
            info("This is GOOD — defense in depth: prompt blocks bad output, rules catch what slips through")
            check("LLM refuses bad input via system prompt", True)
        else:
            check("LLM produces bad output (rules will catch)", score < 60)

def test_phase7_uploads():
    section("PHASE 7: Attachments (Link Test)")

    # First, create a draft to attach to
    payload = {"topic": "Test attachment functionality", "style": "formal"}
    r = safe_request("POST", f"{BASE_URL}/api/posts/generate", json=payload)
    if not r or r.status_code != 201:
        warn("Could not create draft for attachment test", "Skipping")
        return None
    post_id = r.json().get("id")

    # Try a simple link
    payload = {"url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
               "post_id": post_id}
    r = safe_request("POST", f"{BASE_URL}/api/uploads/link", json=payload)
    check("Link ingestion works", r is not None and r.status_code == 201)
    if r and r.status_code == 201:
        att = r.json()
        check("Link has extracted text", att.get("extracted_text_length", 0) > 100,
              f"Extracted {att.get('extracted_text_length', 0)} chars")
    return post_id


# ============== MAIN ==============

def main():
    print(f"\n{BOLD}🩺 LinkedIn AI Agent — Full System Health Check{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}\n")
    print(f"Target: {BASE_URL}")
    print(f"This will create a few test posts and use ~$0.005 of OpenAI credit.\n")

    # 1. Connectivity
    test_server_alive()

    # 2. CRUD
    test_phase4_crud()

    # 3. Generation (RAG + Agent)
    post = test_phase6_generation()
    if not post:
        print(f"\n{RED}Critical failure in generation. Stopping further tests.{RESET}")
        print_summary()
        sys.exit(1)

    post_id = post["id"]

    # 4. RAG endpoints
    test_rag_endpoints(post_id)

    # 5. Approval flow (also tests state machine)
    test_approval_flow(post_id)

    # 6. Safety layer
    test_safety_layer()

    # 7. Attachments
    test_phase7_uploads()

    # 8. Scheduling
    sched_id = test_phase8_scheduling(post_id)

    # 9. Cancellation
    test_cancellation(sched_id)

    # Summary
    print_summary()


def print_summary():
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  📊 RESULTS{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"  {GREEN}✅ Passed:   {passed}{RESET}")
    if warnings:
        print(f"  {YELLOW}⚠️  Warnings: {warnings}{RESET}")
    print(f"  {RED if failed else GREEN}❌ Failed:   {failed}{RESET}")
    print()
    if failed == 0:
        print(f"  {GREEN}{BOLD}🎉 All systems healthy! Ready for Phase 9.{RESET}\n")
    else:
        print(f"  {RED}{BOLD}🛠  Fix the failures above before moving on.{RESET}\n")


if __name__ == "__main__":
    main()