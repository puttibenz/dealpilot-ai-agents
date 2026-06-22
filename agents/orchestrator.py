"""
DealPilot Orchestrator — ADK SequentialAgent
Connect all agents in a sequential pipeline.
Implementation: Day 4
"""

import warnings
from google.adk.agents import SequentialAgent
from agents.crm_agent import crm_agent
from agents.research_agent import research_agent
from agents.writer_agent import writer_agent
from agents.scheduler_agent import scheduler_agent

# Silence SequentialAgent deprecation warnings to keep logs clean
warnings.filterwarnings("ignore", category=DeprecationWarning)

orchestrator = SequentialAgent(
    name="dealpilot_orchestrator",
    sub_agents=[crm_agent, research_agent, writer_agent, scheduler_agent]
)
