"""Roadmap generation engine — creates ordered learning roadmaps respecting prerequisites."""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    Learner, Skill, LearnerSkill, Resource, Roadmap, RoadmapItem,
    SkillPriority, ItemType, ItemStatus, ResourceDifficulty, ScheduleStatus
)
from app.ai.provider import get_provider

logger = logging.getLogger(__name__)


# ── Roadmap template definitions for all major tech paths ─────────────────────

ROADMAP_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "dbms and sql specialist": [
        {
            "phase": 1,
            "name": "Relational Foundations & Schema Design",
            "items": [
                {
                    "title": "Database Architecture & ER Modeling",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 4,
                    "skills": "Relational Modeling,SQL",
                    "desc": "Understand relational concepts, tables, primary & foreign keys, constraints, and ER diagram design",
                    "milestone": "Design an ER diagram for an e-commerce platform",
                    "resource_keywords": ["sql", "database"]
                },
                {
                    "title": "Database Normalization (1NF to BCNF)",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 3,
                    "skills": "Database Normalization,Relational Modeling",
                    "desc": "Learn functional dependencies, 1NF, 2NF, 3NF, and BCNF to eliminate redundancy and anomalies",
                    "resource_keywords": ["database", "sql"]
                },
                {
                    "title": "Hands-on Schema Project: University DB",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 3,
                    "skills": "Relational Modeling,Database Normalization",
                    "desc": "Create a normalized relational schema with table constraints and relationships",
                    "milestone": "Phase 1 Complete: Relational Architecture Mastered",
                    "project": {
                        "objective": "Design and build a normalized database schema",
                        "requirements": ["ER Diagram", "Normalization up to 3NF", "Primary & Foreign keys", "Integrity constraints"],
                        "skills_demonstrated": ["Relational Modeling", "Database Normalization"],
                        "expected_outcome": "A fully functional database schema definition ready for SQL execution"
                    }
                }
            ]
        },
        {
            "phase": 2,
            "name": "SQL DDL, DML & Query Mastery",
            "items": [
                {
                    "title": "SQL DDL & DML Fundamentals",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 4,
                    "skills": "SQL,DDL & DML Queries",
                    "desc": "CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, and data types in modern RDBMS",
                    "resource_keywords": ["sql", "database"]
                },
                {
                    "title": "Filtering, Sorting & Pattern Matching",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 3,
                    "skills": "SQL,DDL & DML Queries",
                    "desc": "WHERE clauses, LIKE, BETWEEN, IN, ORDER BY, LIMIT/OFFSET, and NULL handling",
                    "resource_keywords": ["sql"]
                },
                {
                    "title": "Aggregate Functions & GROUP BY",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 4,
                    "skills": "SQL,DDL & DML Queries",
                    "desc": "COUNT, SUM, AVG, MIN, MAX, GROUP BY, and HAVING clauses for analytical queries",
                    "resource_keywords": ["sql"]
                },
                {
                    "title": "SQL Query Challenge: 50 Core Queries",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 4,
                    "skills": "SQL,DDL & DML Queries",
                    "desc": "Write real-world analytical queries against a live relational database dataset",
                    "milestone": "Phase 2 Complete: Core SQL Query Fluency",
                    "project": {
                        "objective": "Execute practical analytical and data modification SQL queries",
                        "requirements": ["Data ingestion", "Filtering and sorting", "Aggregate reports", "Data updates and deletions"],
                        "skills_demonstrated": ["SQL", "DDL & DML Queries"],
                        "expected_outcome": "A SQL script answering 50 business reporting questions"
                    }
                }
            ]
        },
        {
            "phase": 3,
            "name": "Advanced Joins, Subqueries & Views",
            "items": [
                {
                    "title": "Mastering SQL Joins (INNER, LEFT, RIGHT, FULL, CROSS, SELF)",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 5,
                    "skills": "Advanced Joins & Subqueries,SQL",
                    "desc": "Deep dive into multi-table joins, join algorithms, cartesian products, and self-joins",
                    "resource_keywords": ["sql", "postgresql"]
                },
                {
                    "title": "Subqueries, CTEs & Window Functions",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 5,
                    "skills": "Advanced Joins & Subqueries,SQL",
                    "desc": "Correlated subqueries, Common Table Expressions (WITH), ROW_NUMBER, RANK, DENSE_RANK, and PARTITION BY",
                    "resource_keywords": ["sql", "postgresql"]
                },
                {
                    "title": "Stored Procedures, Triggers & Views",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 4,
                    "skills": "Stored Procedures & Views,SQL",
                    "desc": "Create reusable views, stored procedures, user-defined functions, and automated triggers",
                    "resource_keywords": ["sql", "postgresql"]
                },
                {
                    "title": "Multi-Table Analytics Project",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 5,
                    "skills": "Advanced Joins & Subqueries,Stored Procedures & Views",
                    "desc": "Build an analytical reporting engine with window functions, CTEs, and automated triggers",
                    "milestone": "Phase 3 Complete: Advanced Data Querying",
                    "project": {
                        "objective": "Build automated business intelligence views and queries",
                        "requirements": ["Multi-table complex joins", "Window functions for rankings", "Recursive CTEs", "Audit trigger on modifications"],
                        "skills_demonstrated": ["Advanced Joins & Subqueries", "Stored Procedures & Views", "SQL"],
                        "expected_outcome": "Production-ready reporting views and stored routines"
                    }
                }
            ]
        },
        {
            "phase": 4,
            "name": "Transactions, Indexing & Query Optimization",
            "items": [
                {
                    "title": "Transactions, ACID Properties & Concurrency Control",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 4,
                    "skills": "Transactions & ACID,SQL",
                    "desc": "Commit, Rollback, Savepoints, Isolation Levels (Read Uncommitted to Serializable), and Deadlock handling",
                    "resource_keywords": ["sql", "postgresql", "database"]
                },
                {
                    "title": "Database Indexing & Query Plan Optimization",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 5,
                    "skills": "Indexing & Optimization,SQL",
                    "desc": "B-Tree vs Hash vs GIN indexes, EXPLAIN ANALYZE, query execution plans, and index scan optimization",
                    "resource_keywords": ["postgresql", "sql", "database"]
                },
                {
                    "title": "Final Capstone: High-Performance Database System",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 6,
                    "skills": "SQL,Indexing & Optimization,Transactions & ACID,Relational Modeling",
                    "desc": "Build and tune a high-concurrency database system with transactions, indexes, and optimized query plans",
                    "milestone": "GOAL ACHIEVED: DBMS & SQL Specialist",
                    "project": {
                        "objective": "Design, implement, and optimize a high-throughput relational database",
                        "requirements": [
                            "Full normalized relational schema",
                            "Transaction handling with isolation levels",
                            "Index creation and EXPLAIN plan tuning",
                            "Complex reporting queries with CTEs and Window functions"
                        ],
                        "skills_demonstrated": ["SQL", "Indexing & Optimization", "Transactions & ACID", "Relational Modeling"],
                        "expected_outcome": "A fully tuned database running optimized queries with benchmarked execution plans"
                    }
                }
            ]
        }
    ],

    "backend java developer": [
        {
            "phase": 1,
            "name": "Java Foundation",
            "items": [
                {
                    "title": "Advanced Java Concepts",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 6,
                    "skills": "Core Java,OOP",
                    "desc": "Deep dive into Java collections, generics, streams, and functional programming",
                    "milestone": "Build a console Java application using streams and collections",
                    "resource_keywords": ["java", "core java"]
                },
                {
                    "title": "Java Exception Handling & I/O",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 3,
                    "skills": "Core Java",
                    "desc": "Master exception handling patterns and Java I/O operations",
                    "resource_keywords": ["java", "exception"]
                },
                {
                    "title": "SQL & Database Fundamentals",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 5,
                    "skills": "SQL",
                    "desc": "CRUD operations, JOINs, indexes, and query optimization",
                    "resource_keywords": ["sql", "database"]
                },
                {
                    "title": "Java Foundation Project",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 4,
                    "skills": "Core Java,SQL,OOP",
                    "desc": "Build a Student Management System using Java and SQLite",
                    "milestone": "Phase 1 Complete: Foundation Skills",
                    "project": {
                        "objective": "Build a Student Management System",
                        "requirements": ["CRUD operations", "File I/O", "OOP design patterns", "SQL integration"],
                        "skills_demonstrated": ["Core Java", "SQL", "OOP"],
                        "expected_outcome": "A working CLI application managing student records"
                    }
                },
            ]
        },
        {
            "phase": 2,
            "name": "Spring Boot Core",
            "items": [
                {
                    "title": "Spring Boot Fundamentals",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 8,
                    "skills": "Spring Boot",
                    "desc": "Spring Boot auto-configuration, application structure, and dependency injection",
                    "resource_keywords": ["spring boot", "spring"]
                },
                {
                    "title": "Building REST APIs with Spring",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 6,
                    "skills": "REST APIs,Spring Boot",
                    "desc": "Create REST endpoints, request/response handling, DTOs, and OpenAPI docs",
                    "resource_keywords": ["spring boot", "rest", "api"]
                },
                {
                    "title": "Spring Data JPA & Hibernate",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 6,
                    "skills": "JPA/Hibernate,Spring Boot",
                    "desc": "ORM mapping, repositories, JPQL, transactions, and query methods",
                    "resource_keywords": ["jpa", "hibernate", "spring data"]
                },
                {
                    "title": "REST API Project: Expense Tracker",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 8,
                    "skills": "Spring Boot,REST APIs,JPA/Hibernate,SQL",
                    "milestone": "Phase 2 Complete: Build a CRUD REST API",
                    "desc": "Build a Personal Expense Tracker REST API",
                    "project": {
                        "objective": "Build a Personal Expense Tracker REST API",
                        "requirements": [
                            "CRUD for expenses with categories",
                            "Monthly summary endpoints",
                            "Input validation",
                            "PostgreSQL or H2 database",
                            "OpenAPI documentation"
                        ],
                        "skills_demonstrated": ["Spring Boot", "REST APIs", "JPA/Hibernate", "SQL"],
                        "expected_outcome": "A fully functional REST API ready for frontend integration"
                    }
                },
            ]
        },
        {
            "phase": 3,
            "name": "Security & Testing",
            "items": [
                {
                    "title": "Spring Security & JWT",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 8,
                    "skills": "Spring Security,Spring Boot",
                    "desc": "Authentication, authorization, JWT tokens, and security configurations",
                    "resource_keywords": ["spring security", "jwt", "security"]
                },
                {
                    "title": "Testing Spring Boot Applications",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 5,
                    "skills": "Testing,Spring Boot",
                    "desc": "Unit tests, integration tests, MockMvc, and test-driven development",
                    "resource_keywords": ["testing", "junit", "mockito"]
                },
                {
                    "title": "Secured API Project",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 10,
                    "skills": "Spring Security,Testing,Spring Boot,REST APIs",
                    "milestone": "Phase 3 Complete: Production-secured API",
                    "desc": "Add JWT authentication and comprehensive tests to your Expense Tracker",
                    "project": {
                        "objective": "Secure the Expense Tracker API with JWT authentication",
                        "requirements": [
                            "User registration and login",
                            "JWT token generation and validation",
                            "Role-based access control",
                            "Unit and integration tests (>80% coverage)"
                        ],
                        "skills_demonstrated": ["Spring Security", "Testing", "JWT"],
                        "expected_outcome": "Production-grade secured REST API with full test suite"
                    }
                },
            ]
        },
        {
            "phase": 4,
            "name": "Production & Deployment",
            "items": [
                {
                    "title": "Docker & Containerization",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 4,
                    "skills": "Docker",
                    "desc": "Docker fundamentals, writing Dockerfiles, docker-compose for local development",
                    "resource_keywords": ["docker", "container"]
                },
                {
                    "title": "Maven, Build & Deployment",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 3,
                    "skills": "Maven/Gradle",
                    "desc": "Maven lifecycle, dependency management, profiles, and CI/CD basics",
                    "resource_keywords": ["maven", "build"]
                },
                {
                    "title": "Final Capstone: Deploy to Production",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 8,
                    "skills": "Docker,Spring Boot,REST APIs,Spring Security",
                    "milestone": "GOAL ACHIEVED: Backend Java Developer",
                    "desc": "Containerize and deploy your secured API to a cloud provider",
                    "project": {
                        "objective": "Deploy a production-ready Java microservice",
                        "requirements": [
                            "Dockerize the Spring Boot application",
                            "Set up docker-compose with PostgreSQL",
                            "Deploy to Render or Railway",
                            "Configure environment variables",
                            "Set up health endpoints"
                        ],
                        "skills_demonstrated": ["Docker", "Spring Boot", "REST APIs", "Spring Security"],
                        "expected_outcome": "Live production URL with running API"
                    }
                },
            ]
        }
    ],

    "fullstack developer": [
        {
            "phase": 1,
            "name": "Frontend Essentials",
            "items": [
                {"title": "HTML5, Modern CSS & Flexbox/Grid", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.BEGINNER, "hours": 6, "skills": "HTML/CSS", "desc": "Semantic markup, responsive design, and CSS layouts"},
                {"title": "JavaScript (ES6+) & DOM Manipulation", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 8, "skills": "JavaScript", "desc": "Async/await, Promises, DOM events, and fetch API"},
                {"title": "Interactive Web App Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.BEGINNER, "hours": 4, "skills": "HTML/CSS,JavaScript", "desc": "Build a responsive task manager web app", "milestone": "Phase 1: Frontend Foundations Mastered"}
            ]
        },
        {
            "phase": 2,
            "name": "Modern React & State Management",
            "items": [
                {"title": "React Core & Component Architecture", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 8, "skills": "React,JavaScript", "desc": "JSX, props, state, hooks (useState, useEffect, useContext)"},
                {"title": "TypeScript for React Developers", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 5, "skills": "TypeScript,React", "desc": "Type safety, interfaces, generic components, and typed hooks"},
                {"title": "React Dashboard Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 6, "skills": "React,TypeScript", "desc": "Build a full-featured analytics dashboard with charts", "milestone": "Phase 2: React Component Mastery"}
            ]
        },
        {
            "phase": 3,
            "name": "Backend Node.js & REST APIs",
            "items": [
                {"title": "Node.js & Express API Development", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 8, "skills": "Node.js,REST APIs", "desc": "Server setup, routing, middleware, controllers, and JWT auth"},
                {"title": "SQL & PostgreSQL Database Integration", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 6, "skills": "SQL,Node.js", "desc": "Relational data modeling, queries, migrations, and ORM integration"},
                {"title": "Full Stack CRUD Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED, "hours": 8, "skills": "React,Node.js,REST APIs,SQL", "desc": "Connect React frontend to Express & Postgres backend", "milestone": "Phase 3: Full Stack Integration"}
            ]
        },
        {
            "phase": 4,
            "name": "Deployment & Production Capstone",
            "items": [
                {"title": "Docker, CI/CD & Cloud Deployment", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 5, "skills": "Docker,Git", "desc": "Containerize full stack app and deploy to Vercel + Render"},
                {"title": "Final Fullstack Capstone Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED, "hours": 10, "skills": "React,Node.js,SQL,Docker", "desc": "Deploy a complete SaaS product with auth, database, and payments", "milestone": "GOAL ACHIEVED: Full Stack Developer"}
            ]
        }
    ],

    "data scientist": [
        {
            "phase": 1,
            "name": "Python & Statistical Foundations",
            "items": [
                {"title": "Python for Data Science", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.BEGINNER, "hours": 6, "skills": "Python", "desc": "Python data structures, functions, OOP, and virtual environments"},
                {"title": "Applied Statistics & Probability", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 6, "skills": "Statistics", "desc": "Descriptive statistics, hypothesis testing, distributions, and probability"},
                {"title": "Statistical Data Analysis Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.BEGINNER, "hours": 4, "skills": "Python,Statistics", "desc": "Perform statistical exploration on real-world datasets", "milestone": "Phase 1: Statistics Mastered"}
            ]
        },
        {
            "phase": 2,
            "name": "Data Wrangling & Visualization",
            "items": [
                {"title": "NumPy & Pandas Mastery", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 8, "skills": "Pandas,Python", "desc": "Dataframes, cleaning, filtering, grouping, merging, and reshaping data"},
                {"title": "Data Visualization with Matplotlib & Seaborn", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 4, "skills": "Data Visualization,Python", "desc": "Exploratory Data Analysis (EDA) and publication-quality charts"},
                {"title": "SQL for Data Analysts", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 5, "skills": "SQL", "desc": "Complex queries, window functions, and data extraction from databases"},
                {"title": "Comprehensive EDA Capstone Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 6, "skills": "Pandas,Data Visualization,SQL", "desc": "Complete EDA report on healthcare or financial datasets", "milestone": "Phase 2: Data Wrangling Mastered"}
            ]
        },
        {
            "phase": 3,
            "name": "Machine Learning Algorithms",
            "items": [
                {"title": "Supervised Learning (Regression & Classification)", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 8, "skills": "Machine Learning,Python", "desc": "Linear regression, Logistic regression, Decision Trees, Random Forests, XGBoost"},
                {"title": "Unsupervised Learning & Clustering", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 6, "skills": "Machine Learning", "desc": "K-Means, PCA dimensionality reduction, and anomaly detection"},
                {"title": "Model Evaluation & Hyperparameter Tuning", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.ADVANCED, "hours": 4, "skills": "Machine Learning", "desc": "Cross-validation, ROC-AUC, Precision/Recall, GridSearch"},
                {"title": "End-to-End Predictive ML Project", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED, "hours": 8, "skills": "Machine Learning,Pandas", "desc": "Build and tune a churn prediction model with scikit-learn", "milestone": "Phase 3: Machine Learning Mastered"}
            ]
        },
        {
            "phase": 4,
            "name": "Deep Learning & Model Deployment",
            "items": [
                {"title": "Deep Learning with PyTorch Basics", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.ADVANCED, "hours": 8, "skills": "Deep Learning,Python", "desc": "Neural networks, backpropagation, and PyTorch tensors"},
                {"title": "Model Serving with Streamlit & FastAPI", "type": ItemType.LEARN, "difficulty": ResourceDifficulty.INTERMEDIATE, "hours": 5, "skills": "Python,Machine Learning", "desc": "Deploy machine learning models as interactive web apps and APIs"},
                {"title": "Final Data Science Capstone", "type": ItemType.PROJECT, "difficulty": ResourceDifficulty.ADVANCED, "hours": 10, "skills": "Machine Learning,Deep Learning,Python", "desc": "Deploy an AI data product live with interactive dashboard", "milestone": "GOAL ACHIEVED: Data Scientist"}
            ]
        }
    ],
}


async def generate_roadmap(
    learner: Learner,
    gaps: List[Dict[str, Any]],
    resources: List[Resource],
    db: AsyncSession,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Generate a complete personalized roadmap.
    Returns: (title, description, phases_data)
    """
    # 1. Try AI-powered dynamic roadmap generation
    provider = get_provider()
    if provider.is_available():
        try:
            ai_roadmap = await _ai_generate_roadmap(learner, gaps)
            if ai_roadmap and len(ai_roadmap) > 0:
                title = f"Personalized Roadmap: {learner.career_goal or 'Your Learning Path'}"
                desc = _generate_roadmap_description(learner, gaps, ai_roadmap)
                return title, desc, ai_roadmap
        except Exception as e:
            logger.warning(f"AI roadmap generation failed, falling back to smart template engine: {e}")

    # 2. Match template from domain knowledge base
    target_role = _detect_role(learner)
    template = ROADMAP_TEMPLATES.get(target_role)

    if not template:
        # If no hardcoded template matched the exact role, synthesize custom phases directly from the goal & gaps
        template = _synthesize_custom_roadmap(learner, gaps)

    # Filter/reorder template based on skill gaps
    phases_data = _personalize_template(template, gaps, learner)

    # Generate title and description
    title = f"Personalized Roadmap: {learner.career_goal or 'Your Learning Journey'}"
    desc = _generate_roadmap_description(learner, gaps, phases_data)

    return title, desc, phases_data


def _detect_role(learner: Learner) -> str:
    """Detect target role from learner goal."""
    texts = []
    if learner.career_goal:
        texts.append(learner.career_goal.lower())
    if learner.goal_description:
        texts.append(learner.goal_description.lower())
    combined = " ".join(texts)

    role_keywords = [
        ("fullstack developer", ["fullstack", "full stack", "full-stack", "mern", "mean"]),
        ("frontend developer", ["frontend", "front end", "react developer", "ui/ux", "web design"]),
        ("data scientist", ["data science", "data scientist", "data analysis", "data analyst", "pandas", "statistics"]),
        ("machine learning engineer", ["machine learning", "ml engineer", "deep learning", "ai engineer", "artificial intelligence", "nlp", "computer vision", "llm"]),
        ("devops engineer", ["devops", "cloud engineer", "aws", "kubernetes", "k8s", "ci/cd", "infrastructure", "terraform"]),
        ("backend python developer", ["python developer", "python backend", "fastapi", "django", "flask"]),
        ("backend java developer", ["java developer", "spring boot", "spring framework", "backend java", "core java"]),
        ("dbms and sql specialist", ["dbms", "database", "sql", "queries", "query", "postgres", "postgresql", "mysql", "rdbms", "relational", "sqlite"]),
    ]

    best_role = None
    best_score = 0

    for role_name, keywords in role_keywords:
        score = sum(len(kw) for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_role = role_name

    if best_role:
        return best_role

    return None


def _synthesize_custom_roadmap(learner: Learner, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Synthesize custom roadmap phases dynamically for any freeform goal."""
    skill_names = [g["skill_name"] for g in gaps] if gaps else ["Core Fundamentals", "Practical Skills", "Advanced Concepts"]
    goal_title = (learner.career_goal or "Custom Skill Mastery").title()

    # Split skills across 3-4 phases
    p1_skills = skill_names[:max(1, len(skill_names)//3)]
    p2_skills = skill_names[len(p1_skills):len(p1_skills) + max(1, len(skill_names)//3)]
    p3_skills = skill_names[len(p1_skills) + len(p2_skills):] or ["Applied Best Practices"]

    return [
        {
            "phase": 1,
            "name": f"Phase 1: {goal_title} — Core Fundamentals",
            "items": [
                {
                    "title": f"Fundamentals of {', '.join(p1_skills[:2])}",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 5,
                    "skills": ",".join(p1_skills),
                    "desc": f"Understand core principles, theory, and architecture of {', '.join(p1_skills)}",
                    "milestone": "Complete foundation assessments",
                    "resource_keywords": [s.lower() for s in p1_skills]
                },
                {
                    "title": f"Hands-on Starter Project: {goal_title} Lab 1",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.BEGINNER,
                    "hours": 4,
                    "skills": ",".join(p1_skills),
                    "desc": f"Apply fundamental concepts of {', '.join(p1_skills)} in a guided practical project",
                    "milestone": "Phase 1 Complete",
                    "project": {
                        "objective": f"Build initial working module for {goal_title}",
                        "requirements": ["Basic setup", "Core implementation", "Verification tests"],
                        "skills_demonstrated": p1_skills,
                        "expected_outcome": "Working prototype demonstrating core knowledge"
                    }
                }
            ]
        },
        {
            "phase": 2,
            "name": f"Phase 2: {goal_title} — Implementation & Practice",
            "items": [
                {
                    "title": f"In-depth Mastery: {', '.join(p2_skills[:2])}",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 6,
                    "skills": ",".join(p2_skills),
                    "desc": f"Deep dive into intermediate features, workflows, and tools for {', '.join(p2_skills)}",
                    "resource_keywords": [s.lower() for s in p2_skills]
                },
                {
                    "title": f"Intermediate Application Project: {goal_title} Lab 2",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.INTERMEDIATE,
                    "hours": 6,
                    "skills": ",".join(p2_skills),
                    "desc": f"Build intermediate functionality combining multiple concepts",
                    "milestone": "Phase 2 Complete",
                    "project": {
                        "objective": f"Implement intermediate features for {goal_title}",
                        "requirements": ["Feature implementation", "Error handling", "Documentation"],
                        "skills_demonstrated": p2_skills,
                        "expected_outcome": "Functional subsystem"
                    }
                }
            ]
        },
        {
            "phase": 3,
            "name": f"Phase 3: {goal_title} — Advanced Optimization & Capstone",
            "items": [
                {
                    "title": f"Advanced Techniques & Optimization",
                    "type": ItemType.LEARN,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 6,
                    "skills": ",".join(p3_skills),
                    "desc": f"Performance tuning, scalability, error handling, and production best practices",
                    "resource_keywords": [s.lower() for s in p3_skills]
                },
                {
                    "title": f"Final Capstone: Production-Ready {goal_title}",
                    "type": ItemType.PROJECT,
                    "difficulty": ResourceDifficulty.ADVANCED,
                    "hours": 8,
                    "skills": ",".join(skill_names),
                    "desc": f"Build, test, and polish an end-to-end capstone project demonstrating complete mastery",
                    "milestone": f"GOAL ACHIEVED: {goal_title}",
                    "project": {
                        "objective": f"Deliver a complete, production-ready implementation of {goal_title}",
                        "requirements": ["End-to-end architecture", "Optimization & benchmarks", "Comprehensive documentation"],
                        "skills_demonstrated": skill_names[:4],
                        "expected_outcome": "Complete portfolio capstone project"
                    }
                }
            ]
        }
    ]


async def _ai_generate_roadmap(learner: Learner, gaps: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Use AI to construct a custom multi-phase roadmap tailored to the learner's timeline & goal."""
    provider = get_provider()
    if not provider.is_available():
        return None

    prompt = f"""Generate a personalized learning roadmap for this learner:

GOAL: "{learner.career_goal or ''}"
GOAL DESCRIPTION: "{learner.goal_description or ''}"
EXPERIENCE LEVEL: "{learner.experience_level or 'INTERMEDIATE'}"
WEEKLY HOURS AVAILABLE: {learner.weekly_hours_available or 8}
TIMELINE: "{learner.target_timeline or 'custom'}"
SKILL GAPS IDENTIFIED: {json.dumps([g['skill_name'] for g in gaps])}

Generate 3 to 4 sequential learning phases respecting prerequisites.
Return ONLY valid JSON array with this exact structure:
[
  {{
    "phase": 1,
    "name": "Phase Name",
    "items": [
      {{
        "title": "Item Title",
        "type": "LEARN",
        "difficulty": "BEGINNER",
        "hours": 4,
        "skills": "Skill1,Skill2",
        "desc": "Detailed description of what the learner will study and do",
        "milestone": "Phase 1 Complete (or null)",
        "project": null
      }},
      {{
        "title": "Hands-on Project Title",
        "type": "PROJECT",
        "difficulty": "INTERMEDIATE",
        "hours": 5,
        "skills": "Skill1,Skill2",
        "desc": "Build a hands-on project",
        "milestone": "Phase 1 Milestone",
        "project": {{
          "objective": "Project goal",
          "requirements": ["Req 1", "Req 2"],
          "skills_demonstrated": ["Skill1", "Skill2"],
          "expected_outcome": "Deliverable outcome"
        }}
      }}
    ]
  }}
]

Rules:
- Difficulty must be "BEGINNER", "INTERMEDIATE", or "ADVANCED"
- Type must be "LEARN" or "PROJECT"
- Tailor the items specifically to the user's input (e.g. if they want to write DBMS queries in 3 days, create intensive query-writing and schema design labs)
- Do NOT output markdown or explanation, ONLY the valid JSON array."""

    try:
        data = await provider.generate_json(prompt)
        if isinstance(data, list) and len(data) > 0:
            # Normalize enum strings
            for phase in data:
                for item in phase.get("items", []):
                    item["type"] = ItemType(item.get("type", "LEARN"))
                    item["difficulty"] = ResourceDifficulty(item.get("difficulty", "INTERMEDIATE"))
            return data
    except Exception as e:
        logger.warning(f"AI dynamic roadmap generation failed: {e}")
    return None


def _personalize_template(
    template: List[Dict],
    gaps: List[Dict],
    learner: Learner
) -> List[Dict]:
    """Personalize roadmap template based on learner's actual skill gaps."""
    gap_map = {g["skill_name"].lower(): g for g in gaps}

    # Strong skills — may allow skipping beginner content
    strong_skills = {
        g["skill_name"].lower()
        for g in gaps
        if g["current_proficiency"] >= 3.0
    }

    personalized_phases = []
    for phase in template:
        items = []
        for item in phase["items"]:
            skills_lower = [s.strip().lower() for s in str(item.get("skills", "")).split(",")]

            # Check if any skill in this item is already strong → can skip/reduce
            all_strong = len(skills_lower) > 0 and all(s in strong_skills for s in skills_lower)
            item_copy = dict(item)
            if all_strong and item_copy.get("type") != ItemType.PROJECT:
                item_copy["desc"] = f"[Can be fast-tracked if you already know this] {item_copy.get('desc', '')}"

            items.append(item_copy)

        personalized_phases.append({**phase, "items": items})

    return personalized_phases


def _generate_roadmap_description(learner, gaps, phases) -> str:
    critical_count = sum(1 for g in gaps if g.get("priority") == SkillPriority.CRITICAL and g.get("gap_score", 0) > 0.1)
    total_hours = sum(
        item.get("hours", 4)
        for p in phases
        for item in p.get("items", [])
    )
    weeks = total_hours / max(1, learner.weekly_hours_available or 8)

    return (
        f"This personalized roadmap for '{learner.career_goal}' consists of {len(phases)} phases "
        f"targeting {critical_count} critical skill gaps. "
        f"Estimated {total_hours} hours total at {learner.weekly_hours_available or 8} hours/week = "
        f"~{max(1, round(weeks))} weeks. Phases are structured to build from foundation to real-world capstone projects."
    )


def compute_schedule_status(learner: Learner, roadmap: Optional[Roadmap]) -> ScheduleStatus:
    """Calculate if learner is on-track for their goal."""
    if not learner or not learner.target_timeline:
        return ScheduleStatus.ON_TRACK

    timeline_str = learner.target_timeline.lower()
    weeks_available = 16  # default
    if "month" in timeline_str:
        try:
            months = int(timeline_str.split()[0])
            weeks_available = months * 4
        except ValueError:
            pass
    elif "week" in timeline_str:
        try:
            weeks_available = int(timeline_str.split()[0])
        except ValueError:
            pass
    elif "day" in timeline_str:
        weeks_available = 1

    if not roadmap or roadmap.total_items == 0:
        return ScheduleStatus.ON_TRACK

    weeks_in = max(1, (datetime.utcnow() - roadmap.generated_at).days // 7)
    expected_completion = weeks_in / weeks_available
    actual_completion = roadmap.completion_percentage / 100

    if actual_completion >= expected_completion + 0.1:
        return ScheduleStatus.AHEAD_OF_SCHEDULE
    elif actual_completion >= expected_completion - 0.1:
        return ScheduleStatus.ON_TRACK
    else:
        return ScheduleStatus.AT_RISK


def estimate_completion_date(learner: Learner, remaining_hours: float) -> str:
    """Estimate when learner will complete the roadmap."""
    hours_per_week = max(1, learner.weekly_hours_available or 8)
    weeks = remaining_hours / hours_per_week
    estimated_date = datetime.utcnow() + timedelta(weeks=weeks)
    return estimated_date.strftime("%B %Y")
