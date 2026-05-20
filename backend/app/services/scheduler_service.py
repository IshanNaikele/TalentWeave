from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.recruitment import Job, Application, ExamAttempt, Candidate
from app.services.email_service import send_interview_email, send_assignment_email

scheduler = BackgroundScheduler()

# ─────────────────────────────────────────────
# REGISTRATION FUNCTIONS  (called from endpoints)
# ─────────────────────────────────────────────

def register_screening_deadline(job_id: int, run_at: datetime):
    """
    Arms a one-shot APScheduler job that fires process_screening_deadline
    at the exact moment the screening window closes.
    Called by POST /recruitment/jobs/create right after the job row is saved.
    """
    scheduler.add_job(
        func=process_screening_deadline,
        trigger="date",
        run_date=run_at,
        args=[job_id],
        id=f"screening_deadline_{job_id}",
        replace_existing=True
    )
    print(f"⏰ Screening deadline registered for job {job_id} at {run_at}")


def register_assignment_deadline(job_id: int, run_at: datetime):
    """
    Arms a one-shot APScheduler job that fires process_assignment_deadline
    when the assignment submission window closes.
    Called inside process_screening_deadline (assignment branch only).
    """
    scheduler.add_job(
        func=process_assignment_deadline,
        trigger="date",
        run_date=run_at,
        args=[job_id],
        id=f"assignment_deadline_{job_id}",
        replace_existing=True
    )
    print(f"⏰ Assignment deadline registered for job {job_id} at {run_at}")


# ─────────────────────────────────────────────
# DEADLINE HANDLERS  (run on background thread)
# ─────────────────────────────────────────────

def process_screening_deadline(job_id: int):
    """
    Fires when the screening window closes.

    1. Fetches all submitted exam attempts for this job.
    2. Filters passing candidates using filter_mode from the job config.
    3. Branches on include_assignment:
       - Assignment path  → emails PDF, flips job status to assignment_open,
                            arms assignment deadline clock.
       - Interview path   → assigns sequential time slots, sends calendar invite
                            email, flips job status to interviews_scheduled.

    IMPORTANT: Uses its own db session (SessionLocal directly) because this
    runs on a background thread, not inside a FastAPI request context.
    The get_db() dependency is request-scoped and cannot be used here.
    """
    print(f"\n🔔 Screening deadline fired for job {job_id}")
    db = SessionLocal()

    try:
        # ── 1. Load job config ──────────────────────────────────────────
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"❌ Job {job_id} not found in database — aborting.")
            return

        print(f"   Job: '{job.title}' | filter_mode={job.filter_mode} | "
              f"pass_threshold={job.pass_threshold} | "
              f"include_assignment={job.include_assignment}")

        # ── 2. Fetch all submitted exam attempts for this job ───────────
        # Join through Application to reach ExamAttempt
        attempts = (
            db.query(ExamAttempt)
            .join(Application, ExamAttempt.application_id == Application.id)
            .filter(Application.job_id == job_id)
            .filter(ExamAttempt.passed.isnot(None))   # only submitted attempts
            .all()
        )

        print(f"   Total submitted attempts: {len(attempts)}")

        if not attempts:
            print(f"   No candidates submitted for job {job_id}. Nothing to do.")
            job.status = "closed"
            db.commit()
            return

        # ── 3. Apply filter mode ────────────────────────────────────────
        passing_attempts = _filter_candidates(
            attempts=attempts,
            filter_mode=job.filter_mode,
            pass_threshold=job.pass_threshold,
            percentile_cutoff=job.percentile_cutoff
        )

        print(f"   Passing candidates after filter: {len(passing_attempts)}")

        if not passing_attempts:
            print(f"   No candidates passed for job {job_id}.")
            job.status = "closed"
            db.commit()
            return

        # ── 4. Branch on include_assignment ─────────────────────────────
        if job.include_assignment:
            _handle_assignment_branch(db, job, passing_attempts)
        else:
            _handle_interview_branch(db, job, passing_attempts)

        db.commit()
        print(f"✅ Screening deadline processing complete for job {job_id}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error in process_screening_deadline for job {job_id}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def process_assignment_deadline(job_id: int):
    """
    Fires when the assignment submission window closes.
    Updates job status so ops dashboard shows submissions are ready for review.
    Uses its own db session — same reason as process_screening_deadline.
    """
    print(f"\n🔔 Assignment deadline fired for job {job_id}")
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"❌ Job {job_id} not found — aborting.")
            return

        job.status = "assignment_closed"
        db.commit()
        print(f"✅ Job {job_id} status → assignment_closed. "
              f"Submissions ready for ops review.\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error in process_assignment_deadline for job {job_id}: {e}")

    finally:
        db.close()


# ─────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────

def _filter_candidates(
    attempts: list,
    filter_mode: str,
    pass_threshold: int,
    percentile_cutoff: float
) -> list:
    """
    Applies the configured filter mode to select passing candidates.

    fixed_threshold  — keeps everyone with score >= pass_threshold.
                       Straightforward cut-off.

    top_percentile   — keeps the top X% of scorers regardless of absolute score.
                       Useful when all candidates are strong and you want
                       to limit pipeline size.
    """
    if filter_mode == "fixed_threshold":
        return [a for a in attempts if a.score >= pass_threshold]

    elif filter_mode == "top_percentile":
        if not attempts:
            return []
        scores = sorted([a.score for a in attempts], reverse=True)
        # How many candidates to keep (minimum 1)
        cutoff_count = max(1, int(len(scores) * (percentile_cutoff / 100)))
        cutoff_score = scores[cutoff_count - 1]   # lowest score that still qualifies
        return [a for a in attempts if a.score >= cutoff_score]

    else:
        # Unknown filter mode — fall back to fixed_threshold with a safe default
        print(f"   ⚠️ Unknown filter_mode '{filter_mode}' — defaulting to fixed_threshold")
        return [a for a in attempts if a.score >= pass_threshold]


def _handle_assignment_branch(db, job: Job, passing_attempts: list):
    """
    Assignment path:
    - Flip job status to assignment_open so candidate portal accepts submissions.
    - Email each passing candidate their assignment PDF.
    - Arm the assignment deadline clock.
    """
    print(f"   → Assignment branch: emailing {len(passing_attempts)} candidates")

    job.status = "assignment_open"

    for attempt in passing_attempts:
        candidate = db.query(Candidate).filter(
            Candidate.id == attempt.candidate_id
        ).first()

        if not candidate:
            print(f"   ⚠️ Candidate {attempt.candidate_id} not found — skipping.")
            continue

        send_assignment_email(
            candidate_name=candidate.full_name,
            candidate_email=candidate.email,
            job_title=job.title,
            job_id=job.id,
            assignment_pdf_path=job.assignment_pdf_path or ""
        )

    # Arm assignment deadline clock
    # assignment_deadline was set when the job was created
    if job.assignment_deadline:
        register_assignment_deadline(
            job_id=job.id,
            run_at=job.assignment_deadline
        )
        print(f"   ⏰ Assignment deadline armed at {job.assignment_deadline}")
    else:
        print(f"   ⚠️ No assignment_deadline set for job {job.id} — "
              f"ops must close manually.")


def _handle_interview_branch(db, job: Job, passing_attempts: list):
    """
    Interview path (no assignment):
    - Assign sequential time slots starting tomorrow at 10:00 AM.
      Each slot is 30 minutes. Candidates get consecutive slots.
    - Generate a static placeholder Meet URL per candidate.
    - Send interview email with ICS calendar attachment.
    - Update application row with slot details.
    - Flip job status to interviews_scheduled.
    """
    print(f"   → Interview branch: scheduling {len(passing_attempts)} candidates")

    # Start slots from tomorrow at 10:00 AM
    tomorrow = datetime.utcnow().replace(
        hour=10, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)

    slot_duration_minutes = 30

    for index, attempt in enumerate(passing_attempts):
        candidate = db.query(Candidate).filter(
            Candidate.id == attempt.candidate_id
        ).first()

        if not candidate:
            print(f"   ⚠️ Candidate {attempt.candidate_id} not found — skipping.")
            continue

        # Sequential slot assignment — first candidate 10:00, next 10:30, etc.
        slot_start = tomorrow + timedelta(minutes=index * slot_duration_minutes)
        slot_end = slot_start + timedelta(minutes=slot_duration_minutes)

        # Static placeholder Meet URL — realistic for demo, no API needed
        meet_url = f"https://meet.google.com/talentweave-{job.id}-{candidate.id:03d}"

        # Update application with slot details
        application = db.query(Application).filter(
            Application.id == attempt.application_id
        ).first()

        if application:
            application.interview_slot_start = slot_start
            application.interview_slot_end = slot_end
            application.meet_url = meet_url
            application.status = "interview"

        # Send email with ICS calendar attachment
        send_interview_email(
            candidate_name=candidate.full_name,
            candidate_email=candidate.email,
            job_title=job.title,
            interview_slot_start=slot_start,
            interview_slot_end=slot_end,
            meet_url=meet_url
        )

    job.status = "interviews_scheduled"
    print(f"   ✅ Job {job.id} status → interviews_scheduled")