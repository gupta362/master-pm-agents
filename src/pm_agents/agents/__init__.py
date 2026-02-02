"""PM specialist agents."""

# Prioritization agent (existing)
from .prioritization import PROMPT as PRIORITIZATION_PROMPT
from .prioritization import run_agent as run_prioritization
from .prioritization import stream_agent as stream_prioritization

# Problem Space agent (new - validates if problems exist and matter)
from .problem_space import PROMPT as PROBLEM_SPACE_PROMPT
from .problem_space import run_agent as run_problem_space
from .problem_space import stream_agent as stream_problem_space

# Context Mapping agent (new - maps domains and stakeholders)
from .context_mapping import PROMPT as CONTEXT_MAPPING_PROMPT
from .context_mapping import run_agent as run_context_mapping
from .context_mapping import stream_agent as stream_context_mapping

# Constraints agent (new - surfaces hidden limitations)
from .constraints import PROMPT as CONSTRAINTS_PROMPT
from .constraints import run_agent as run_constraints
from .constraints import stream_agent as stream_constraints

# Solution Validation agent (new - validates against 4 risks)
from .solution_validation import PROMPT as SOLUTION_VALIDATION_PROMPT
from .solution_validation import run_agent as run_solution_validation
from .solution_validation import stream_agent as stream_solution_validation

# Note: discovery.py is deprecated and will be removed after verification
# The 4 new agents above replace the single discovery agent with specialized capabilities

__all__ = [
    # Prioritization
    "PRIORITIZATION_PROMPT",
    "run_prioritization",
    "stream_prioritization",
    # Problem Space
    "PROBLEM_SPACE_PROMPT",
    "run_problem_space",
    "stream_problem_space",
    # Context Mapping
    "CONTEXT_MAPPING_PROMPT",
    "run_context_mapping",
    "stream_context_mapping",
    # Constraints
    "CONSTRAINTS_PROMPT",
    "run_constraints",
    "stream_constraints",
    # Solution Validation
    "SOLUTION_VALIDATION_PROMPT",
    "run_solution_validation",
    "stream_solution_validation",
]
