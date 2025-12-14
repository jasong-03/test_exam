# Documentation Index - Exam Extractor

**Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Complete

---

## Welcome

This documentation provides comprehensive guidance for understanding, using, and developing the **Growtrics Exam Extractor** - an intelligent multi-agent system for extracting structured questions from exam PDF files.

---

## Quick Navigation

### For First-Time Users
1. Start with **[../README.md](../README.md)** (5 min read)
   - Quick start guide
   - Basic usage examples
   - Feature overview

2. Then review **[project-overview-pdr.md](project-overview-pdr.md)** (15 min read)
   - Project vision and scope
   - Key features and requirements
   - Success metrics

### For Developers
1. Read **[codebase-summary.md](codebase-summary.md)** (20 min read)
   - Directory structure
   - Module overview
   - File organization

2. Review **[system-architecture.md](system-architecture.md)** (25 min read)
   - 5-phase pipeline
   - Agent interactions
   - Data flow diagrams

3. Study **[code-standards.md](code-standards.md)** (30 min read)
   - Naming conventions
   - Type hints and patterns
   - Error handling

### For Advanced Customization
1. Review **[system-architecture.md](system-architecture.md)** for design details
2. Examine **[code-standards.md](code-standards.md)** for implementation patterns
3. Check original flow docs: **[../FLOW_OPTIMIZED.md](../FLOW_OPTIMIZED.md)** and **[../JSON_EXAMPLES.md](../JSON_EXAMPLES.md)**

---

## Documentation Map

### 1. Project-Level Documentation

#### **README.md** (../README.md)
**Purpose**: Quick start and feature overview
**Length**: 370 lines | **Read Time**: 5-10 minutes
**Contains**:
- Installation instructions
- Basic usage (CLI and Python API)
- Feature list
- Output format examples
- Configuration options
- Troubleshooting

**When to Read**: First thing when getting started

---

#### **project-overview-pdr.md**
**Purpose**: Product requirements and business context
**Length**: 490 lines | **Read Time**: 15-20 minutes
**Contains**:
- Project vision and goals
- Feature descriptions
- Functional requirements (FR-001 to FR-007)
- Non-functional requirements (NFR-001 to NFR-006)
- Acceptance criteria
- Data specifications
- Success metrics
- Risk assessment

**When to Read**: Understanding product requirements and strategic goals

**Key Sections**:
- Strategic goals and vision
- Feature overview (6 major features)
- 7 functional requirements
- 6 non-functional requirements
- Cost and performance targets

---

### 2. Technical Documentation

#### **codebase-summary.md**
**Purpose**: Structural overview of codebase
**Length**: 497 lines | **Read Time**: 20-30 minutes
**Contains**:
- Directory structure
- Module overview (agents, models, tracking)
- Class descriptions and responsibilities
- Configuration constants
- Entry points (CLI, Python API, Direct)
- Performance characteristics
- File count and statistics

**When to Read**: Understanding codebase organization

**Key Sections**:
- Directory structure diagram
- Module overview with key classes
- Configuration and constants
- Entry points and usage patterns
- Performance metrics

---

#### **system-architecture.md**
**Purpose**: Detailed system design and component interaction
**Length**: 791 lines | **Read Time**: 30-45 minutes
**Contains**:
- High-level architecture diagram
- 5-phase pipeline with detailed flows
- Agent interaction diagrams
- Data model hierarchy
- Data flow diagrams
- Cost optimization strategies
- Error handling and recovery
- Scalability considerations
- Output directory structure
- Performance characteristics

**When to Read**: Deep dive into system design and architecture

**Key Sections**:
- Architecture overview
- 5-phase pipeline details (Phase 1-5)
- Phase 3 optimization (50% cost reduction)
- Agent interactions
- Data model hierarchy
- Cost optimization mechanisms
- Error handling strategy
- Scalability approaches

---

#### **code-standards.md**
**Purpose**: Coding conventions and implementation guidelines
**Length**: 875 lines | **Read Time**: 40-50 minutes
**Contains**:
- Python version and environment setup
- File organization and naming
- Naming conventions (classes, functions, variables, constants)
- Type hints and type safety
- Dataclass patterns
- JSON serialization
- Async/await patterns
- Error handling approaches
- Logging standards
- Testing strategy
- Documentation standards
- Code review checklist

**When to Read**: Contributing code to the project

**Key Sections**:
- Naming conventions (detailed examples)
- Type hints best practices
- Dataclass and serialization patterns
- Async/await guidelines
- Error handling patterns
- Logging standards with examples
- Testing patterns
- Code review checklist

---

### 3. Original Reference Documentation

#### **FLOW_OPTIMIZED.md** (../FLOW_OPTIMIZED.md)
**Purpose**: Detailed pipeline flow documentation
**Length**: 350 lines
**Contains**: Original pipeline documentation with optimization details
**When to Read**: Understanding historical optimization approach

---

#### **JSON_EXAMPLES.md** (../JSON_EXAMPLES.md)
**Purpose**: Complete JSON schema examples
**Length**: 537 lines
**Contains**: JSON input/output examples and schema mappings
**When to Read**: Understanding data format specifications

---

## Document Statistics

| Document | Lines | Size | Type |
|----------|-------|------|------|
| README.md | 372 | 12 KB | User Guide |
| project-overview-pdr.md | 490 | 16 KB | Requirements |
| codebase-summary.md | 497 | 16 KB | Technical |
| system-architecture.md | 791 | 26 KB | Technical |
| code-standards.md | 875 | 21 KB | Guidelines |
| **Total Docs** | **3,025** | **91 KB** | - |
| FLOW_OPTIMIZED.md | 350 | 8 KB | Reference |
| JSON_EXAMPLES.md | 537 | 14 KB | Reference |
| **Grand Total** | **3,912** | **113 KB** | - |

---

## Learning Paths

### Path 1: User (5-15 minutes)
Estimated Time: 20 minutes

1. **README.md** - Basic usage and features (10 min)
2. **Installation** - Set up environment (5 min)
3. **Run example** - Process sample PDF (5 min)

**Outcome**: Can run Exam Extractor and understand basic features

---

### Path 2: Developer (45-90 minutes)
Estimated Time: 60 minutes

1. **README.md** - Overview (10 min)
2. **project-overview-pdr.md** - Requirements (15 min)
3. **codebase-summary.md** - Structure (15 min)
4. **system-architecture.md** - Design (15 min)
5. **code-standards.md** (sections only) - Key patterns (5 min)

**Outcome**: Understand architecture, can contribute code following standards

---

### Path 3: Deep Dive (2-4 hours)
Estimated Time: 180 minutes

1. **README.md** - Full read (10 min)
2. **project-overview-pdr.md** - Full read (20 min)
3. **codebase-summary.md** - Full read (25 min)
4. **system-architecture.md** - Full read (45 min)
5. **code-standards.md** - Full read (50 min)
6. **Original docs** - FLOW_OPTIMIZED.md + JSON_EXAMPLES.md (30 min)

**Outcome**: Complete understanding of system, ready for advanced development

---

## Key Concepts by Document

### Pipeline Architecture
**Documents**: system-architecture.md, FLOW_OPTIMIZED.md
- 5-phase pipeline
- Phase 3 optimization
- Cost reduction (50%)
- Error handling

### Data Models
**Documents**: codebase-summary.md, system-architecture.md
- 20 dataclasses
- 5 enums
- Hierarchy and composition
- Serialization patterns

### Agent System
**Documents**: system-architecture.md, codebase-summary.md
- 6 specialized agents
- Orchestration pattern
- Async processing
- Error recovery

### API Integration
**Documents**: project-overview-pdr.md, system-architecture.md
- Gemini API usage
- Cost tracking
- Token counting
- Response formats

### Development Standards
**Documents**: code-standards.md
- Type hints
- Naming conventions
- Error handling
- Testing patterns
- Logging standards

---

## Quick Reference

### Essential Files and Locations

```
exam_extractor/
├── README.md                           # START HERE
├── docs/
│   ├── INDEX.md                        # This file
│   ├── project-overview-pdr.md        # Product requirements
│   ├── codebase-summary.md            # Code structure
│   ├── system-architecture.md         # Design details
│   └── code-standards.md              # Coding rules
├── agents/                             # Agent implementations
├── models/                             # Data structures
├── tracking/                           # Cost and logging
└── FLOW_OPTIMIZED.md                  # Original flow docs
```

### Key Classes to Know

**Core Agents**:
- `OrchestratorAgent` - Pipeline coordinator
- `PDFParserAgent` - PDF processing
- `QuestionExtractorAgent` - Question extraction
- `DiagramExtractorAgent` - Diagram handling
- `AnswerKeyAgent` - Answer extraction

**Data Models**:
- `ExamPaper` - Root output object
- `Question` - Individual question
- `Diagram` - Figure/diagram
- `AnswerKey` - Solution object
- `ExamMetadata` - Exam information

**Tracking**:
- `CostTracker` - Token and cost tracking
- `PipelineLogger` - Event logging

### CLI Commands

```bash
# Basic usage
python -m exam_extractor.main exam.pdf

# With options
python -m exam_extractor.main exam.pdf --output results/ -v

# Batch processing
python -m exam_extractor.main *.pdf --parallel

# Skip features
python -m exam_extractor.main exam.pdf --no-diagrams --no-answers
```

### Configuration

```bash
# Environment variable
export GEMINI_API_KEY=your_key_here

# Or .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

---

## FAQ and Common Questions

### Q: Where do I start?
**A**: Read README.md first (10 min), then run the sample exam to see the system in action.

### Q: How does the system reduce costs?
**A**: Combined question + diagram extraction in single LLM call (Phase 3) reduces API calls by 50%.

### Q: What question types are supported?
**A**: 8 types: Multiple Choice, Short Answer, Long Answer, Working Area, Fill-in-Blank, True/False, Matching, Diagram Label.

### Q: Can I run it offline?
**A**: No, Gemini API key required for extraction. Cost tracking and logging work offline.

### Q: How long does processing take?
**A**: 5-8 seconds per page; 10-page exam typically takes 45-60 seconds.

### Q: What's the cost per exam?
**A**: Typically $0.10-0.20 USD for 10-30 page exam (varies by content density).

### Q: How accurate is extraction?
**A**: 95%+ accuracy on standard exams; confidence scores provided per element.

### Q: Can I customize the extraction?
**A**: Yes, review code-standards.md for patterns, or modify prompts in agents/prompts.py.

---

## Updates and Maintenance

### Document Version Control
- **Version**: 1.0.0
- **Last Updated**: 2025-12-14
- **Status**: Production Ready
- **Review Schedule**: Quarterly

### Keeping Documentation Current

When updating code:
1. Update relevant documentation
2. Run repomix to regenerate codebase-summary.md
3. Update system-architecture.md if pipeline changes
4. Update code-standards.md if conventions change
5. Test all examples in README.md

---

## Document Cross-References

### By Topic

**Getting Started**:
- README.md (Quick Start)
- project-overview-pdr.md (Features)

**Architecture**:
- system-architecture.md (Detailed design)
- FLOW_OPTIMIZED.md (Pipeline flow)

**Implementation**:
- codebase-summary.md (Code structure)
- code-standards.md (Coding guidelines)

**Data Format**:
- JSON_EXAMPLES.md (Schema examples)
- system-architecture.md (Data models)

**Operations**:
- README.md (CLI usage)
- codebase-summary.md (Entry points)

---

## Support Resources

### Documentation Navigation
- **This File**: INDEX.md (you are here)
- **Project Root**: README.md
- **Requirements**: project-overview-pdr.md
- **Architecture**: system-architecture.md
- **Code**: code-standards.md
- **Structure**: codebase-summary.md

### Troubleshooting
1. Check README.md troubleshooting section
2. Review error logs in output/logs/
3. Check project-overview-pdr.md error handling section
4. Review code-standards.md error patterns

### Further Help
- Run with `-v` flag for verbose output
- Check output/logs/agents/ for detailed traces
- Review cost breakdown in output/logs/costs/

---

## Document Metadata

| Attribute | Value |
|-----------|-------|
| Project | Growtrics Exam Extractor |
| Version | 1.0.0 |
| Python Version | 3.10+ |
| API | Google Gemini |
| Status | Production Ready |
| Last Updated | 2025-12-14 |
| Maintainer | Documentation Team |
| Review Cycle | Quarterly |

---

## Document Change Log

### Version 1.0.0 (2025-12-14)
- Initial comprehensive documentation
- Created 4 core documentation files
- Added README with quick start
- Index file (this document)

---

**Navigation**:
- [← Back to Project](../README.md)
- [Code Standards →](code-standards.md)
- [System Architecture →](system-architecture.md)

---

**End of Index**
Last Updated: 2025-12-14
