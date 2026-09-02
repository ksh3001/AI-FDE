import { useState, useEffect, useCallback } from "react";
import { getPrompt, listPrompts } from "../api";
import type { PromptDetail, PromptSummary } from "../types";
import { PromptModal } from "./PromptModal";
import { SkillModal } from "./SkillModal";

// Import Markdown skills as raw text
import fdeOperatingModelRaw from "../assets/skills/fde-operating-model.md?raw";
import processLeanDiscoveryRaw from "../assets/skills/process-and-lean-discovery.md?raw";
import dataKnowledgeRaw from "../assets/skills/data-and-knowledge.md?raw";
import domainArchitectureRaw from "../assets/skills/domain-and-architecture.md?raw";
import execCommunicationRaw from "../assets/skills/exec-communication.md?raw";
import trustRiskSecurityRaw from "../assets/skills/trust-risk-security.md?raw";
import specDrivenDeliveryRaw from "../assets/skills/spec-driven-delivery.md?raw";
import aiEngineeringFoundationsRaw from "../assets/skills/ai-engineering-foundations.md?raw";
import azureAiPlatformRaw from "../assets/skills/azure-ai-platform.md?raw";
import agenticSystemsRaw from "../assets/skills/agentic-systems.md?raw";
import deliveryOpsLlmopsRaw from "../assets/skills/delivery-ops-llmops.md?raw";

const SKILL_FILES: Record<string, string> = {
  "FDE Operating Model": fdeOperatingModelRaw,
  "Process & Lean Discovery": processLeanDiscoveryRaw,
  "Data & Knowledge": dataKnowledgeRaw,
  "Domain & Architecture": domainArchitectureRaw,
  "Executive Communication": execCommunicationRaw,
  "Trust, Risk & Security": trustRiskSecurityRaw,
  "Spec-Driven Delivery": specDrivenDeliveryRaw,
  "AI Engineering Foundations": aiEngineeringFoundationsRaw,
  "Azure AI Platform": azureAiPlatformRaw,
  "Agentic Systems": agenticSystemsRaw,
  "Delivery Ops/LLMOps": deliveryOpsLlmopsRaw,
};

type JourneyModule = { id: string; name: string };
const JOURNEY_NAMES: Record<string, string> = {
  "DK-01": "FDE Operating Model",
  "DK-02": "AI Engineering Foundations",
  "DK-03": "Cloud AI Platform",
  "DK-04": "Domain & Architecture",
  "DK-05": "Agentic Systems",
  "DK-06": "Data & Knowledge",
  "DK-07": "Delivery Ops / FinOps",
  "DK-08": "Process & Lean Discovery",
  "DK-09": "Trust, Risk & Security",
  "DK-10": "Spec-Driven Delivery",
};

const JOURNEY_LINKS: Record<string, string> = {
  "DK-01": "day-1",
  "DK-02": "day-4",
  "DK-03": "day-5",
  "DK-04": "day-7",
  "DK-05": "day-9",
  "DK-06": "day-19",
  "DK-07": "day-10",
  "DK-08": "day-18",
  "DK-09": "day-22",
  "DK-10": "day-26",
};

interface StageDetail {
  id: string;
  name: string;
  description: string;
  prompts: string[]; // matching prompt stages/IDs
  skills: string[];
  journey: string[];
  toolLabel: string;
}

const STAGES: StageDetail[] = [
  {
    id: "discover",
    name: "Discover",
    description: "Convert ambiguity into a scoped GenAI use case with success metric and risk boundary.",
    prompts: ["Discovery"],
    skills: ["FDE Operating Model", "Process & Lean Discovery", "Data & Knowledge", "Domain & Architecture", "Executive Communication"],
    journey: ["DK-01", "DK-04", "DK-06", "DK-08"],
    toolLabel: "Discovery artifact",
  },
  {
    id: "frame",
    name: "Frame",
    description: "Establish the situation, complication, question, and answer. Define PRD and Risk Classification.",
    prompts: ["SCQA", "Risk Classification", "PRD"],
    skills: ["Executive Communication", "Process & Lean Discovery", "Domain & Architecture", "Trust, Risk & Security", "Spec-Driven Delivery"],
    journey: ["DK-04", "DK-08", "DK-09"],
    toolLabel: "SCQA, Risk and PRD artifacts",
  },
  {
    id: "design",
    name: "Design",
    description: "Map the domain, specify features, layout C4 architecture, and address security and controls.",
    prompts: ["Domain Model", "Feature Specs", "Architecture", "Security Model", "Decisions (ADR)", "Compliance Controls", "Technical Design", "Lean / DMAIC"],
    skills: ["Domain & Architecture", "AI Engineering Foundations", "Azure AI Platform", "Agentic Systems", "Data & Knowledge", "Trust, Risk & Security", "Spec-Driven Delivery"],
    journey: ["DK-02", "DK-03", "DK-04", "DK-05", "DK-06", "DK-08", "DK-09", "DK-10"],
    toolLabel: "Design and governance pack",
  },
  {
    id: "prove",
    name: "Prove",
    description: "Verify specifications and technical design constraints against actual platform implementation rules.",
    prompts: ["Feature Specs", "Technical Design", "Lean / DMAIC"],
    skills: ["AI Engineering Foundations", "Agentic Systems", "Azure AI Platform", "Spec-Driven Delivery", "Delivery Ops/LLMOps"],
    journey: ["DK-02", "DK-03", "DK-05", "DK-07", "DK-10"],
    toolLabel: "Feature specs, testable acceptance criteria, and technical design",
  },
  {
    id: "assure",
    name: "Assure",
    description: "Audit controls, security models, risks, and governance components before moving to scale.",
    prompts: ["Risk Classification", "Security Model", "Compliance Controls", "Decisions (ADR)", "Technical Design"],
    skills: ["Trust, Risk & Security", "Delivery Ops/LLMOps", "Agentic Systems", "Spec-Driven Delivery", "Data & Knowledge"],
    journey: ["DK-05", "DK-06", "DK-07", "DK-09", "DK-10"],
    toolLabel: "Risk, security, controls and governance artifacts",
  },
  {
    id: "scale",
    name: "Scale",
    description: "Package the verified architecture and controls into a final scalable solution proposal.",
    prompts: ["Solution Proposal", "Lean / DMAIC", "Decisions (ADR)", "Compliance Controls"],
    skills: ["Delivery Ops/LLMOps", "Azure AI Platform", "Executive Communication", "FDE Operating Model", "Spec-Driven Delivery"],
    journey: ["DK-01", "DK-03", "DK-07", "DK-10"],
    toolLabel: "Final Solution Proposal",
  }
];

// Helper to map UI names to prompt stages from API
const PROMPT_STAGE_MAP: Record<string, string> = {
  "Discovery": "discovery",
  "SCQA": "scqa",
  "Risk Classification": "risk_classification",
  "PRD": "prd",
  "Domain Model": "domain_model",
  "Feature Specs": "feature_specs",
  "Architecture": "architecture",
  "Security Model": "security_model",
  "Decisions (ADR)": "decisions",
  "Compliance Controls": "compliance_controls",
  "Technical Design": "technical_design",
  "Lean / DMAIC": "lean_dmaic",
  "Solution Proposal": "solution_proposal",
};

function JourneyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <circle cx="4.5" cy="18" r="2" />
      <circle cx="19.5" cy="6" r="2" />
      <path d="M6.3 16.7 11 11l3 2 4.2-4.7" />
    </svg>
  );
}

function PromptIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M12 5.5c-1.6-1-4-1.5-6.5-1.5A1.5 1.5 0 0 0 4 5.5v13A1.5 1.5 0 0 1 5.5 17c2.5 0 4.9.5 6.5 1.5" />
      <path d="M12 5.5c1.6-1 4-1.5 6.5-1.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 0-1.5-1.5c-2.5 0-4.9.5-6.5 1.5" />
      <path d="M12 5.5v13" />
    </svg>
  );
}

function SkillIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
    </svg>
  );
}

function ToolIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M6.5 3h7l4 4v13a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M13.5 3v4a1 1 0 0 0 1 1h4" />
      <path d="M9 13h6M9 16.5h6" />
    </svg>
  );
}

export function Framework() {
  const [activeStage, setActiveStage] = useState<string>("discover");
  
  // Prompts state
  const [allPrompts, setAllPrompts] = useState<PromptSummary[]>([]);
  const [promptsError, setPromptsError] = useState<string | null>(null);
  
  // Modal state
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [promptDetails, setPromptDetails] = useState<Record<string, PromptDetail>>({});
  const [promptDetailLoading, setPromptDetailLoading] = useState(false);
  const [promptDetailError, setPromptDetailError] = useState<string | null>(null);

  const [selectedSkill, setSelectedSkill] = useState<{title: string, content: string} | null>(null);

  useEffect(() => {
    listPrompts()
      .then((all) => setAllPrompts(all.filter((p) => p.id.startsWith("stage."))))
      .catch((err) => setPromptsError(err instanceof Error ? err.message : "Failed to load prompts."));
  }, []);

  const openPrompt = useCallback(
    (promptName: string) => {
      const stageCode = PROMPT_STAGE_MAP[promptName];
      if (!stageCode) return;
      
      const promptSummary = allPrompts.find(p => p.stage === stageCode);
      if (!promptSummary) {
        setPromptDetailError("Prompt not found in library.");
        // Still open modal to show error
        const fakeId = `missing-${stageCode}`;
        setSelectedPromptId(fakeId);
        return;
      }
      
      const id = promptSummary.id;
      setSelectedPromptId(id);
      
      if (promptDetails[id]) return;
      
      setPromptDetailLoading(true);
      setPromptDetailError(null);
      getPrompt(id)
        .then((detail) => setPromptDetails((prev) => ({ ...prev, [id]: detail })))
        .catch((err) => setPromptDetailError(err instanceof Error ? err.message : "Failed to load this prompt."))
        .finally(() => setPromptDetailLoading(false));
    },
    [allPrompts, promptDetails]
  );

  const openSkill = (skillName: string) => {
    const rawContent = SKILL_FILES[skillName];
    if (rawContent) {
      setSelectedSkill({ title: skillName, content: rawContent });
    }
  };

  const stage = STAGES.find(s => s.id === activeStage)!;
  const selectedPromptObj = selectedPromptId && !selectedPromptId.startsWith("missing-") 
    ? allPrompts.find(p => p.id === selectedPromptId) ?? null 
    : null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12 md:py-16">
      <div className="mb-12">
        <h1 className="font-sans text-3xl font-semibold text-[var(--color-ink)]">Value-to-Scale Framework</h1>
        <p className="mt-3 max-w-3xl text-[var(--color-ink-soft)] leading-relaxed">
          The FDE delivery lifecycle. Move from business evidence to governed, scalable delivery without losing traceability.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-10 items-start">
        {/* Stages Rail */}
        <div className="w-full lg:w-64 shrink-0 flex flex-row lg:flex-col overflow-x-auto lg:overflow-x-visible pb-4 lg:pb-0 gap-2 hide-scrollbar">
          {STAGES.map((s, idx) => {
            const isActive = activeStage === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActiveStage(s.id)}
                className={`relative flex items-center gap-4 rounded-xl px-4 py-3 text-left transition-colors whitespace-nowrap lg:whitespace-normal
                  ${isActive 
                    ? "bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-medium" 
                    : "text-[var(--color-ink-soft)] hover:bg-[var(--color-paper-raised)] hover:text-[var(--color-ink)]"
                  }`}
              >
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-mono
                  ${isActive ? "bg-[var(--color-accent)] text-[var(--color-on-accent)]" : "bg-[var(--color-paper-raised)] text-[var(--color-ink-faint)]"}
                `}>
                  {String(idx + 1).padStart(2, "0")}
                </span>
                <span className="font-sans text-base tracking-tight">{s.name}</span>
                {isActive && (
                  <div className="hidden lg:block absolute -right-4 top-1/2 -mt-2 h-4 w-4 rotate-45 border-r border-t border-[var(--color-accent-soft)] bg-[var(--color-accent-soft)]" />
                )}
              </button>
            );
          })}
        </div>

        {/* Stage Details Pane */}
        <div className="min-w-0 flex-1 rounded-2xl border border-[var(--color-line-strong)] bg-[var(--color-paper-raised)] p-6 md:p-10 shadow-[var(--shadow-panel)]">
          <div className="mb-8">
            <h2 className="font-sans text-2xl font-semibold text-[var(--color-ink)]">{stage.name}</h2>
            <p className="mt-3 text-[var(--color-ink-soft)] leading-relaxed">{stage.description}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Prompts */}
            <div className="flex flex-col gap-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-faint)]">
                <PromptIcon /> Prompts
              </h3>
              <div className="flex flex-col gap-2">
                {stage.prompts.map(p => (
                  <button 
                    key={p} 
                    onClick={() => openPrompt(p)}
                    className="group flex items-center justify-between rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] px-4 py-3 text-left transition-colors hover:border-[var(--color-accent)]"
                  >
                    <span className="text-sm font-medium text-[var(--color-ink)] group-hover:text-[var(--color-accent)]">{p}</span>
                    <span className="text-[var(--color-ink-faint)] group-hover:text-[var(--color-accent)]">→</span>
                  </button>
                ))}
                {promptsError && <p className="text-xs text-[var(--color-failed)]">{promptsError}</p>}
              </div>
            </div>

            {/* Skills */}
            <div className="flex flex-col gap-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-faint)]">
                <SkillIcon /> Skills
              </h3>
              <div className="flex flex-wrap gap-2">
                {stage.skills.map(skill => (
                  <button 
                    key={skill}
                    onClick={() => openSkill(skill)}
                    className="inline-flex items-center rounded-md bg-[var(--color-line)] px-3 py-1.5 text-sm font-medium text-[var(--color-ink-soft)] transition-colors hover:bg-[var(--color-accent-soft)] hover:text-[var(--color-accent)]"
                  >
                    {skill}
                  </button>
                ))}
              </div>
            </div>

            {/* FDE Journey */}
            <div className="flex flex-col gap-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-faint)]">
                <JourneyIcon /> FDE Journey
              </h3>
              <div className="flex flex-col gap-2">
                {stage.journey.map(mod => (
                  <a 
                    key={mod}
                    href={`/portal.html#${JOURNEY_LINKS[mod]}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-center justify-between rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] px-4 py-3 text-left transition-colors hover:border-[var(--color-accent)]"
                  >
                    <div className="flex items-center gap-3">
                      <span className="rounded bg-[var(--color-line-strong)] px-2 py-0.5 font-mono text-xs text-[var(--color-ink)]">{mod}</span>
                      <span className="text-sm text-[var(--color-ink-soft)] group-hover:text-[var(--color-ink)]">{JOURNEY_NAMES[mod] || "Module"}</span>
                    </div>
                    <span className="text-[var(--color-ink-faint)] group-hover:text-[var(--color-accent)]">↗</span>
                  </a>
                ))}
              </div>
            </div>

            {/* Tool Action */}
            <div className="flex flex-col gap-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-faint)]">
                <ToolIcon /> Generator Tool
              </h3>
              <a 
                href="#/generator"
                className="group flex items-center justify-between rounded-lg border border-[var(--color-accent-soft)] bg-[var(--color-accent-soft)] px-4 py-4 transition-colors hover:bg-[var(--color-accent)]"
              >
                <div>
                  <span className="block text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)] group-hover:text-[var(--color-on-accent)]">Pipeline Output</span>
                  <span className="mt-1 block text-sm font-medium text-[var(--color-ink)] group-hover:text-[var(--color-on-accent)]">{stage.toolLabel}</span>
                </div>
                <span className="text-[var(--color-accent)] group-hover:text-[var(--color-on-accent)]">→</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {selectedPromptObj && (
        <PromptModal
          prompt={selectedPromptObj}
          detail={promptDetails[selectedPromptObj.id] ?? null}
          loading={promptDetailLoading && !promptDetails[selectedPromptObj.id]}
          error={promptDetailError}
          onClose={() => setSelectedPromptId(null)}
        />
      )}
      
      {selectedPromptId?.startsWith("missing-") && (
        <PromptModal
          prompt={{ id: selectedPromptId, title: "Missing Prompt", version: "unknown", stage: selectedPromptId.replace("missing-", ""), model_role: "generator", output_format: "markdown" }}
          detail={null}
          loading={false}
          error="This prompt is not available in the API."
          onClose={() => setSelectedPromptId(null)}
        />
      )}

      {selectedSkill && (
        <SkillModal
          title={selectedSkill.title}
          content={selectedSkill.content}
          onClose={() => setSelectedSkill(null)}
        />
      )}
    </div>
  );
}
