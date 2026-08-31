"""Assessment generation and submission API."""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import (
    Learner, Skill, Assessment, AssessmentQuestion, LearnerSkill,
    AssessmentStatus
)
from app.schemas.schemas import (
    AssessmentGenerateRequest, AssessmentSubmitRequest, AssessmentResponse,
    AssessmentQuestionResponse, SkillResponse
)
from app.ai.provider import get_provider

router = APIRouter(prefix="/api/assessments", tags=["assessments"])
logger = logging.getLogger(__name__)

# Fallback question bank for major tech skills
FALLBACK_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "sql": [
        {
            "question_text": "Which SQL clause is used to filter groups created by the GROUP BY clause?",
            "options": ["WHERE", "HAVING", "ORDER BY", "FILTER"],
            "correct": "B",
            "explanation": "HAVING filters groups of rows after aggregation, whereas WHERE filters individual rows before aggregation.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What is the difference between UNION and UNION ALL in SQL?",
            "options": ["UNION ALL removes duplicate records; UNION keeps all rows", "UNION removes duplicate records; UNION ALL retains all rows including duplicates", "UNION is only for numerical columns", "There is no difference in execution"],
            "correct": "B",
            "explanation": "UNION performs an internal deduplication step, whereas UNION ALL combines result sets directly with higher performance.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "Which type of SQL JOIN returns all rows from the left table and matching rows from the right table?",
            "options": ["INNER JOIN", "FULL OUTER JOIN", "LEFT JOIN (LEFT OUTER JOIN)", "CROSS JOIN"],
            "correct": "C",
            "explanation": "LEFT JOIN returns all rows from the left table, with NULLs in columns of the right table when no match is found.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What does a B-Tree index optimize most effectively in a relational database?",
            "options": ["Full table text scans", "Exact match lookups (=) and range queries (<, >, BETWEEN)", "Random memory allocation", "Unindexed JOIN operations"],
            "correct": "B",
            "explanation": "B-Tree indexes maintain sorted order, allowing logarithmic O(log N) lookups for equality and continuous range scans.",
            "difficulty": "HARD"
        },
        {
            "question_text": "Which property in ACID ensures database transactions are either completely executed or completely rolled back?",
            "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
            "correct": "A",
            "explanation": "Atomicity enforces the 'all-or-nothing' rule for transaction operations.",
            "difficulty": "EASY"
        }
    ],

    "relational modeling": [
        {
            "question_text": "What is the primary purpose of a Foreign Key in relational database design?",
            "options": ["To encrypt sensitive table data", "To enforce referential integrity between related tables", "To automatically calculate table row counts", "To store JSON payloads"],
            "correct": "B",
            "explanation": "A foreign key matches the primary key of another table, ensuring references between records remain valid and consistent.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What characterizes a relation in Third Normal Form (3NF)?",
            "options": ["It is in 2NF and contains no transitive functional dependencies", "It has only one column per table", "It contains nested arrays", "It has no primary key"],
            "correct": "A",
            "explanation": "3NF requires a table to be in 2NF and ensure all non-key attributes depend only on the primary key, with no transitive dependencies.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "Which cardinality describes the relationship where an author writes multiple books, and a book can have multiple authors?",
            "options": ["One-to-One (1:1)", "One-to-Many (1:N)", "Many-to-Many (M:N)", "Zero-to-One"],
            "correct": "C",
            "explanation": "Many-to-Many (M:N) relationships model entities where instances on both sides relate to multiple instances on the other, typically resolved via a junction table.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What is a surrogate key?",
            "options": ["A key composed of natural business data", "An artificial unique identifier (like an auto-incrementing integer or UUID)", "A foreign key with no matching primary key", "A temporary table lock"],
            "correct": "B",
            "explanation": "A surrogate key is an artificial unique identifier generated solely for primary key purposes rather than derived from business attributes.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What issue does normalization primarily aim to prevent in database design?",
            "options": ["Network latency", "Data redundancy and modification anomalies (insert, update, delete)", "Syntax compilation errors", "Database disk encryption"],
            "correct": "B",
            "explanation": "Normalization organizes fields and table structures to eliminate duplicate data and avoid anomalies during CRUD operations.",
            "difficulty": "EASY"
        }
    ],

    "react": [
        {
            "question_text": "What is the primary purpose of the useEffect hook in React?",
            "options": ["To create global CSS styles", "To handle side effects such as data fetching, subscriptions, and DOM mutations", "To replace all JavaScript loops", "To render raw HTML directly"],
            "correct": "B",
            "explanation": "useEffect lets functional components run side-effect operations after rendering when specified dependencies change.",
            "difficulty": "EASY"
        },
        {
            "question_text": "Why should you never mutate state directly in React (e.g. state.count = 5)?",
            "options": ["It causes a JavaScript syntax error", "React will not trigger a re-render because it relies on shallow object equality", "It slows down CPU clock speeds", "React deletes mutated objects"],
            "correct": "B",
            "explanation": "React checks object references for state changes; mutating directly prevents re-renders and breaks component synchronization.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What does React's virtual DOM accomplish?",
            "options": ["It compiles JavaScript into native C++ code", "It calculates minimal DOM diffs in memory before committing changes to the real browser DOM", "It replaces the browser's rendering engine", "It stores state in browser cookies"],
            "correct": "B",
            "explanation": "The virtual DOM reconciles UI changes efficiently in memory (diffing) before updating only changed real DOM nodes.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "When should you pass an empty dependency array `[]` to `useEffect`?",
            "options": ["When the effect should run on every single render", "When the effect should run only once when the component mounts and cleanup on unmount", "When you want to disable the component", "When using TypeScript"],
            "correct": "B",
            "explanation": "An empty dependency array tells React the effect does not depend on any props or state, running only upon initial mount.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What is the benefit of React.memo or useMemo?",
            "options": ["It enables multi-threading", "It memoizes render output or computed values to avoid unnecessary re-calculations", "It caches server HTTP requests permanently", "It validates PropTypes"],
            "correct": "B",
            "explanation": "Memoization skips redundant rendering or heavy computations when input props or dependencies have not changed.",
            "difficulty": "MEDIUM"
        }
    ],

    "python": [
        {
            "question_text": "What is the difference between a list and a tuple in Python?",
            "options": ["Lists are immutable; tuples are mutable", "Lists are mutable; tuples are immutable", "Tuples cannot store integers", "Lists cannot be iterated over"],
            "correct": "B",
            "explanation": "Lists can be modified (mutable) after creation, whereas tuples cannot be altered once defined (immutable).",
            "difficulty": "EASY"
        },
        {
            "question_text": "What does a generator function in Python use to return values iteratively without holding the entire sequence in memory?",
            "options": ["return", "yield", "emit", "async"],
            "correct": "B",
            "explanation": "yield pauses function state and produces a value lazily on demand, making memory usage O(1) regardless of sequence size.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is the purpose of Python's GIL (Global Interpreter Lock)?",
            "options": ["To encrypt bytecode", "To ensure thread-safety in CPython by allowing only one native thread to execute Python bytecode at a time", "To speed up matrix multiplication", "To manage virtual environments"],
            "correct": "B",
            "explanation": "The GIL is a mutex in CPython that prevents multi-threaded CPU execution from corrupting internal memory management.",
            "difficulty": "HARD"
        },
        {
            "question_text": "Which built-in Python data structure offers O(1) average time complexity for key lookups?",
            "options": ["list", "tuple", "dict (and set)", "deque"],
            "correct": "C",
            "explanation": "Dictionaries and sets in Python use hash tables, providing O(1) average lookup, insertion, and deletion time.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What is a decorator in Python?",
            "options": ["A graphical UI library", "A function that takes another function as an argument and extends its behavior without modifying its source code", "A CSS processor", "A garbage collector hook"],
            "correct": "B",
            "explanation": "Decorators wrap functions using the `@decorator` syntax to inject reusable behavior such as logging, authentication, or timing.",
            "difficulty": "MEDIUM"
        }
    ],

    "default": [
        {
            "question_text": "What is the primary benefit of modular software architecture?",
            "options": ["Faster compile times only", "High cohesion, loose coupling, and easier testability & maintenance", "Eliminates the need for databases", "Reduces required RAM to zero"],
            "correct": "B",
            "explanation": "Modularity separates concerns into distinct components, making software significantly easier to test, extend, and maintain.",
            "difficulty": "EASY"
        },
        {
            "question_text": "Which design pattern is best suited when an object needs to notify multiple other objects of state changes?",
            "options": ["Observer Pattern", "Singleton Pattern", "Factory Pattern", "Adapter Pattern"],
            "correct": "A",
            "explanation": "The Observer pattern defines a one-to-many dependency where subjects notify observers automatically of state changes.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What does asynchronous execution achieve in modern application programming?",
            "options": ["Locks the CPU until all tasks complete", "Allows I/O-bound tasks to execute concurrently without blocking the main event loop", "Compiles code to machine assembly", "Doubles processor speed"],
            "correct": "B",
            "explanation": "Asynchronous code yields execution during network or disk I/O, allowing other requests to be processed concurrently.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is the core principle behind Test-Driven Development (TDD)?",
            "options": ["Write code first, write tests before production release", "Write failing automated tests first, write minimal code to pass, then refactor", "Only test frontend components manually", "Test only performance metrics"],
            "correct": "B",
            "explanation": "TDD follows the Red-Green-Refactor cycle: write a failing test, implement the minimal solution, then clean up the code.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is the main role of continuous integration (CI) in software development?",
            "options": ["Automatically merging, building, and running automated tests on code changes", "Selling software licenses automatically", "Deploying only once a year", "Writing code using AI"],
            "correct": "A",
            "explanation": "CI automatically verifies that each commit builds and passes test suites, catching regressions early in the lifecycle.",
            "difficulty": "EASY"
        }
    ]
}


@router.post("/generate", status_code=201)
async def generate_assessment(
    request: AssessmentGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate an assessment for a specific skill."""
    result = await db.execute(select(Learner).where(Learner.id == request.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    result = await db.execute(select(Skill).where(Skill.id == request.skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Generate questions using AI or domain fallback
    questions_data = await _generate_questions(skill, request.num_questions)

    assessment = Assessment(
        learner_id=request.learner_id,
        skill_id=request.skill_id,
        title=f"{skill.name} Skill Assessment",
        description=f"Test your {skill.name} knowledge with {len(questions_data)} practical questions",
        total_questions=len(questions_data),
        status=AssessmentStatus.IN_PROGRESS,
    )
    db.add(assessment)
    await db.flush()

    for i, q_data in enumerate(questions_data):
        q = AssessmentQuestion(
            assessment_id=assessment.id,
            question_number=i + 1,
            question_text=q_data["question_text"],
            options=json.dumps(q_data["options"]),
            correct_answer=q_data["correct"],
            explanation=q_data["explanation"],
            difficulty=q_data.get("difficulty", "MEDIUM"),
        )
        db.add(q)

    await db.commit()
    await db.refresh(assessment)

    return await _format_assessment(assessment, skill, db)


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    skill = None
    if assessment.skill_id:
        s = await db.execute(select(Skill).where(Skill.id == assessment.skill_id))
        skill = s.scalar_one_or_none()
    return await _format_assessment(assessment, skill, db)


@router.get("/learner/{learner_id}")
async def list_learner_assessments(learner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assessment).where(Assessment.learner_id == learner_id)
        .order_by(Assessment.started_at.desc())
    )
    assessments = result.scalars().all()
    output = []
    for a in assessments:
        skill = None
        if a.skill_id:
            sr = await db.execute(select(Skill).where(Skill.id == a.skill_id))
            skill = sr.scalar_one_or_none()
        output.append(await _format_assessment(a, skill, db))
    return output


@router.post("/{assessment_id}/submit")
async def submit_assessment(
    assessment_id: int,
    request: AssessmentSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit assessment answers and calculate results."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Load questions
    q_result = await db.execute(
        select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment_id)
    )
    questions = q_result.scalars().all()

    correct = 0
    for q in questions:
        answer = request.answers.get(q.id) or request.answers.get(str(q.id))
        q.learner_answer = answer
        q.is_correct = answer == q.correct_answer
        if q.is_correct:
            correct += 1
        db.add(q)

    score_pct = (correct / max(1, len(questions))) * 100
    proficiency = (score_pct / 100) * 5

    assessment.correct_answers = correct
    assessment.score_percentage = score_pct
    assessment.estimated_proficiency = round(proficiency, 2)
    assessment.status = AssessmentStatus.COMPLETED
    assessment.completed_at = datetime.utcnow()
    db.add(assessment)

    # Update learner skill proficiency based on assessment
    if assessment.skill_id and assessment.learner_id:
        ls_result = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.learner_id == assessment.learner_id,
                LearnerSkill.skill_id == assessment.skill_id
            )
        )
        ls = ls_result.scalar_one_or_none()
        if ls:
            old_prof = ls.current_proficiency
            ls.current_proficiency = round((old_prof * 0.3 + proficiency * 0.7), 1)
            ls.gap_score = max(0.0, ls.target_proficiency - ls.current_proficiency) / max(1, ls.target_proficiency)
            ls.confidence = 0.95
            db.add(ls)

    await db.commit()

    if score_pct >= 80:
        msg = f"Excellent! Score: {score_pct:.0f}%. You have demonstrated strong mastery in this topic."
    elif score_pct >= 60:
        msg = f"Good job! Score: {score_pct:.0f}%. Continue with practical exercises in your roadmap."
    else:
        msg = f"Score: {score_pct:.0f}%. Review the foundational tutorials in this phase before retrying."

    return {
        "assessment_id": assessment_id,
        "score_percentage": score_pct,
        "correct_answers": correct,
        "total_questions": len(questions),
        "estimated_proficiency": proficiency,
        "adaptation_message": msg,
    }


async def get_assessment_by_skill(learner_id: int, skill_id: int, db: AsyncSession):
    result = await db.execute(
        select(Assessment).where(
            Assessment.learner_id == learner_id,
            Assessment.skill_id == skill_id,
        ).order_by(Assessment.started_at.desc()).limit(1)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    sr = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = sr.scalar_one_or_none()
    return await _format_assessment(assessment, skill, db)


async def _format_assessment(assessment: Assessment, skill, db: AsyncSession) -> dict:
    q_result = await db.execute(
        select(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment.id)
        .order_by(AssessmentQuestion.question_number)
    )
    questions = q_result.scalars().all()

    skill_resp = None
    if skill:
        skill_resp = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "domain": skill.domain,
        }

    return {
        "id": assessment.id,
        "skill": skill_resp,
        "title": assessment.title,
        "description": assessment.description,
        "total_questions": assessment.total_questions,
        "correct_answers": assessment.correct_answers,
        "score_percentage": assessment.score_percentage,
        "estimated_proficiency": assessment.estimated_proficiency,
        "status": assessment.status,
        "started_at": assessment.started_at,
        "completed_at": assessment.completed_at,
        "questions": [
            {
                "id": q.id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "options": json.loads(q.options) if q.options else [],
                "correct_answer": q.correct_answer if assessment.status == AssessmentStatus.COMPLETED else None,
                "learner_answer": q.learner_answer,
                "is_correct": q.is_correct,
                "explanation": q.explanation if assessment.status == AssessmentStatus.COMPLETED else None,
                "difficulty": q.difficulty,
            }
            for q in questions
        ],
    }


async def _generate_questions(skill: Skill, num_questions: int) -> list:
    """Generate assessment questions using AI or smart domain fallback."""
    provider = get_provider()
    if provider.is_available():
        try:
            prompt = f"""Generate {num_questions} multiple-choice assessment questions for the skill: "{skill.name}"
Description: {skill.description or 'Technical competency evaluation'}

Return ONLY a valid JSON array with objects:
[
  {{
    "question_text": "Clear technical question testing understanding of {skill.name}",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": "A",
    "explanation": "Why option A is the correct answer and how it applies in practice",
    "difficulty": "MEDIUM"
  }}
]
Rules:
- correct must be one of "A", "B", "C", "D"
- difficulty must be "EASY", "MEDIUM", or "HARD"
- Questions must test real practical understanding of {skill.name}
- Return ONLY the JSON array without markdown formatting"""
            data = await provider.generate_json(prompt)
            if isinstance(data, list) and len(data) > 0:
                return data[:num_questions]
        except Exception as e:
            logger.warning(f"AI question generation failed: {e}")

    # Check seeded assessment questions
    from app.seed.seed_data import ASSESSMENT_QUESTIONS
    if skill.name in ASSESSMENT_QUESTIONS:
        return ASSESSMENT_QUESTIONS[skill.name][:num_questions]

    # Check fallback domain questions
    skill_lower = skill.name.lower()
    for key, q_list in FALLBACK_QUESTIONS.items():
        if key in skill_lower or any(part in skill_lower for part in key.split()):
            return q_list[:num_questions]

    # Synthesize topic-specific questions for any novel skill
    return _synthesize_topic_questions(skill.name, num_questions)


def _synthesize_topic_questions(skill_name: str, num_questions: int) -> list:
    """Dynamically synthesize realistic conceptual questions for any novel skill name."""
    return [
        {
            "question_text": f"What is the core architectural principle behind {skill_name} in modern applications?",
            "options": [
                f"Separation of concerns and modular encapsulation tailored for {skill_name}",
                "Executing all computation on a single thread without memory management",
                "Converting all data structures into flat text files",
                "Disabling network security protocols for raw performance"
            ],
            "correct": "A",
            "explanation": f"Mastery in {skill_name} requires understanding separation of concerns, modular design, and robust state management.",
            "difficulty": "EASY"
        },
        {
            "question_text": f"Which of the following is considered an industry best practice when working with {skill_name}?",
            "options": [
                "Hardcoding configuration credentials directly into codebase",
                f"Applying proper error handling, input validation, and testing standards across {skill_name} components",
                "Avoiding version control to deploy faster",
                "Ignoring performance bottlenecks during development"
            ],
            "correct": "B",
            "explanation": f"Production-grade {skill_name} workflows emphasize structured error handling, clean validation, and automated verification.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": f"When scaling systems that utilize {skill_name}, what strategy provides the highest reliability?",
            "options": [
                "Restarting server processes on every user request",
                f"Implementing efficient indexing, caching, and horizontal decoupling for {skill_name} workflows",
                "Removing database constraints to save CPU cycles",
                "Executing long-running blocking tasks on the UI thread"
            ],
            "correct": "B",
            "explanation": f"Scalability in {skill_name} involves optimizing bottleneck paths with caching, indexing, and asynchronous decoupling.",
            "difficulty": "HARD"
        },
        {
            "question_text": f"What is the most effective approach for testing components in {skill_name}?",
            "options": [
                "Testing only after production deployment failure",
                f"Automated unit testing with Mock/Stub dependencies combined with integration test suites for {skill_name}",
                "Deleting test files to reduce bundle size",
                "Testing solely through browser console prints"
            ],
            "correct": "B",
            "explanation": f"Reliable {skill_name} codebases leverage test-driven principles with isolated unit tests and end-to-end integration checks.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": f"What security consideration is paramount when implementing {skill_name} in production?",
            "options": [
                "Trusting all raw client-provided inputs without sanitization",
                f"Applying the principle of least privilege, input sanitization, and secure credential management in {skill_name}",
                "Disabling CORS and HTTPS to minimize overhead",
                "Storing unhashed passwords in plaintext tables"
            ],
            "correct": "B",
            "explanation": f"Security standards for {skill_name} dictate strict input sanitization, encrypted communications, and least privilege access.",
            "difficulty": "MEDIUM"
        }
    ][:num_questions]
