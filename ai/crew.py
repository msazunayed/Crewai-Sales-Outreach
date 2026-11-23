import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, DirectoryReadTool, FileReadTool
from tools import SentimentAnalysisTool

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
INSTR = os.path.join(BASE, "instructions")
INSTR_HINT = (f"\nInstruction files live in this folder: {INSTR}. First list that directory with the "
              "directory tool, then read the relevant files with the file reader using their full paths.")


def build_crew(task_callback=None) -> Crew:
    llm = LLM(model=os.getenv("MODEL", "gpt-4o-mini"))

    search_tool = SerperDevTool()
    directory_read_tool = DirectoryReadTool()  # no fixed directory: Groq rejects the empty-args schema
    file_read_tool = FileReadTool()
    sentiment_tool = SentimentAnalysisTool()

    sales_rep = Agent(
        role="Sales Representative",
        goal="Identify high-value leads that match our ideal customer profile",
        backstory=("As a member of the dynamic sales team at CrewAI, you scour the digital landscape "
                   "for leads that fit our ideal customer profile. You research each company thoroughly "
                   "and rely on evidence, not guesses."),
        tools=[search_tool, directory_read_tool, file_read_tool],
        llm=llm, allow_delegation=False, verbose=True,
    )

    lead_sales_rep = Agent(
        role="Lead Sales Representative",
        goal="Nurture leads with personalized, compelling communications",
        backstory=("Within the vibrant sales team at CrewAI, you excel at turning insights into outreach "
                   "that resonates. You connect our solutions to what each lead has just achieved."),
        tools=[directory_read_tool, file_read_tool, sentiment_tool],
        llm=llm, allow_delegation=False, verbose=True,
    )

    lead_profiling = Task(
        description=(
            "Research and analyse {lead_name}, a company in {industry}. Key decision maker: "
            "{decision_maker} ({position}). Recent milestone: {milestone}.\n"
            "Use web search plus the instruction files (company size guidelines) to build a detailed profile."
            + INSTR_HINT
        ),
        expected_output=(
            "A markdown report with sections: Company Background, Key Decision-Makers, Recent Milestones, "
            "Identified Needs, How Our Solutions Add Value, Suggested Engagement Strategy."
        ),
        agent=sales_rep,
        output_file=os.path.join(OUT, "lead_profile.md"),
    )

    personalized_outreach = Task(
        description=(
            "Using the lead profile, create a personalized outreach campaign for {decision_maker} "
            "({position}) at {lead_name}, addressing the milestone: {milestone}, and how our solutions "
            "support their goals. Follow the outreach guidelines in the instructions folder, then run the "
            "drafts through the sentiment tool and refine until the tone is positive and professional."
            + INSTR_HINT
        ),
        expected_output=(
            "A markdown document with a series of personalized email drafts (subject + body), a compelling "
            "narrative linking our solutions to their achievements, a professional tone aligned with "
            "the company's culture, and the sentiment score for each draft."
        ),
        agent=lead_sales_rep,
        context=[lead_profiling],
        output_file=os.path.join(OUT, "outreach_campaign.md"),
    )

    return Crew(
        agents=[sales_rep, lead_sales_rep],
        tasks=[lead_profiling, personalized_outreach],
        process=Process.sequential,
        task_callback=task_callback,
        verbose=True,
    )
