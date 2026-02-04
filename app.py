"""
Streamlit chat UI for PM Brainstorming System.

Implements a human-in-the-loop flow with 3 checkpoints:
1. Problem Refinement - Make input specific and concrete
2. Classification - Confirm or override the routing
3. Soft Guesses - Validate assumptions before full analysis

Run with: uv run streamlit run app.py
"""

import streamlit as st
from pm_agents import (
    run_stage1_refinement,
    run_stage2_classification,
    run_stage3_soft_guesses,
    run_stage4_specialist,
)

# --------------------
# PAGE CONFIG
# --------------------

st.set_page_config(
    page_title="PM Brainstorming Assistant",
    page_icon="🎯",
    layout="wide"
)


# --------------------
# CUSTOM CSS
# --------------------

st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Progress bar styling */
    .progress-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #e0e0e0;
    }

    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }

    .progress-step::after {
        content: '';
        position: absolute;
        top: 15px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: #e0e0e0;
        z-index: -1;
    }

    .progress-step:last-child::after {
        display: none;
    }

    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }

    .step-circle.completed {
        background: #10b981;
        color: white;
    }

    .step-circle.active {
        background: #3b82f6;
        color: white;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
    }

    .step-circle.pending {
        background: #f3f4f6;
        color: #9ca3af;
        border: 2px solid #e5e7eb;
    }

    .step-label {
        font-size: 12px;
        color: #6b7280;
        text-align: center;
    }

    .step-label.active {
        color: #3b82f6;
        font-weight: 600;
    }

    .step-label.completed {
        color: #10b981;
    }

    /* Sidebar agent cards */
    .agent-card {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .agent-card:hover {
        border-color: #3b82f6;
        background: #f8fafc;
    }

    .agent-card-title {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 2px;
    }

    .agent-card-desc {
        font-size: 12px;
        color: #6b7280;
    }

    /* Welcome card styling */
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .welcome-card h2 {
        margin-bottom: 0.5rem;
    }

    /* Checkpoint card styling */
    .checkpoint-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .checkpoint-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .checkpoint-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .checkpoint-icon.refine { background: #dbeafe; }
    .checkpoint-icon.classify { background: #dcfce7; }
    .checkpoint-icon.validate { background: #fef3c7; }
    .checkpoint-icon.analyze { background: #f3e8ff; }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }

    .status-badge.success {
        background: #dcfce7;
        color: #166534;
    }

    .status-badge.info {
        background: #dbeafe;
        color: #1e40af;
    }

    .status-badge.warning {
        background: #fef3c7;
        color: #92400e;
    }

    /* Example prompts styling */
    .example-prompt {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 14px;
        color: #475569;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .example-prompt:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Improve button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* Improve selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
    }

    /* Improve text area */
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }

    /* Improve expander */
    .streamlit-expanderHeader {
        font-weight: 500;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------
# PROGRESS INDICATOR
# --------------------

WORKFLOW_STAGES = [
    ("input", "Start", "1"),
    ("refinement", "Refine", "2"),
    ("classification", "Classify", "3"),
    ("soft_guesses", "Validate", "4"),
    ("streaming", "Analyze", "5"),
    ("complete", "Done", "✓"),
]

def render_progress_indicator():
    """Render the workflow progress indicator."""
    current_stage = st.session_state.workflow_stage
    stage_order = [s[0] for s in WORKFLOW_STAGES]
    current_idx = stage_order.index(current_stage) if current_stage in stage_order else 0

    cols = st.columns(len(WORKFLOW_STAGES))

    for i, (stage_id, label, number) in enumerate(WORKFLOW_STAGES):
        with cols[i]:
            if i < current_idx:
                # Completed
                st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: #10b981; color: white;
                                    display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;">
                            ✓
                        </div>
                        <div style="font-size: 12px; color: #10b981; margin-top: 4px;">{label}</div>
                    </div>
                """, unsafe_allow_html=True)
            elif i == current_idx:
                # Active
                st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: #3b82f6; color: white;
                                    display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;
                                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);">
                            {number}
                        </div>
                        <div style="font-size: 12px; color: #3b82f6; font-weight: 600; margin-top: 4px;">{label}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Pending
                st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: #f3f4f6; color: #9ca3af;
                                    display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;
                                    border: 2px solid #e5e7eb;">
                            {number}
                        </div>
                        <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{label}</div>
                    </div>
                """, unsafe_allow_html=True)


# --------------------
# SIDEBAR
# --------------------

AGENT_CARDS = [
    {
        "id": "prioritization",
        "icon": "⚖️",
        "title": "Prioritization",
        "desc": "Trade-off decisions & competing priorities",
        "view": "doc_prioritization",
    },
    {
        "id": "problem_space",
        "icon": "🔍",
        "title": "Problem Space",
        "desc": "Validate if problems exist & matter",
        "view": "doc_problem_space",
    },
    {
        "id": "context_mapping",
        "icon": "🗺️",
        "title": "Context Mapping",
        "desc": "Map stakeholders & org dynamics",
        "view": "doc_context_mapping",
    },
    {
        "id": "constraints",
        "icon": "🚧",
        "title": "Constraints",
        "desc": "Surface hidden blockers & limitations",
        "view": "doc_constraints",
    },
    {
        "id": "solution_validation",
        "icon": "✅",
        "title": "Solution Validation",
        "desc": "Stress-test ideas before building",
        "view": "doc_solution_validation",
    },
]

COMING_SOON = [
    {"icon": "👥", "title": "Stakeholder Mapping"},
    {"icon": "📊", "title": "Competitive Analysis"},
    {"icon": "🚀", "title": "Go-to-Market Planning"},
]


def render_sidebar():
    """Render sidebar with navigation buttons to agent documentation pages."""
    with st.sidebar:
        st.markdown("### 📚 Agent Library")
        st.caption("Learn about each agent's methodology")

        st.markdown("")  # spacing

        for agent in AGENT_CARDS:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown(f"<span style='font-size: 24px;'>{agent['icon']}</span>", unsafe_allow_html=True)
            with col2:
                if st.button(
                    agent["title"],
                    key=f"btn_{agent['id']}",
                    use_container_width=True,
                    help=agent["desc"]
                ):
                    st.session_state.current_view = agent["view"]
                    st.rerun()
                st.caption(agent["desc"])

            st.markdown("")  # spacing between cards

        st.divider()

        st.markdown("### 🔮 Coming Soon")
        for item in COMING_SOON:
            st.markdown(f"{item['icon']} **{item['title']}**")
            st.caption("In development")


# --------------------
# SESSION STATE INIT
# --------------------

# Workflow stage: "input" | "refinement" | "classification" | "soft_guesses" | "streaming" | "complete"
if "workflow_stage" not in st.session_state:
    st.session_state.workflow_stage = "input"

# Data from each stage
if "original_input" not in st.session_state:
    st.session_state.original_input = ""
if "refinement_data" not in st.session_state:
    st.session_state.refinement_data = None
if "refined_input" not in st.session_state:
    st.session_state.refined_input = ""
if "classification_data" not in st.session_state:
    st.session_state.classification_data = None
if "soft_guesses_data" not in st.session_state:
    st.session_state.soft_guesses_data = []
if "confirmed_guesses" not in st.session_state:
    st.session_state.confirmed_guesses = []
if "final_output" not in st.session_state:
    st.session_state.final_output = ""

# Chat history for display
if "messages" not in st.session_state:
    st.session_state.messages = []

# View state: "chat" or "doc_<agent_name>" for documentation pages
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"


def reset_workflow():
    """Reset workflow to initial state."""
    st.session_state.workflow_stage = "input"
    st.session_state.original_input = ""
    st.session_state.refinement_data = None
    st.session_state.refined_input = ""
    st.session_state.classification_data = None
    st.session_state.soft_guesses_data = []
    st.session_state.confirmed_guesses = []
    st.session_state.final_output = ""


# --------------------
# DISPLAY HELPERS
# --------------------

def display_chat_history():
    """Display previous messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "coordinator" in message:
                st.info(
                    f"**Classification:** {message['coordinator']['classification']}\n\n"
                    f"**Reasoning:** {message['coordinator']['reasoning']}"
                )
            st.markdown(message["content"])


EXAMPLE_PROMPTS = [
    "Should we build feature A or B first?",
    "I think users struggle with onboarding, but I'm not sure",
    "Engineering says this won't work but I don't understand why",
    "We're entering a new market and need to understand the landscape",
]


def show_welcome():
    """Show welcome message with usage instructions."""
    # Hero section
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;">
            <h2 style="margin: 0 0 0.5rem 0; color: white;">Welcome to PM Brainstorming</h2>
            <p style="margin: 0; opacity: 0.9;">Your AI thinking partner for product decisions</p>
        </div>
    """, unsafe_allow_html=True)

    # How it works - horizontal steps
    st.markdown("#### How it works")
    cols = st.columns(4)
    steps = [
        ("1️⃣", "Describe", "Share your PM challenge"),
        ("2️⃣", "Refine", "We clarify together"),
        ("3️⃣", "Validate", "Confirm assumptions"),
        ("4️⃣", "Analyze", "Get actionable insights"),
    ]
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f8fafc; border-radius: 8px; height: 100%;">
                    <div style="font-size: 24px;">{num}</div>
                    <div style="font-weight: 600; margin: 0.5rem 0;">{title}</div>
                    <div style="font-size: 13px; color: #64748b;">{desc}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("")  # spacing

    # Example prompts
    st.markdown("#### Try an example")
    col1, col2 = st.columns(2)
    for i, prompt in enumerate(EXAMPLE_PROMPTS):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(f"💡 {prompt}", key=f"example_{i}", use_container_width=True):
                st.session_state.original_input = prompt
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Trigger refinement stage
                with st.spinner("Refining your problem statement..."):
                    for event_type, data in run_stage1_refinement(prompt):
                        if event_type == "refinement":
                            st.session_state.refinement_data = data
                            st.session_state.refined_input = data["refined_statement"]
                st.session_state.workflow_stage = "refinement"
                st.rerun()


def format_classification_name(classification: str) -> str:
    """Format classification for display."""
    return classification.replace("_", " ").title()


# --------------------
# DOCUMENTATION PAGES
# --------------------

def show_doc_prioritization():
    """Documentation page for Prioritization agent."""
    if st.button("← Back to Chat"):
        st.session_state.current_view = "chat"
        st.rerun()

    st.title("Prioritization Agent")
    st.markdown("*Help with trade-off decisions and competing priorities*")

    st.markdown("---")

    st.header("What It Solves")
    st.markdown("""
- "Should we build A or B first?"
- Competing stakeholder requests with no clear winner
- Resource allocation decisions when everything feels urgent
- Breaking deadlocks between teams with different priorities
    """)

    st.header("Frameworks Explained")

    st.subheader("RICE Scoring")
    st.markdown("""
RICE provides a **quantitative score** to compare options objectively. Each factor is scored and combined into a single number.

| Factor | What It Measures | How to Score |
|--------|------------------|--------------|
| **Reach** | How many users/customers affected per quarter? | Estimate a number (e.g., 10,000 users) |
| **Impact** | How much will it move the needle per user? | 3 = massive, 2 = high, 1 = medium, 0.5 = low, 0.25 = minimal |
| **Confidence** | How sure are you about these estimates? | 100% = high, 80% = medium, 50% = low |
| **Effort** | Person-months to complete | Estimate in person-months (e.g., 2) |

**Formula:** `RICE Score = (Reach × Impact × Confidence) / Effort`

**Best for:** Comparing 3+ options quantitatively, especially when you need to justify decisions with data.
    """)

    st.subheader("MoSCoW Prioritization")
    st.markdown("""
MoSCoW categorizes features into **four buckets** to negotiate scope with stakeholders. It's not about scoring—it's about forcing hard conversations about what's truly essential.

| Category | Definition | Rule of Thumb |
|----------|------------|---------------|
| **Must Have** | Without this, the release is a failure. Non-negotiable. | Should be ~60% of effort |
| **Should Have** | Important but not critical. Painful to leave out. | ~20% of effort |
| **Could Have** | Nice to have. Include if time permits. | ~20% of effort |
| **Won't Have** | Explicitly out of scope for this release. | Document for later |

**Best for:** Scope negotiations, release planning, getting stakeholder alignment on trade-offs.

**Key insight:** The power is in "Won't Have"—explicitly agreeing what you're NOT doing prevents scope creep.
    """)

    st.subheader("Value vs Effort Matrix (2×2)")
    st.markdown("""
A quick visual tool that plots options on two axes. Draw a 2×2 grid and place each option:

```
        High Value
             │
   Quick     │    Big Bets
   Wins ★    │    (validate first)
─────────────┼─────────────
   Fill-ins  │    Money Pit
   (depri)   │    (avoid)
             │
        Low Value
    Low Effort ──────── High Effort
```

| Quadrant | Action |
|----------|--------|
| **Quick Wins** (high value, low effort) | Do these first |
| **Big Bets** (high value, high effort) | Validate assumptions before committing |
| **Fill-ins** (low value, low effort) | Do if you have spare capacity |
| **Money Pit** (low value, high effort) | Avoid or redesign |

**Best for:** Fast prioritization in workshops, visual communication with stakeholders.
    """)

    st.subheader("Weighted Scoring")
    st.markdown("""
When different criteria matter differently to your business, assign **weights** to each criterion and score options against them.

**Example Setup:**
| Criterion | Weight | Option A | Option B |
|-----------|--------|----------|----------|
| Revenue Impact | 40% | 8 | 6 |
| Strategic Fit | 30% | 7 | 9 |
| Technical Risk | 20% | 5 | 8 |
| Time to Market | 10% | 9 | 4 |
| **Weighted Score** | | **7.1** | **7.0** |

**Best for:** When stakeholders disagree on what matters most—forces explicit conversation about weights.
    """)

    st.header("How the Agent Works")
    st.markdown("""
1. **Restates the core trade-off** in clear terms so everyone agrees on what's being decided
2. **Selects the most appropriate framework** based on your situation (number of options, need for quantitative data, stakeholder dynamics)
3. **Applies the framework** with specific scores, categories, or placements
4. **Provides a concrete recommendation** (not vague "it depends")
5. **Identifies assumptions** you should validate before committing
    """)

    st.header("What You Get")
    st.markdown("""
- **Framework comparison tables** with your options scored/categorized
- **Clear recommendation** with reasoning
- **Sensitivity analysis** showing what would change the answer
- **Validation questions** to pressure-test with stakeholders
    """)


def show_doc_problem_space():
    """Documentation page for Problem Space agent."""
    if st.button("← Back to Chat"):
        st.session_state.current_view = "chat"
        st.rerun()

    st.title("Problem Space Agent")
    st.markdown("*Validate whether problems actually exist and matter to users*")

    st.markdown("---")

    st.header("What It Solves")
    st.markdown("""
- "Is this actually a problem worth solving?"
- Validating user pain points before building solutions
- Avoiding the trap of solutions in search of problems
- Distinguishing real pain from assumed pain
- Deciding whether to invest in deeper discovery
    """)

    st.header("Why This Matters")
    st.markdown("""
Most failed products solve problems that either:
1. **Don't actually exist** (we assumed users struggle, but they don't)
2. **Exist but don't matter enough** (it's annoying, but not worth paying/switching for)
3. **Have good-enough workarounds** (users already solved it themselves)

This agent helps you **stress-test your problem hypothesis** before committing resources to solutions.
    """)

    st.header("The Analysis Framework")

    st.subheader("1. Problem Existence Analysis")
    st.markdown("""
The agent examines evidence **for** and **against** the problem being real:

| Evidence Type | For (Problem Exists) | Against (Problem Overstated) |
|---------------|----------------------|------------------------------|
| **User behavior** | Users complain, abandon tasks, seek alternatives | Users complete tasks, low support tickets |
| **Market signals** | Competitors solving this, willingness to pay | No competitors, free workarounds exist |
| **Quantitative data** | High drop-off rates, time-on-task metrics | Metrics look healthy |
| **Qualitative data** | Interviews reveal frustration | Users say "it's fine" |

**Key question:** Is there evidence beyond your intuition that this problem exists?
    """)

    st.subheader("2. Severity Assessment")
    st.markdown("""
Not all problems are worth solving. The agent evaluates severity across three dimensions:

| Dimension | Questions to Answer |
|-----------|---------------------|
| **Frequency** | How often do users encounter this? Daily? Monthly? Once? |
| **Intensity** | When it happens, how painful is it? Mild annoyance or showstopper? |
| **Alternatives** | What do users do today? Is the workaround "good enough"? |

**Severity Matrix:**
```
        High Frequency
              │
   Chronic    │    Acute
   Pain ★     │    Crisis ★
──────────────┼──────────────
   Paper      │    Non-
   Cuts       │    Issue
              │
        Low Frequency
    Low Intensity ─── High Intensity
```

**Worth solving:** Chronic Pain (frequent + intense) and Acute Crisis (rare but severe)
**Probably not worth solving:** Paper Cuts (frequent but mild) and Non-Issues (rare and mild)
    """)

    st.subheader("3. Validation Experiments")
    st.markdown("""
The agent suggests experiments to **test your assumptions** before building:

| Experiment Type | What It Tests | Example |
|-----------------|---------------|---------|
| **Problem Interview** | Does the problem exist? | "Tell me about the last time you tried to X..." |
| **Fake Door Test** | Is there demand? | Landing page with "Sign up for early access" |
| **Concierge MVP** | Can we solve it manually? | Do the task by hand for 10 users |
| **Wizard of Oz** | Will users engage with the solution? | Human behind the curtain pretending to be software |
| **Smoke Test** | Will people pay? | Pre-order or waitlist with commitment |

Each experiment should have:
- **Hypothesis:** What you're testing
- **Success criteria:** What result would validate/invalidate
- **Sample size:** How many responses you need
    """)

    st.header("How the Agent Works")
    st.markdown("""
1. **Makes educated guesses** about whether the problem exists and why
2. **Analyzes evidence** you've provided for and against
3. **Assesses severity** using frequency, intensity, and alternatives
4. **Generates specific validation experiments** with success criteria
5. **Provides a confidence rating** on problem validity
    """)

    st.header("What You Get")
    st.markdown("""
- **Confidence rating** on whether the problem is real and worth solving
- **Evidence gap analysis** showing what you know vs. what you're assuming
- **Severity assessment** with frequency/intensity/alternatives breakdown
- **Validation experiments** with specific questions and success criteria
- **Decision recommendation:** Invest, pivot, or gather more evidence
    """)


def show_doc_context_mapping():
    """Documentation page for Context Mapping agent."""
    if st.button("← Back to Chat"):
        st.session_state.current_view = "chat"
        st.rerun()

    st.title("Context Mapping Agent")
    st.markdown("*Map unfamiliar domains, stakeholders, and organizational dynamics*")

    st.markdown("---")

    st.header("What It Solves")
    st.markdown("""
- Joining a new team, company, or domain and needing to get up to speed fast
- Understanding unfamiliar stakeholder dynamics and who really makes decisions
- Navigating organizational politics without stepping on landmines
- Entering a new market or industry with domain-specific knowledge gaps
- Figuring out "how things really work around here"
    """)

    st.header("Why This Matters")
    st.markdown("""
PMs often fail not because of bad product decisions, but because they **misread the context**:
- Proposed changes that violated unwritten rules
- Missed the real decision-maker (it wasn't the person with the title)
- Used terminology incorrectly and lost credibility
- Didn't understand historical context ("we tried that in 2019...")

This agent helps you **build a mental map** of the territory before you start making moves.
    """)

    st.header("The Analysis Framework")

    st.subheader("1. Stakeholder Mapping")
    st.markdown("""
The agent maps key players using an **Influence vs. Interest** matrix:

```
        High Influence
              │
   Key        │    Keep
   Players ★  │    Satisfied
   (partner)  │    (inform)
──────────────┼──────────────
   Keep       │    Monitor
   Informed   │    (minimal)
   (update)   │
              │
        Low Influence
    Low Interest ─── High Interest
```

For each stakeholder, the agent identifies:

| Attribute | What It Means |
|-----------|---------------|
| **Role** | Their formal position and responsibilities |
| **Motivation** | What they actually care about (often different from their role) |
| **Influence** | Their ability to approve, block, or accelerate your work |
| **Interest** | How much they care about your specific area |
| **Engagement** | How you should interact with them (partner, inform, consult) |

**Key insight:** The org chart lies. The real decision-maker might be the "technical lead" who the VP always defers to, or the EA who controls the calendar.
    """)

    st.subheader("2. Domain Concept Glossary")
    st.markdown("""
Every domain has terminology that insiders use fluently but newcomers stumble over:

| Term Type | Examples | Why It Matters |
|-----------|----------|----------------|
| **Acronyms** | ARR, DAU, LTV, CAC | Using these wrong signals you're an outsider |
| **Jargon** | "Sprint", "Epic", "Spike" | Different orgs use the same words differently |
| **Domain terms** | Medical: "contraindication"; Finance: "mark to market" | Industry-specific knowledge |
| **Internal terms** | "The Platform", "Project Phoenix" | Company-specific references |

The agent creates a glossary with:
- **Term:** The word or phrase
- **Definition:** What it means in this context
- **Business relevance:** Why it matters for your work
- **Related terms:** Connected concepts
    """)

    st.subheader("3. Hidden Dynamics")
    st.markdown("""
The agent surfaces the **unwritten rules** that govern how things really work:

| Dynamic Type | Questions to Uncover |
|--------------|----------------------|
| **Real decision-makers** | Who does the "decision-maker" actually defer to? |
| **Historical context** | What was tried before? Why did it fail? Who was blamed? |
| **Political sensitivities** | What topics are off-limits? Who has beef with whom? |
| **Sacred cows** | What can never be changed, questioned, or killed? |
| **Power shifts** | Who is rising? Who is falling? Where is the org heading? |

**Example hidden dynamics:**
- "The CTO technically owns this, but Sarah in Platform actually decides"
- "Don't mention the 2020 reorg—people are still bitter"
- "The CEO's pet project is untouchable, even though it's failing"
    """)

    st.subheader("4. Learning Roadmap")
    st.markdown("""
The agent creates a sequenced plan to build context efficiently:

| Timeframe | Focus | Activities |
|-----------|-------|------------|
| **Week 1** | Orientation | Meet key stakeholders, learn terminology, understand current state |
| **Week 2** | Depth | Shadow users, review past decisions, understand metrics |
| **Week 3+** | Integration | Start contributing, validate your mental model, fill gaps |

Each phase includes:
- **People to meet** (and what to ask them)
- **Documents to read** (and what to look for)
- **Questions to answer** (to validate your understanding)
    """)

    st.header("How the Agent Works")
    st.markdown("""
1. **Analyzes your situation** to understand what context you need
2. **Maps stakeholders** with influence, interest, and motivations
3. **Identifies domain terminology** you'll need to learn
4. **Surfaces hidden dynamics** and political considerations
5. **Creates a learning roadmap** with prioritized activities
    """)

    st.header("What You Get")
    st.markdown("""
- **Stakeholder map** with engagement priorities and motivations
- **Domain glossary** with key terms and their business relevance
- **Hidden dynamics analysis** surfacing unwritten rules
- **Learning roadmap** with week-by-week activities
- **Validation questions** to test your understanding with insiders
    """)


def show_doc_constraints():
    """Documentation page for Constraints agent."""
    if st.button("← Back to Chat"):
        st.session_state.current_view = "chat"
        st.rerun()

    st.title("Constraints Agent")
    st.markdown("*Surface hidden limitations and blockers*")

    st.markdown("---")

    st.header("What It Solves")
    st.markdown("""
- "Engineering says this can't be done—but why exactly?"
- Hidden blockers that keep killing your initiatives
- Understanding what's actually negotiable vs. truly fixed
- Getting unstuck when you keep hitting walls
- Translating "no" into "yes, if..."
    """)

    st.header("Why This Matters")
    st.markdown("""
When someone says "we can't do that," there's usually a hidden constraint. Understanding **why** unlocks new options:

| What They Say | Possible Hidden Constraint | Possible Path Forward |
|---------------|---------------------------|----------------------|
| "That's not possible" | Architecture limitation | Redesign the approach |
| "We don't have bandwidth" | Competing priorities | Negotiate scope/timeline |
| "Legal won't approve" | Specific regulation concern | Find compliant alternative |
| "We tried that before" | Historical failure | Understand what's different now |

The goal isn't to bulldoze through constraints—it's to **understand them well enough to work with them**.
    """)

    st.header("Constraint Categories")

    st.subheader("Technical Constraints")
    st.markdown("""
Limitations imposed by your technology stack, architecture, or engineering realities:

| Constraint | Example | Negotiability |
|------------|---------|---------------|
| **Architecture limits** | "Our monolith can't handle real-time updates" | Medium - may require refactoring |
| **Legacy systems** | "We can't touch that code—nobody understands it" | Low - but can often work around |
| **Performance** | "That query would take 10 minutes" | Medium - optimization possible |
| **Security** | "We can't store that data in plain text" | Very Low - usually non-negotiable |
| **Technical debt** | "We'd have to fix X, Y, and Z first" | Medium - can often sequence differently |
    """)

    st.subheader("Resource Constraints")
    st.markdown("""
Limitations on people, money, and time:

| Constraint | Example | Negotiability |
|------------|---------|---------------|
| **Team capacity** | "We only have 2 engineers" | Medium - can hire, borrow, outsource |
| **Budget** | "There's no money for new tools" | Medium - depends on business case |
| **Timeline** | "We need this by Q3" | Varies - understand why the deadline exists |
| **Skills** | "Nobody here knows ML" | Medium - train, hire, or buy |
| **Attention** | "Leadership is focused on Project X" | High - timing and framing matter |
    """)

    st.subheader("Organizational Constraints")
    st.markdown("""
Limitations from how your company operates:

| Constraint | Example | Negotiability |
|------------|---------|---------------|
| **Approval processes** | "Legal review takes 6 weeks" | Low - but can start earlier |
| **Cross-team dependencies** | "Platform team owns that" | Medium - relationship dependent |
| **Org structure** | "That's not our team's scope" | Medium - can propose reorg |
| **Decision rights** | "VP needs to sign off" | Low - but can prepare the case |
| **Culture** | "We don't do things that way here" | Low - requires change management |
    """)

    st.subheader("External Constraints")
    st.markdown("""
Limitations from outside your organization:

| Constraint | Example | Negotiability |
|------------|---------|---------------|
| **Regulations** | "GDPR requires consent" | Very Low - compliance is mandatory |
| **Vendor dependencies** | "Stripe doesn't support that" | Low - but alternatives may exist |
| **Market timing** | "Conference is in 3 months" | Very Low - external deadline |
| **Customer contracts** | "We promised X in the SLA" | Low - contractual obligation |
| **Partner requirements** | "Apple requires X for App Store" | Very Low - platform rules |
    """)

    st.subheader("Historical Constraints")
    st.markdown("""
Limitations from past decisions and experiences:

| Constraint | Example | Negotiability |
|------------|---------|---------------|
| **Past failures** | "We tried that in 2019, it flopped" | High - circumstances may have changed |
| **Commitments** | "We told customers we'd never do X" | Medium - may need to grandfather |
| **Sunk costs** | "We invested $2M in the current system" | Medium - beware sunk cost fallacy |
| **Precedent** | "If we do this for them, everyone will want it" | Medium - can create explicit policies |
    """)

    st.header("The Action Framework")
    st.markdown("""
For each constraint, the agent recommends one of four actions:

| Action | When to Use | Example |
|--------|-------------|---------|
| **Accept** | Constraint is real and unchangeable | "HIPAA requires encryption—build it in" |
| **Negotiate** | Constraint is soft or has wiggle room | "Can we get 3 engineers instead of 2 if we cut scope?" |
| **Escalate** | Constraint needs higher authority to remove | "We need VP approval to change the timeline" |
| **Pivot** | Constraint makes current approach unviable | "Given the API limits, let's try a different architecture" |
    """)

    st.header("How the Agent Works")
    st.markdown("""
1. **Identifies likely constraints** based on your situation (with confidence levels)
2. **Categorizes each constraint** by type (technical, resource, organizational, etc.)
3. **Assesses severity** and how much it blocks your path
4. **Evaluates negotiability** based on constraint type and context
5. **Recommends specific actions** for each constraint
    """)

    st.header("What You Get")
    st.markdown("""
- **Constraint inventory** with all identified blockers
- **Severity assessment** showing which constraints matter most
- **Negotiability ratings** distinguishing hard limits from soft ones
- **Action recommendations** for each constraint (accept, negotiate, escalate, pivot)
- **Conversation starters** for discussing constraints with stakeholders
    """)


def show_doc_solution_validation():
    """Documentation page for Solution Validation agent."""
    if st.button("← Back to Chat"):
        st.session_state.current_view = "chat"
        st.rerun()

    st.title("Solution Validation Agent")
    st.markdown("*Stress-test ideas before committing resources*")

    st.markdown("---")

    st.header("What It Solves")
    st.markdown("""
- "Will this solution actually work, or are we building the wrong thing?"
- Stress-testing ideas before committing engineering resources
- Identifying the riskiest assumptions that could sink the project
- Deciding what to validate first when everything feels uncertain
- Avoiding expensive failures by testing cheap and early
    """)

    st.header("Why This Matters")
    st.markdown("""
Most product failures aren't bad execution—they're **building the wrong thing**. Teams spend months building features that:
- Users don't actually want (value risk)
- Users can't figure out how to use (usability risk)
- Engineering can't actually build as specced (feasibility risk)
- The business can't support profitably (viability risk)

The goal is to **identify and address the biggest risks early**, when changes are cheap.
    """)

    st.header("The Four Product Risks")
    st.caption("Framework from Marty Cagan's 'Inspired'")

    st.subheader("1. Value Risk")
    st.markdown("""
**The Question:** Will customers actually buy or use this?

This is the most common reason products fail. We build things nobody wants.

| Signal | High Risk | Low Risk |
|--------|-----------|----------|
| **User demand** | "That would be nice" (polite interest) | "When can I get this?" (active demand) |
| **Willingness to pay** | "I'd use it if it's free" | "I'd pay $X for this" |
| **Switching cost** | Happy with current solution | Actively frustrated |
| **Problem severity** | Nice-to-have | Hair-on-fire problem |

**Validation approaches:**
- **Problem interviews:** "Tell me about the last time you dealt with X..."
- **Landing page test:** Would people click "Sign up for early access"?
- **Fake door test:** Add a button for the feature, see if people click
- **Pre-orders:** Would people put down money before it exists?
    """)

    st.subheader("2. Usability Risk")
    st.markdown("""
**The Question:** Can users figure out how to use this?

Even valuable features fail if users can't navigate them.

| Signal | High Risk | Low Risk |
|--------|-----------|----------|
| **Complexity** | Multi-step, many options | Single action, obvious path |
| **Novelty** | New interaction patterns | Familiar UX conventions |
| **User sophistication** | Non-technical users | Power users |
| **Error cost** | Mistakes are expensive | Easy to undo |

**Validation approaches:**
- **Prototype testing:** Watch 5 users try to complete a task
- **First-click tests:** Where do users click first? Is it right?
- **Comprehension tests:** Show the UI—can they explain what it does?
- **Wizard of Oz:** Human behind the scenes, test the interaction model
    """)

    st.subheader("3. Feasibility Risk")
    st.markdown("""
**The Question:** Can engineering actually build this?

Sometimes what we spec is harder (or impossible) to build than we assumed.

| Signal | High Risk | Low Risk |
|--------|-----------|----------|
| **Technical novelty** | Never done before | Proven patterns |
| **Dependencies** | Relies on external systems | Self-contained |
| **Performance needs** | Real-time, massive scale | Standard requirements |
| **Team experience** | New domain for the team | Team has done this before |

**Validation approaches:**
- **Spike:** Time-boxed technical investigation (1-2 days)
- **Architecture review:** Have senior engineers assess feasibility
- **Prototype:** Build the hardest part first
- **Reference check:** Has anyone else built something similar?
    """)

    st.subheader("4. Viability Risk")
    st.markdown("""
**The Question:** Does this work for the business?

Even if users love it and we can build it, it might not be viable.

| Signal | High Risk | Low Risk |
|--------|-----------|----------|
| **Unit economics** | Costs more to serve than we earn | Healthy margins |
| **Legal/compliance** | Regulatory gray area | Clearly compliant |
| **Strategic fit** | Distracts from core business | Aligns with strategy |
| **Stakeholder support** | Key stakeholders oppose | Broad support |

**Validation approaches:**
- **Financial modeling:** Does this make money at scale?
- **Legal review:** Can we do this compliantly?
- **Stakeholder interviews:** Who needs to say yes?
- **Competitive analysis:** How will competitors respond?
    """)

    st.header("Risk Assessment Matrix")
    st.markdown("""
The agent rates each risk dimension and helps you prioritize:

| Risk | Rating | Confidence | Priority |
|------|--------|------------|----------|
| Value | High | Low | **Validate First** |
| Usability | Medium | Medium | Second |
| Feasibility | Low | High | Monitor |
| Viability | Medium | Medium | Third |

**Priority rule:** Address high-risk, low-confidence items first—these are where you're most likely to be wrong in ways that matter.
    """)

    st.header("How the Agent Works")
    st.markdown("""
1. **Analyzes your solution** against all four risk dimensions
2. **Rates each risk** as High/Medium/Low with reasoning
3. **Assesses your confidence** in each rating
4. **Identifies the highest-priority risk** to validate first
5. **Recommends specific experiments** with success criteria
    """)

    st.header("What You Get")
    st.markdown("""
- **Risk assessment matrix** with ratings for all four dimensions
- **Confidence levels** showing where you have evidence vs. assumptions
- **Priority recommendation** for which risk to tackle first
- **Validation experiments** with specific methods and success criteria
- **Kill criteria:** What result would tell you to abandon this approach?
    """)


# --------------------
# STAGE HANDLERS
# --------------------

def handle_input_stage():
    """Handle initial input collection."""
    # Show any previous messages
    display_chat_history()

    # Show welcome instructions only when no messages yet
    if not st.session_state.messages:
        show_welcome()
        st.markdown("")  # Add spacing before chat input

    # Chat input
    if prompt := st.chat_input("Describe your PM problem..."):
        st.session_state.original_input = prompt
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Run refinement
        with st.spinner("Refining your problem statement..."):
            for event_type, data in run_stage1_refinement(prompt):
                if event_type == "refinement":
                    st.session_state.refinement_data = data
                    st.session_state.refined_input = data["refined_statement"]

        st.session_state.workflow_stage = "refinement"
        st.rerun()


def handle_refinement_stage():
    """Checkpoint 1: Show refinement and get confirmation."""
    display_chat_history()

    with st.chat_message("assistant"):
        # Checkpoint header with icon
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: #dbeafe;
                            display: flex; align-items: center; justify-content: center; font-size: 22px;">
                    ✏️
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 600;">Problem Refinement</div>
                    <div style="font-size: 13px; color: #6b7280;">Review and edit the refined problem statement</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Side by side comparison with styled cards
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
                <div style="font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: 6px;">
                    Original
                </div>
            """, unsafe_allow_html=True)
            st.info(st.session_state.original_input)

        with col2:
            st.markdown("""
                <div style="font-size: 12px; font-weight: 600; color: #3b82f6; text-transform: uppercase; margin-bottom: 6px;">
                    Refined (editable)
                </div>
            """, unsafe_allow_html=True)
            refined = st.text_area(
                "Edit if needed:",
                value=st.session_state.refined_input,
                height=100,
                key="refined_input_edit",
                label_visibility="collapsed"
            )

        st.markdown("")  # Spacing

        # Show what was improved
        if st.session_state.refinement_data.get("improvements"):
            with st.expander("💡 What I changed", expanded=False):
                for improvement in st.session_state.refinement_data["improvements"]:
                    st.markdown(f"- {improvement}")

        # Show initial soft guesses from refinement
        if st.session_state.refinement_data.get("soft_guesses"):
            with st.expander("🔮 Initial assumptions spotted", expanded=False):
                for guess in st.session_state.refinement_data["soft_guesses"]:
                    st.markdown(f"- {guess}")

        st.markdown("")  # Spacing before buttons

        # Buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("✓ Confirm & Continue", type="primary", use_container_width=True):
                st.session_state.refined_input = refined

                # Run classification
                with st.spinner("Classifying your problem..."):
                    for event_type, data in run_stage2_classification(refined):
                        if event_type == "classification":
                            st.session_state.classification_data = data

                st.session_state.workflow_stage = "classification"
                st.rerun()

        with col2:
            if st.button("↺ Start Over", use_container_width=True):
                reset_workflow()
                st.rerun()


CLASSIFICATION_ICONS = {
    "prioritization": "⚖️",
    "problem_space": "🔍",
    "context_mapping": "🗺️",
    "constraints": "🚧",
    "solution_validation": "✅",
}


def handle_classification_stage():
    """Checkpoint 2: Show classification and allow override."""
    display_chat_history()

    with st.chat_message("assistant"):
        # Checkpoint header with icon
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: #dcfce7;
                            display: flex; align-items: center; justify-content: center; font-size: 22px;">
                    🎯
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 600;">Agent Selection</div>
                    <div style="font-size: 13px; color: #6b7280;">Confirm or change the recommended approach</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        data = st.session_state.classification_data
        classification = data["classification"]
        reasoning = data["reasoning"]
        alternatives = data.get("alternatives", [])

        # Show recommended classification with icon
        icon = CLASSIFICATION_ICONS.get(classification, "📋")
        st.markdown(f"""
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="font-size: 20px;">{icon}</span>
                    <span style="font-weight: 600; color: #166534;">Recommended: {format_classification_name(classification)}</span>
                </div>
                <div style="color: #15803d; font-size: 14px;">{reasoning}</div>
            </div>
        """, unsafe_allow_html=True)

        # Build options for selectbox
        all_options = [classification] + [alt for alt in alternatives if alt != classification]
        all_categories = ["prioritization", "problem_space", "context_mapping", "constraints", "solution_validation"]

        # Add remaining categories not in alternatives
        for cat in all_categories:
            if cat not in all_options:
                all_options.append(cat)

        # Format for display with icons
        option_labels = {opt: f"{CLASSIFICATION_ICONS.get(opt, '📋')} {format_classification_name(opt)}" for opt in all_options}

        # Show alternatives if any
        if alternatives:
            with st.expander("🔄 Other possible approaches", expanded=False):
                for alt in alternatives:
                    alt_icon = CLASSIFICATION_ICONS.get(alt, "📋")
                    st.markdown(f"- {alt_icon} **{format_classification_name(alt)}**")

        # Override selector
        selected = st.selectbox(
            "Select approach:",
            options=all_options,
            format_func=lambda x: option_labels.get(x, x),
            index=0,
            key="classification_select"
        )

        st.markdown("")  # Spacing before buttons

        # Buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("✓ Confirm & Continue", type="primary", use_container_width=True):
                # Update classification if changed
                st.session_state.classification_data["classification"] = selected

                # Run soft guesses extraction
                with st.spinner("Extracting key assumptions..."):
                    for event_type, data in run_stage3_soft_guesses(
                        st.session_state.refined_input,
                        selected
                    ):
                        if event_type == "soft_guesses":
                            st.session_state.soft_guesses_data = data

                st.session_state.workflow_stage = "soft_guesses"
                st.rerun()

        with col2:
            if st.button("← Back", use_container_width=True):
                st.session_state.workflow_stage = "refinement"
                st.rerun()


def handle_soft_guesses_stage():
    """Checkpoint 3: Show soft guesses and get validation."""
    display_chat_history()

    with st.chat_message("assistant"):
        # Checkpoint header with icon
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: #fef3c7;
                            display: flex; align-items: center; justify-content: center; font-size: 22px;">
                    🔮
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 600;">Validate Assumptions</div>
                    <div style="font-size: 13px; color: #6b7280;">Confirm or correct before full analysis</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        guesses = st.session_state.soft_guesses_data

        if not guesses:
            st.markdown("""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1rem; text-align: center;">
                    <span style="font-size: 24px;">✨</span>
                    <div style="font-weight: 500; color: #166534; margin-top: 0.5rem;">No major assumptions detected</div>
                    <div style="font-size: 13px; color: #15803d;">Ready to proceed with analysis!</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Create a form for each guess
            confirmed = []

            for i, guess in enumerate(guesses):
                confidence = guess.get("confidence", "Medium")
                confidence_style = {
                    "High": ("🟢", "#dcfce7", "#166534"),
                    "Medium": ("🟡", "#fef3c7", "#92400e"),
                    "Low": ("🔴", "#fee2e2", "#991b1b"),
                }.get(confidence, ("🟡", "#fef3c7", "#92400e"))

                with st.container():
                    # Card-like container for each assumption
                    st.markdown(f"""
                        <div style="background: #fafafa; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <span style="font-weight: 600;">{guess.get('topic', 'Assumption')}</span>
                                    <span style="background: {confidence_style[1]}; color: {confidence_style[2]};
                                                 padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px;">
                                        {confidence_style[0]} {confidence}
                                    </span>
                                </div>
                            </div>
                            <div style="margin-top: 0.5rem; color: #374151;">{guess.get('assumption', '')}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if guess.get("reason"):
                            st.caption(f"💡 {guess['reason']}")
                    with col2:
                        is_correct = st.checkbox(
                            "Correct",
                            value=True,
                            key=f"guess_{i}"
                        )

                    # If not correct, allow correction
                    if not is_correct:
                        correction = st.text_input(
                            "What's the correct information?",
                            key=f"correction_{i}",
                            placeholder="Enter the correct information..."
                        )
                        if correction:
                            confirmed.append({
                                "topic": guess.get("topic", "Correction"),
                                "assumption": correction,
                                "confidence": "High",
                                "reason": "Corrected by user"
                            })
                    else:
                        confirmed.append(guess)

                    st.markdown("")  # Spacing between cards

            st.session_state.confirmed_guesses = confirmed

        st.markdown("")  # Spacing before buttons

        # Buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                st.session_state.workflow_stage = "streaming"
                st.rerun()

        with col2:
            if st.button("← Back", use_container_width=True):
                st.session_state.workflow_stage = "classification"
                st.rerun()


def handle_streaming_stage():
    """Stream the specialist output."""
    display_chat_history()

    with st.chat_message("assistant"):
        classification = st.session_state.classification_data["classification"]
        icon = CLASSIFICATION_ICONS.get(classification, "📋")

        # Analysis header
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: #f3e8ff;
                            display: flex; align-items: center; justify-content: center; font-size: 22px;">
                    {icon}
                </div>
                <div>
                    <div style="font-size: 18px; font-weight: 600;">{format_classification_name(classification)} Analysis</div>
                    <div style="font-size: 13px; color: #6b7280;">Generating insights...</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Context summary
        with st.expander("📋 Context Summary", expanded=False):
            st.markdown(f"**Problem:** {st.session_state.refined_input}")
            if st.session_state.confirmed_guesses:
                st.markdown("**Confirmed Assumptions:**")
                for guess in st.session_state.confirmed_guesses:
                    st.markdown(f"- **{guess.get('topic', 'Assumption')}:** {guess.get('assumption', '')}")

        st.markdown("---")

        # Streaming placeholder
        response_placeholder = st.empty()
        full_response = ""

        # Run specialist with streaming
        for event_type, data in run_stage4_specialist(
            st.session_state.refined_input,
            classification,
            st.session_state.confirmed_guesses
        ):
            if event_type == "token":
                full_response += data
                response_placeholder.markdown(full_response + "▌")
            elif event_type == "done":
                response_placeholder.markdown(full_response)
                st.session_state.final_output = full_response

        # Save to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "coordinator": {
                "classification": classification,
                "reasoning": st.session_state.classification_data.get("reasoning", ""),
            }
        })

        st.session_state.workflow_stage = "complete"
        st.rerun()


def handle_complete_stage():
    """Show completed output with option to start new."""
    display_chat_history()

    st.markdown("")  # Spacing

    # Success message and new problem button
    st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white; padding: 1.5rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 28px; margin-bottom: 0.5rem;">✓</div>
            <div style="font-weight: 600;">Analysis Complete</div>
            <div style="opacity: 0.9; font-size: 14px;">Your insights are ready above</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🆕 Start New Problem", type="primary", use_container_width=True):
            reset_workflow()
            st.rerun()


# --------------------
# MAIN ROUTING
# --------------------

# Check current_view first - documentation pages bypass the workflow
view = st.session_state.current_view

if view == "doc_prioritization":
    show_doc_prioritization()
elif view == "doc_problem_space":
    show_doc_problem_space()
elif view == "doc_context_mapping":
    show_doc_context_mapping()
elif view == "doc_constraints":
    show_doc_constraints()
elif view == "doc_solution_validation":
    show_doc_solution_validation()
else:
    # Main chat workflow - render sidebar and header only for chat view
    render_sidebar()

    # Header with title
    st.markdown("""
        <div style="margin-bottom: 0.5rem;">
            <span style="font-size: 28px; font-weight: 700;">PM Brainstorming Assistant</span>
        </div>
    """, unsafe_allow_html=True)
    st.caption("A thinking partner for prioritization decisions and discovery challenges")

    stage = st.session_state.workflow_stage

    # Show progress indicator when workflow has started
    if stage != "input":
        st.markdown("")  # spacing
        render_progress_indicator()
        st.markdown("")  # spacing

    if stage == "input":
        handle_input_stage()
    elif stage == "refinement":
        handle_refinement_stage()
    elif stage == "classification":
        handle_classification_stage()
    elif stage == "soft_guesses":
        handle_soft_guesses_stage()
    elif stage == "streaming":
        handle_streaming_stage()
    elif stage == "complete":
        handle_complete_stage()
