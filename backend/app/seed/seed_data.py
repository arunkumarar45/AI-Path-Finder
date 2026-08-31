"""
Realistic seed data for the AI Learning Path Recommender.
Creates skills, resources, and the demo learner (Alex).
"""

import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    Learner, Skill, LearnerSkill, Resource, Roadmap, RoadmapItem,
    Assessment, AssessmentQuestion, ChatMessage, Feedback,
    ExperienceLevel, LearningStyle, SkillCategory, SkillPriority, SkillStatus,
    ResourceType, ResourceDifficulty, ItemType, ItemStatus,
    RoadmapStatus, ScheduleStatus, AssessmentStatus, FeedbackType, MessageRole
)

logger = logging.getLogger(__name__)


SKILLS_DATA = [
    # Java Ecosystem
    {"name": "Core Java", "category": SkillCategory.PROGRAMMING_LANGUAGE, "domain": "Backend", "prerequisites": "", "difficulty_level": 2, "description": "Java fundamentals: syntax, OOP, collections, streams, generics, exceptions"},
    {"name": "OOP", "category": SkillCategory.CONCEPT, "domain": "Backend", "prerequisites": "Core Java", "difficulty_level": 2, "description": "Object-oriented programming: encapsulation, inheritance, polymorphism, abstraction"},
    {"name": "Spring Boot", "category": SkillCategory.FRAMEWORK, "domain": "Backend", "prerequisites": "Core Java,OOP", "difficulty_level": 3, "description": "Spring Boot auto-configuration, dependency injection, Spring MVC, application structure"},
    {"name": "REST APIs", "category": SkillCategory.CONCEPT, "domain": "Backend", "prerequisites": "Spring Boot", "difficulty_level": 3, "description": "RESTful design, HTTP methods, status codes, request/response, OpenAPI"},
    {"name": "JPA/Hibernate", "category": SkillCategory.FRAMEWORK, "domain": "Backend", "prerequisites": "SQL,Spring Boot", "difficulty_level": 3, "description": "ORM mapping, entity relationships, JPQL, repositories, transactions"},
    {"name": "Spring Security", "category": SkillCategory.SECURITY, "domain": "Backend", "prerequisites": "Spring Boot,REST APIs", "difficulty_level": 4, "description": "Authentication, authorization, JWT, security configurations, CSRF protection"},
    {"name": "Testing", "category": SkillCategory.TESTING, "domain": "Backend", "prerequisites": "Core Java,Spring Boot", "difficulty_level": 3, "description": "Unit testing with JUnit/Mockito, integration testing, TDD, MockMvc"},
    {"name": "Maven/Gradle", "category": SkillCategory.TOOL, "domain": "Backend", "prerequisites": "Core Java", "difficulty_level": 2, "description": "Build tools, dependency management, lifecycle, profiles"},
    {"name": "Microservices", "category": SkillCategory.ARCHITECTURE, "domain": "Backend", "prerequisites": "Spring Boot,Docker,REST APIs", "difficulty_level": 4, "description": "Microservice patterns, service discovery, API gateway, distributed systems"},
    # Data / DBMS
    {"name": "SQL", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "", "difficulty_level": 2, "description": "SQL fundamentals, CRUD, JOINs, indexes, transactions, query optimization"},
    {"name": "Relational Modeling", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL", "difficulty_level": 2, "description": "Relational schema design, entity relationships, constraints, foreign keys"},
    {"name": "DDL & DML Queries", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL", "difficulty_level": 2, "description": "Table creation, data manipulation, filtering, sorting, aggregate functions"},
    {"name": "Advanced Joins & Subqueries", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL,DDL & DML Queries", "difficulty_level": 3, "description": "Multi-table joins, subqueries, CTEs, window functions"},
    {"name": "Indexing & Optimization", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL", "difficulty_level": 4, "description": "B-Tree indexes, EXPLAIN ANALYZE, query execution plans, performance tuning"},
    {"name": "Transactions & ACID", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL", "difficulty_level": 3, "description": "Transaction control, commit/rollback, isolation levels, concurrency"},
    {"name": "Database Normalization", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "Relational Modeling", "difficulty_level": 3, "description": "1NF, 2NF, 3NF, BCNF, functional dependencies"},
    {"name": "PostgreSQL", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "SQL", "difficulty_level": 3, "description": "PostgreSQL-specific features, psql, indexing strategies, performance"},
    {"name": "Redis", "category": SkillCategory.DATABASE, "domain": "Data", "prerequisites": "Spring Boot", "difficulty_level": 3, "description": "In-memory data structures, caching patterns, pub/sub"},
    # DevOps
    {"name": "Docker", "category": SkillCategory.DEVOPS, "domain": "DevOps", "prerequisites": "", "difficulty_level": 3, "description": "Containers, Dockerfile, docker-compose, image management"},
    {"name": "Git", "category": SkillCategory.TOOL, "domain": "General", "prerequisites": "", "difficulty_level": 1, "description": "Version control, branching, merging, pull requests, rebase"},
    {"name": "CI/CD", "category": SkillCategory.DEVOPS, "domain": "DevOps", "prerequisites": "Git,Docker", "difficulty_level": 3, "description": "Continuous integration and deployment pipelines, GitHub Actions"},
    {"name": "Kubernetes", "category": SkillCategory.DEVOPS, "domain": "DevOps", "prerequisites": "Docker,CI/CD", "difficulty_level": 4, "description": "Container orchestration, pods, services, deployments"},
    # Frontend / Fullstack
    {"name": "JavaScript", "category": SkillCategory.PROGRAMMING_LANGUAGE, "domain": "Frontend", "prerequisites": "", "difficulty_level": 2, "description": "JavaScript ES6+, async/await, DOM, fetch API"},
    {"name": "TypeScript", "category": SkillCategory.PROGRAMMING_LANGUAGE, "domain": "Frontend", "prerequisites": "JavaScript", "difficulty_level": 3, "description": "TypeScript types, interfaces, generics, decorators"},
    {"name": "React", "category": SkillCategory.FRAMEWORK, "domain": "Frontend", "prerequisites": "JavaScript,HTML/CSS", "difficulty_level": 3, "description": "React components, hooks, state management, routing"},
    {"name": "HTML/CSS", "category": SkillCategory.CONCEPT, "domain": "Frontend", "prerequisites": "", "difficulty_level": 1, "description": "HTML5 semantics, CSS3, flexbox, grid, responsive design"},
    # Data Science / ML
    {"name": "Python", "category": SkillCategory.PROGRAMMING_LANGUAGE, "domain": "Data Science", "prerequisites": "", "difficulty_level": 2, "description": "Python fundamentals, OOP, built-in libraries, virtual environments"},
    {"name": "Machine Learning", "category": SkillCategory.CONCEPT, "domain": "Data Science", "prerequisites": "Python,Statistics", "difficulty_level": 4, "description": "Supervised and unsupervised learning, model evaluation, scikit-learn"},
    {"name": "Statistics", "category": SkillCategory.CONCEPT, "domain": "Data Science", "prerequisites": "", "difficulty_level": 3, "description": "Probability, distributions, hypothesis testing, regression"},
]


RESOURCES_DATA = [
    # Spring Boot
    {
        "title": "Spring Boot 3 & Spring Framework 6 — Master Class",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/spring-boot-and-spring-framework-tutorial-for-beginners/",
        "type": ResourceType.COURSE,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "Spring Boot,REST APIs,JPA/Hibernate",
        "prerequisite_skills": "Core Java,SQL",
        "estimated_hours": 25,
        "rating": 4.7,
        "popularity_score": 92,
        "is_free": False,
        "description": "Comprehensive Spring Boot course covering REST APIs, JPA, security and testing"
    },
    {
        "title": "Official Spring Boot Documentation",
        "provider": "Spring.io",
        "url": "https://docs.spring.io/spring-boot/docs/current/reference/html/",
        "type": ResourceType.DOCUMENTATION,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "Spring Boot",
        "prerequisite_skills": "Core Java",
        "estimated_hours": 10,
        "rating": 4.8,
        "popularity_score": 88,
        "is_free": True,
        "description": "Official Spring Boot reference documentation with Getting Started guides"
    },
    {
        "title": "Building REST APIs with Spring Boot",
        "provider": "Baeldung",
        "url": "https://www.baeldung.com/building-a-restful-web-service-with-spring-and-java-based-configuration",
        "type": ResourceType.TUTORIAL,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "REST APIs,Spring Boot",
        "prerequisite_skills": "Spring Boot",
        "estimated_hours": 3,
        "rating": 4.6,
        "popularity_score": 85,
        "is_free": True,
        "description": "Practical guide to building REST APIs with Spring Boot — free high-quality tutorial"
    },
    {
        "title": "Spring Security In Action",
        "provider": "Manning",
        "url": "https://www.manning.com/books/spring-security-in-action",
        "type": ResourceType.BOOK,
        "difficulty": ResourceDifficulty.ADVANCED,
        "skills_taught": "Spring Security",
        "prerequisite_skills": "Spring Boot,REST APIs",
        "estimated_hours": 20,
        "rating": 4.5,
        "popularity_score": 80,
        "is_free": False,
        "description": "The definitive book on Spring Security — authentication, authorization, JWT, OAuth2"
    },
    {
        "title": "Spring Data JPA with Hibernate",
        "provider": "Baeldung",
        "url": "https://www.baeldung.com/the-persistence-layer-with-spring-and-jpa",
        "type": ResourceType.TUTORIAL,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "JPA/Hibernate",
        "prerequisite_skills": "SQL,Spring Boot",
        "estimated_hours": 4,
        "rating": 4.6,
        "popularity_score": 83,
        "is_free": True,
        "description": "Complete guide to Spring Data JPA: entities, repositories, JPQL"
    },
    {
        "title": "Java Testing with JUnit 5 and Mockito",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/testing-spring-boot-beginner-to-guru/",
        "type": ResourceType.COURSE,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "Testing",
        "prerequisite_skills": "Core Java,Spring Boot",
        "estimated_hours": 12,
        "rating": 4.6,
        "popularity_score": 82,
        "is_free": False,
        "description": "Complete testing for Spring Boot: unit tests, integration tests, MockMvc"
    },
    # Java Core
    {
        "title": "Java Programming Masterclass (Java 21)",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/",
        "type": ResourceType.COURSE,
        "difficulty": ResourceDifficulty.BEGINNER,
        "skills_taught": "Core Java,OOP",
        "prerequisite_skills": "",
        "estimated_hours": 80,
        "rating": 4.7,
        "popularity_score": 95,
        "is_free": False,
        "description": "The most comprehensive Java course — from beginner to advanced Java 21"
    },
    {
        "title": "Java Collections & Streams — Full Tutorial",
        "provider": "YouTube - Amigoscode",
        "url": "https://www.youtube.com/watch?v=GdAon80-0KA",
        "type": ResourceType.VIDEO,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "Core Java",
        "prerequisite_skills": "Core Java",
        "estimated_hours": 3,
        "rating": 4.7,
        "popularity_score": 87,
        "is_free": True,
        "description": "Deep dive into Java Collections framework and Stream API"
    },
    # SQL
    {
        "title": "SQL for Beginners — Complete Course",
        "provider": "freeCodeCamp",
        "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
        "type": ResourceType.VIDEO,
        "difficulty": ResourceDifficulty.BEGINNER,
        "skills_taught": "SQL",
        "prerequisite_skills": "",
        "estimated_hours": 4,
        "rating": 4.8,
        "popularity_score": 91,
        "is_free": True,
        "description": "Free complete SQL course from freeCodeCamp on YouTube"
    },
    {
        "title": "PostgreSQL Tutorial",
        "provider": "PostgreSQL.org",
        "url": "https://www.postgresql.org/docs/current/tutorial.html",
        "type": ResourceType.DOCUMENTATION,
        "difficulty": ResourceDifficulty.INTERMEDIATE,
        "skills_taught": "PostgreSQL,SQL",
        "prerequisite_skills": "SQL",
        "estimated_hours": 5,
        "rating": 4.6,
        "popularity_score": 82,
        "is_free": True,
        "description": "Official PostgreSQL tutorial covering queries, transactions, and administration"
    },
    # Docker
    {
        "title": "Docker in Practice",
        "provider": "YouTube - TechWorld with Nana",
        "url": "https://www.youtube.com/watch?v=3c-iBn73dDE",
        "type": ResourceType.VIDEO,
        "difficulty": ResourceDifficulty.BEGINNER,
        "skills_taught": "Docker",
        "prerequisite_skills": "",
        "estimated_hours": 3,
        "rating": 4.8,
        "popularity_score": 90,
        "is_free": True,
        "description": "Complete Docker tutorial for beginners — containers, images, docker-compose"
    },
    # Maven
    {
        "title": "Apache Maven in 1 Hour",
        "provider": "YouTube",
        "url": "https://www.youtube.com/watch?v=KNGQ9JBQWhQ",
        "type": ResourceType.VIDEO,
        "difficulty": ResourceDifficulty.BEGINNER,
        "skills_taught": "Maven/Gradle",
        "prerequisite_skills": "Core Java",
        "estimated_hours": 1,
        "rating": 4.4,
        "popularity_score": 75,
        "is_free": True,
        "description": "Quick Maven tutorial covering POM, dependencies, and build lifecycle"
    },
    # Git
    {
        "title": "Git and GitHub for Beginners",
        "provider": "freeCodeCamp",
        "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
        "type": ResourceType.VIDEO,
        "difficulty": ResourceDifficulty.BEGINNER,
        "skills_taught": "Git",
        "prerequisite_skills": "",
        "estimated_hours": 1,
        "rating": 4.7,
        "popularity_score": 88,
        "is_free": True,
        "description": "Complete Git & GitHub tutorial from freeCodeCamp"
    },
]


ASSESSMENT_QUESTIONS = {
    "Core Java": [
        {
            "question_text": "What is the output of: List<Integer> list = Arrays.asList(1,2,3); list.stream().filter(x -> x > 1).mapToInt(x -> x).sum();",
            "options": ["3", "5", "6", "Compilation error"],
            "correct": "B",
            "explanation": "filter(x > 1) keeps [2,3], mapToInt converts to IntStream, sum() = 2+3 = 5",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "Which of these is NOT a feature of Java 8 streams?",
            "options": ["Lazy evaluation", "Parallel execution", "Mutable state operations", "Pipeline operations"],
            "correct": "C",
            "explanation": "Streams support functional-style operations. Streams are immutable — they do not modify the source.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is the difference between HashMap and ConcurrentHashMap?",
            "options": ["No difference", "ConcurrentHashMap is thread-safe", "HashMap allows null values, ConcurrentHashMap doesn't for keys", "Both B and C"],
            "correct": "D",
            "explanation": "ConcurrentHashMap is thread-safe (allows concurrent reads/writes). It also does not allow null keys or values, whereas HashMap does.",
            "difficulty": "HARD"
        },
        {
            "question_text": "What does the 'finally' block guarantee in Java?",
            "options": ["It runs only if no exception occurs", "It always runs after try/catch", "It only runs when System.exit() is called", "It replaces catch blocks"],
            "correct": "B",
            "explanation": "The 'finally' block always executes after try/catch, regardless of whether an exception occurred (except System.exit() or JVM crash).",
            "difficulty": "EASY"
        },
        {
            "question_text": "Which interface do lambda expressions implement in Java?",
            "options": ["Any interface", "Only Runnable", "Functional interfaces (single abstract method)", "Iterator interface"],
            "correct": "C",
            "explanation": "Lambda expressions implement functional interfaces — interfaces with exactly one abstract method (SAM). Examples: Runnable, Comparator, Predicate.",
            "difficulty": "MEDIUM"
        },
    ],
    "Spring Boot": [
        {
            "question_text": "What annotation enables auto-configuration in a Spring Boot application?",
            "options": ["@SpringBootApplication", "@EnableAutoConfiguration only", "@ComponentScan only", "@Configuration"],
            "correct": "A",
            "explanation": "@SpringBootApplication is a meta-annotation that includes @EnableAutoConfiguration, @ComponentScan, and @Configuration.",
            "difficulty": "EASY"
        },
        {
            "question_text": "In Spring Boot, what is the purpose of @RestController vs @Controller?",
            "options": ["They are identical", "@RestController adds @ResponseBody to all methods", "@Controller is for REST APIs only", "@RestController doesn't support views"],
            "correct": "B",
            "explanation": "@RestController = @Controller + @ResponseBody. It serializes responses directly to HTTP response body (typically JSON/XML) rather than returning a view name.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What does Spring Boot's auto-configuration use to make decisions?",
            "options": ["XML files only", "Classpath conditions, property values, and @Conditional annotations", "Only application.properties", "Database schema"],
            "correct": "B",
            "explanation": "Auto-configuration uses @Conditional annotations to conditionally configure beans based on classpath presence, properties, and other conditions.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is Spring IoC (Inversion of Control)?",
            "options": ["Objects create their own dependencies", "The Spring container manages object creation and dependency injection", "A design pattern for error handling", "A type of REST API pattern"],
            "correct": "B",
            "explanation": "IoC means control of object creation is inverted to the container. Instead of objects creating dependencies, the Spring container injects them.",
            "difficulty": "EASY"
        },
        {
            "question_text": "Which Spring Boot actuator endpoint shows application health status?",
            "options": ["/metrics", "/health", "/status", "/ping"],
            "correct": "B",
            "explanation": "/actuator/health is the standard Spring Boot Actuator endpoint for health checks. It reports UP/DOWN status and component health details.",
            "difficulty": "EASY"
        },
    ],
    "SQL": [
        {
            "question_text": "What is the difference between INNER JOIN and LEFT JOIN?",
            "options": ["No difference", "INNER JOIN returns only matching rows; LEFT JOIN returns all left rows plus matches", "LEFT JOIN is faster", "INNER JOIN returns all rows from both tables"],
            "correct": "B",
            "explanation": "INNER JOIN returns rows where both tables have matching keys. LEFT JOIN returns ALL rows from the left table, with NULL for unmatched right table columns.",
            "difficulty": "EASY"
        },
        {
            "question_text": "What does the GROUP BY clause do?",
            "options": ["Sorts the results", "Groups rows with the same values for aggregate functions", "Filters rows before grouping", "Joins two tables"],
            "correct": "B",
            "explanation": "GROUP BY groups rows with the same column values together, allowing aggregate functions (COUNT, SUM, AVG) to be applied to each group.",
            "difficulty": "EASY"
        },
        {
            "question_text": "Which index type is best for range queries (e.g., WHERE price BETWEEN 10 AND 50)?",
            "options": ["Hash index", "B-Tree index", "Bitmap index", "Full-text index"],
            "correct": "B",
            "explanation": "B-Tree indexes are optimal for range queries as they maintain sorted order. Hash indexes only support equality (=) comparisons.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is a SQL transaction ACID property? What does 'Atomicity' mean?",
            "options": ["Transactions can be split into parts", "Either all operations succeed or all fail (all-or-nothing)", "Transactions are fast", "Transactions can be run concurrently"],
            "correct": "B",
            "explanation": "Atomicity means a transaction is all-or-nothing. If any operation fails, the entire transaction is rolled back. No partial commits.",
            "difficulty": "MEDIUM"
        },
        {
            "question_text": "What is the purpose of the HAVING clause?",
            "options": ["Filter rows before grouping (same as WHERE)", "Filter groups after GROUP BY aggregation", "Join multiple tables", "Sort aggregated results"],
            "correct": "B",
            "explanation": "HAVING filters groups after GROUP BY, operating on aggregated values. WHERE filters rows before grouping. Use HAVING for conditions on aggregate functions (COUNT, SUM, etc.).",
            "difficulty": "MEDIUM"
        },
    ],
}


async def seed_database(db: AsyncSession) -> None:
    """Seed the database with skills, resources, and the demo learner."""

    # Check if already seeded
    result = await db.execute(select(Skill).limit(1))
    if result.scalar_one_or_none():
        logger.info("Database already seeded — skipping")
        return

    logger.info("Seeding database...")

    # ── 1. Seed Skills ──────────────────────────────────────────────────────

    skill_objects = {}
    for skill_data in SKILLS_DATA:
        skill = Skill(**skill_data)
        db.add(skill)
        skill_objects[skill_data["name"]] = skill

    await db.flush()

    # ── 2. Seed Resources ────────────────────────────────────────────────────

    resource_objects = []
    for res_data in RESOURCES_DATA:
        resource = Resource(**res_data)
        db.add(resource)
        resource_objects.append(resource)

    await db.flush()

    # ── 3. Create Demo Learner — Alex ────────────────────────────────────────

    alex = Learner(
        name="Alex Chen",
        email="alex.demo@learningpath.ai",
        career_goal="Backend Java Developer",
        goal_description="I want to become a backend Java developer in 4 months. I already know Core Java, OOP, and SQL. I can study 8 hours per week.",
        experience_level=ExperienceLevel.INTERMEDIATE,
        interests=json.dumps(["java", "spring boot", "REST APIs", "backend development", "databases"]),
        completed_courses=json.dumps(["Core Java Fundamentals", "SQL for Beginners"]),
        previous_projects=json.dumps(["Simple Java Calculator", "Student Management Console App"]),
        preferred_learning_style=LearningStyle.HANDS_ON,
        weekly_hours_available=8,
        target_timeline="4 months",
        preferred_content_types=json.dumps(["COURSE", "PROJECT", "TUTORIAL"]),
        overall_progress=28.5,
        total_hours_learned=12,
        current_streak=5,
        is_demo_user=True,
    )
    db.add(alex)
    await db.flush()

    # ── 4. Seed LearnerSkills for Alex ──────────────────────────────────────

    alex_skills = [
        # Strong skills
        ("Core Java", 3.5, 4.0, SkillPriority.CRITICAL, SkillStatus.IN_PROGRESS),
        ("OOP", 3.0, 3.0, SkillPriority.CRITICAL, SkillStatus.COMPLETED),
        ("SQL", 3.0, 3.0, SkillPriority.CRITICAL, SkillStatus.COMPLETED),
        ("Git", 2.5, 3.0, SkillPriority.RECOMMENDED, SkillStatus.IN_PROGRESS),
        # Gaps
        ("Spring Boot", 1.0, 4.0, SkillPriority.CRITICAL, SkillStatus.NOT_STARTED),
        ("REST APIs", 1.0, 4.0, SkillPriority.CRITICAL, SkillStatus.NOT_STARTED),
        ("JPA/Hibernate", 0.5, 3.0, SkillPriority.RECOMMENDED, SkillStatus.NOT_STARTED),
        ("Spring Security", 0.0, 3.0, SkillPriority.RECOMMENDED, SkillStatus.NOT_STARTED),
        ("Testing", 1.0, 3.0, SkillPriority.RECOMMENDED, SkillStatus.NOT_STARTED),
        ("Maven/Gradle", 1.5, 2.0, SkillPriority.RECOMMENDED, SkillStatus.IN_PROGRESS),
        ("Docker", 0.5, 2.0, SkillPriority.OPTIONAL, SkillStatus.NOT_STARTED),
        ("PostgreSQL", 2.0, 3.0, SkillPriority.RECOMMENDED, SkillStatus.IN_PROGRESS),
    ]

    for skill_name, current, target, priority, status in alex_skills:
        skill = skill_objects.get(skill_name)
        if skill:
            gap = max(0.0, target - current) / target if target > 0 else 0.0
            ls = LearnerSkill(
                learner_id=alex.id,
                skill_id=skill.id,
                current_proficiency=current,
                target_proficiency=target,
                gap_score=round(gap, 3),
                priority=priority,
                status=status,
                confidence=0.85,
            )
            db.add(ls)

    await db.flush()

    # ── 5. Create Personalized Roadmap for Alex ──────────────────────────────

    roadmap = Roadmap(
        learner_id=alex.id,
        title="Personalized Roadmap: Backend Java Developer",
        description="Your personalized 4-month journey to becoming a Backend Java Developer. Built around your existing Java & SQL skills.",
        total_phases=4,
        current_phase=1,
        total_items=12,
        completed_items=3,
        completion_percentage=28.5,
        status=RoadmapStatus.ACTIVE,
        estimated_completion_date="December 2026",
        schedule_status=ScheduleStatus.ON_TRACK,
        ai_reasoning=(
            "Based on your strong Core Java and SQL background, this roadmap skips basic Java foundations "
            "and focuses on Spring Boot and REST APIs as the highest-priority gaps. "
            "Spring Security and Testing are sequenced after Spring Boot mastery. "
            "Docker is placed last as it's optional for your 4-month timeline."
        ),
    )
    db.add(roadmap)
    await db.flush()

    # Find resources for matching
    spring_resource = next((r for r in resource_objects if "Spring Boot 3" in r.title), None)
    rest_resource = next((r for r in resource_objects if "REST APIs with Spring" in r.title), None)
    jpa_resource = next((r for r in resource_objects if "JPA" in r.title), None)
    security_resource = next((r for r in resource_objects if "Spring Security In Action" in r.title), None)
    testing_resource = next((r for r in resource_objects if "Testing Spring Boot" in r.title), None)
    docker_resource = next((r for r in resource_objects if "Docker in Practice" in r.title), None)
    maven_resource = next((r for r in resource_objects if "Maven" in r.title), None)
    java_streams_resource = next((r for r in resource_objects if "Collections & Streams" in r.title), None)
    sql_resource = next((r for r in resource_objects if "SQL for Beginners" in r.title), None)

    roadmap_items_data = [
        # Phase 1 — Java Mastery (partially done)
        {
            "phase_number": 1, "phase_name": "Java Foundation", "order_index": 0,
            "title": "Advanced Java: Collections & Streams",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 3, "skills_gained": "Core Java",
            "desc": "Master Java Streams, Collections, and functional programming patterns",
            "why": "You know basic Java but Streams and Collections are essential for Spring Boot. This closes your remaining Core Java gap.",
            "status": ItemStatus.COMPLETED,
            "resource": java_streams_resource,
            "scoring": {"goal_match": 0.85, "skill_gap_match": 0.62, "prerequisite_match": 1.0, "difficulty_match": 0.9, "preference_match": 0.8, "time_match": 0.9, "progress_match": 0.8, "feedback_adjustment": 0.5, "total_score": 0.82}
        },
        {
            "phase_number": 1, "phase_name": "Java Foundation", "order_index": 1,
            "title": "SQL Deep Dive & PostgreSQL",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 3, "skills_gained": "SQL,PostgreSQL",
            "desc": "Advanced SQL: JOINs, indexes, transactions, and PostgreSQL-specific features",
            "why": "You have basic SQL knowledge. This extends it to production-level PostgreSQL which is required for JPA/Hibernate.",
            "status": ItemStatus.COMPLETED,
            "resource": sql_resource,
            "scoring": {"goal_match": 0.80, "skill_gap_match": 0.50, "prerequisite_match": 1.0, "difficulty_match": 0.9, "preference_match": 0.7, "time_match": 0.9, "progress_match": 0.8, "feedback_adjustment": 0.5, "total_score": 0.77}
        },
        {
            "phase_number": 1, "phase_name": "Java Foundation", "order_index": 2,
            "title": "Java Foundation Project — Student Management System",
            "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 4, "skills_gained": "Core Java,SQL,OOP",
            "is_milestone": True, "milestone_text": "Phase 1 Complete: Built a console Java application demonstrating Java + SQL integration",
            "desc": "Build a Student Management CLI app integrating Core Java with SQL",
            "why": "Practical application of Java + SQL before moving to Spring Boot. Milestone project that validates your foundation.",
            "status": ItemStatus.COMPLETED,
            "project": json.dumps({
                "objective": "Build a Student Management Console Application",
                "requirements": ["CRUD for students", "File persistence with SQLite", "OOP class design", "Exception handling"],
                "skills_demonstrated": ["Core Java", "SQL", "OOP"],
                "expected_outcome": "Working CLI app managing student records with SQL backend"
            }),
            "scoring": {"goal_match": 0.88, "skill_gap_match": 0.60, "prerequisite_match": 1.0, "difficulty_match": 0.85, "preference_match": 0.95, "time_match": 0.85, "progress_match": 0.9, "feedback_adjustment": 0.5, "total_score": 0.84}
        },
        # Phase 2 — Spring Boot (current phase)
        {
            "phase_number": 2, "phase_name": "Spring Boot Core", "order_index": 0,
            "title": "Spring Boot Fundamentals & Dependency Injection",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 8, "skills_gained": "Spring Boot",
            "desc": "Spring Boot auto-configuration, IoC container, DI patterns, application structure",
            "why": "Spring Boot is your #1 critical skill gap (current: 1/5, target: 4/5). Your Java foundation is solid — this is the perfect next step.",
            "status": ItemStatus.IN_PROGRESS,
            "resource": spring_resource,
            "scoring": {"goal_match": 0.95, "skill_gap_match": 0.95, "prerequisite_match": 1.0, "difficulty_match": 0.88, "preference_match": 0.85, "time_match": 0.72, "progress_match": 0.85, "feedback_adjustment": 0.5, "total_score": 0.92}
        },
        {
            "phase_number": 2, "phase_name": "Spring Boot Core", "order_index": 1,
            "title": "Building REST APIs with Spring Boot",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 5, "skills_gained": "REST APIs,Spring Boot",
            "desc": "REST endpoint design, request/response mapping, validation, error handling, OpenAPI docs",
            "why": "REST APIs is a critical gap tied directly to your Backend Java Developer goal. Prerequisites (Spring Boot) are being completed now.",
            "status": ItemStatus.NOT_STARTED,
            "resource": rest_resource,
            "scoring": {"goal_match": 0.95, "skill_gap_match": 0.93, "prerequisite_match": 0.5, "difficulty_match": 0.88, "preference_match": 0.80, "time_match": 0.80, "progress_match": 0.75, "feedback_adjustment": 0.5, "total_score": 0.86}
        },
        {
            "phase_number": 2, "phase_name": "Spring Boot Core", "order_index": 2,
            "title": "Spring Data JPA & Hibernate ORM",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 6, "skills_gained": "JPA/Hibernate",
            "desc": "Entity mapping, relationships, JPA repositories, JPQL, transactions",
            "why": "JPA/Hibernate connects your SQL knowledge to Spring Boot. Your SQL proficiency (3/5) makes this the right time to learn ORM.",
            "status": ItemStatus.NOT_STARTED,
            "resource": jpa_resource,
            "scoring": {"goal_match": 0.82, "skill_gap_match": 0.87, "prerequisite_match": 0.5, "difficulty_match": 0.85, "preference_match": 0.75, "time_match": 0.75, "progress_match": 0.7, "feedback_adjustment": 0.5, "total_score": 0.80}
        },
        {
            "phase_number": 2, "phase_name": "Spring Boot Core", "order_index": 3,
            "title": "REST API Project — Personal Expense Tracker",
            "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 8, "skills_gained": "Spring Boot,REST APIs,JPA/Hibernate,SQL",
            "is_milestone": True, "milestone_text": "Phase 2 Complete: Built a CRUD REST API with database persistence",
            "desc": "End-to-end REST API with Spring Boot, JPA, and PostgreSQL",
            "why": "Hands-on project applying Spring Boot + REST + JPA together. This milestone validates your Phase 2 skills.",
            "status": ItemStatus.NOT_STARTED,
            "project": json.dumps({
                "objective": "Build a Personal Expense Tracker REST API",
                "requirements": ["Expense CRUD endpoints", "Category management", "Monthly summary stats", "Input validation", "PostgreSQL integration", "Swagger/OpenAPI docs"],
                "skills_demonstrated": ["Spring Boot", "REST APIs", "JPA/Hibernate", "SQL"],
                "expected_outcome": "Production-ready REST API with full CRUD and reporting endpoints"
            }),
            "scoring": {"goal_match": 0.93, "skill_gap_match": 0.90, "prerequisite_match": 0.3, "difficulty_match": 0.85, "preference_match": 0.95, "time_match": 0.60, "progress_match": 0.6, "feedback_adjustment": 0.5, "total_score": 0.83}
        },
        # Phase 3 — Security & Testing
        {
            "phase_number": 3, "phase_name": "Security & Testing", "order_index": 0,
            "title": "Spring Security & JWT Authentication",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.ADVANCED,
            "estimated_hours": 8, "skills_gained": "Spring Security",
            "desc": "Authentication flows, authorization, JWT tokens, security filters",
            "why": "Spring Security is required for any production API. Recommended priority — builds on Spring Boot knowledge from Phase 2.",
            "status": ItemStatus.NOT_STARTED,
            "resource": security_resource,
            "scoring": {"goal_match": 0.80, "skill_gap_match": 0.92, "prerequisite_match": 0.2, "difficulty_match": 0.70, "preference_match": 0.75, "time_match": 0.70, "progress_match": 0.5, "feedback_adjustment": 0.5, "total_score": 0.74}
        },
        {
            "phase_number": 3, "phase_name": "Security & Testing", "order_index": 1,
            "title": "Testing Spring Boot with JUnit & Mockito",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 5, "skills_gained": "Testing",
            "desc": "Unit tests, integration tests, MockMvc, test containers, TDD",
            "why": "Testing is a professional requirement. Your current testing level is 1/5 — this brings you to the 3/5 target for your goal.",
            "status": ItemStatus.NOT_STARTED,
            "resource": testing_resource,
            "scoring": {"goal_match": 0.75, "skill_gap_match": 0.80, "prerequisite_match": 0.2, "difficulty_match": 0.85, "preference_match": 0.70, "time_match": 0.80, "progress_match": 0.5, "feedback_adjustment": 0.5, "total_score": 0.71}
        },
        {
            "phase_number": 3, "phase_name": "Security & Testing", "order_index": 2,
            "title": "Secured API — Add Auth to Expense Tracker",
            "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED,
            "estimated_hours": 8, "skills_gained": "Spring Security,Testing",
            "is_milestone": True, "milestone_text": "Phase 3 Complete: Production-secured API with full test coverage",
            "desc": "Add JWT authentication and comprehensive tests to your Expense Tracker API",
            "why": "Apply Phase 3 skills to a real project. This milestone demonstrates you can build production-grade secured APIs.",
            "status": ItemStatus.NOT_STARTED,
            "project": json.dumps({
                "objective": "Secure the Expense Tracker API with JWT",
                "requirements": ["User registration/login", "JWT generation and validation", "Role-based access", "80%+ test coverage"],
                "skills_demonstrated": ["Spring Security", "Testing", "JWT"],
                "expected_outcome": "Secured production API with authentication and comprehensive tests"
            }),
            "scoring": {"goal_match": 0.85, "skill_gap_match": 0.85, "prerequisite_match": 0.15, "difficulty_match": 0.70, "preference_match": 0.90, "time_match": 0.60, "progress_match": 0.4, "feedback_adjustment": 0.5, "total_score": 0.75}
        },
        # Phase 4 — Production
        {
            "phase_number": 4, "phase_name": "Production & Deployment", "order_index": 0,
            "title": "Docker & Containerization",
            "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE,
            "estimated_hours": 4, "skills_gained": "Docker",
            "desc": "Container fundamentals, Dockerfile, docker-compose for development",
            "why": "Docker is optional for your 4-month goal but highly valuable for production deployment. Placed last to protect the critical path.",
            "status": ItemStatus.NOT_STARTED,
            "resource": docker_resource,
            "scoring": {"goal_match": 0.60, "skill_gap_match": 0.75, "prerequisite_match": 0.15, "difficulty_match": 0.85, "preference_match": 0.70, "time_match": 0.85, "progress_match": 0.4, "feedback_adjustment": 0.5, "total_score": 0.65}
        },
        {
            "phase_number": 4, "phase_name": "Production & Deployment", "order_index": 1,
            "title": "Capstone: Deploy to Production",
            "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED,
            "estimated_hours": 8, "skills_gained": "Docker,Spring Boot,REST APIs,Spring Security",
            "is_milestone": True, "milestone_text": "🎉 GOAL ACHIEVED: Backend Java Developer — Live Production API",
            "desc": "Containerize and deploy your full-stack API to a cloud provider",
            "why": "The final milestone that proves you are production-ready. This completes all 4 phases of your Backend Java Developer journey.",
            "status": ItemStatus.NOT_STARTED,
            "project": json.dumps({
                "objective": "Deploy your secured API to production",
                "requirements": ["Dockerize Spring Boot app", "docker-compose with PostgreSQL", "Deploy to Render/Railway", "Configure environment variables", "Set up health endpoints"],
                "skills_demonstrated": ["Docker", "Spring Boot", "REST APIs", "Spring Security"],
                "expected_outcome": "Live production URL — Backend Java Developer milestone achieved!"
            }),
            "scoring": {"goal_match": 0.92, "skill_gap_match": 0.80, "prerequisite_match": 0.1, "difficulty_match": 0.70, "preference_match": 0.92, "time_match": 0.55, "progress_match": 0.3, "feedback_adjustment": 0.5, "total_score": 0.78}
        },
    ]

    for item_data in roadmap_items_data:
        scoring = item_data.pop("scoring", {})
        resource_obj = item_data.pop("resource", None)
        project = item_data.pop("project", None)
        is_milestone = item_data.pop("is_milestone", False)
        milestone_text = item_data.pop("milestone_text", None)
        why = item_data.pop("why", "")
        desc = item_data.pop("desc", "")

        item = RoadmapItem(
            roadmap_id=roadmap.id,
            phase_number=item_data["phase_number"],
            phase_name=item_data["phase_name"],
            order_index=item_data["order_index"],
            title=item_data["title"],
            description=desc,
            type=item_data["type"],
            difficulty=item_data["difficulty"],
            estimated_hours=item_data["estimated_hours"],
            skills_gained=item_data["skills_gained"],
            is_milestone=is_milestone,
            milestone_text=milestone_text,
            status=item_data.get("status", ItemStatus.NOT_STARTED),
            why_recommended=why,
            scoring_metadata=json.dumps(scoring),
            project_info=project,
            resource_id=resource_obj.id if resource_obj else None,
        )
        db.add(item)

    await db.flush()

    # ── 6. Seed Assessments ────────────────────────────────────────────────────

    for skill_name, questions_data in ASSESSMENT_QUESTIONS.items():
        skill = skill_objects.get(skill_name)
        if not skill:
            continue

        # Set appropriate score based on demo setup
        score_map = {"Core Java": 72.0, "Spring Boot": 40.0, "SQL": 80.0}
        correct_map = {"Core Java": 4, "Spring Boot": 2, "SQL": 4}

        score_pct = score_map.get(skill_name, 60.0)
        correct = correct_map.get(skill_name, 3)

        assessment = Assessment(
            learner_id=alex.id,
            skill_id=skill.id,
            title=f"{skill_name} Skill Assessment",
            description=f"5-question assessment to measure your {skill_name} proficiency",
            total_questions=5,
            correct_answers=correct,
            score_percentage=score_pct,
            estimated_proficiency=score_pct / 100 * 5,  # convert % to 0-5
            status=AssessmentStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )
        db.add(assessment)
        await db.flush()

        answer_map = {"Core Java": ["B", "C", "D", "B", "C"], "Spring Boot": ["A", "B", "B", "B", "B"], "SQL": ["B", "B", "B", "B", "B"]}
        answers = answer_map.get(skill_name, ["B", "B", "B", "B", "B"])

        for i, q_data in enumerate(questions_data):
            learner_ans = answers[i]
            is_correct = learner_ans == q_data["correct"]
            q = AssessmentQuestion(
                assessment_id=assessment.id,
                question_number=i + 1,
                question_text=q_data["question_text"],
                options=json.dumps(q_data["options"]),
                correct_answer=q_data["correct"],
                learner_answer=learner_ans,
                is_correct=is_correct,
                explanation=q_data["explanation"],
                difficulty=q_data["difficulty"],
            )
            db.add(q)

    # ── 7. Seed Sample Feedback ───────────────────────────────────────────────

    feedbacks = [
        {
            "type": FeedbackType.VERY_USEFUL,
            "message": "The Java Streams tutorial was excellent — exactly what I needed!",
            "system_response": "Great! I'll prioritize more hands-on tutorials in your recommendations.",
            "processed": True,
        },
        {
            "type": FeedbackType.TOO_EASY,
            "message": "The basic SQL content was too easy, I already know this.",
            "system_response": "Understood. I've marked SQL basics as completed and updated your proficiency. Your roadmap now focuses on advanced SQL and JPA.",
            "processed": True,
        },
    ]

    for fb_data in feedbacks:
        fb = Feedback(
            learner_id=alex.id,
            type=fb_data["type"],
            message=fb_data["message"],
            system_response=fb_data["system_response"],
            processed=fb_data["processed"],
        )
        db.add(fb)

    # ── 8. Seed Chat History ──────────────────────────────────────────────────

    chat_history = [
        (MessageRole.USER, "What should I learn next?"),
        (MessageRole.ASSISTANT, "Based on your roadmap, your current item is **Spring Boot Fundamentals & Dependency Injection**. You've completed your Java Foundation phase — now it's time to dive into Spring Boot, which is your #1 critical skill gap (current: 1/5, target: 4/5). Focus on understanding dependency injection and auto-configuration first."),
        (MessageRole.USER, "Why is Spring Boot so important for my goal?"),
        (MessageRole.ASSISTANT, "Spring Boot is the #1 critical skill gap for a Backend Java Developer. It's the foundation for everything else in your roadmap — REST APIs, JPA/Hibernate, and Spring Security all require Spring Boot knowledge. Your strong Java and SQL background means you're ready for it now."),
    ]

    for role, content in chat_history:
        msg = ChatMessage(
            learner_id=alex.id,
            role=role,
            content=content,
        )
        db.add(msg)

    await db.commit()
    logger.info("✅ Database seeded successfully — Demo learner 'Alex Chen' created")
