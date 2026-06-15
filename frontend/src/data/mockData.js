export const user = {
  name: "Alex Chen",
  email: "alex@example.com",
};

export const conversations = [
  {
    id: "design-agent",
    group: "Today",
    title: "Design a new AI agent...",
  },
  {
    id: "market-report",
    group: "Today",
    title: "Market analysis report",
  },
  {
    id: "journey-map",
    group: "Today",
    title: "User journey mapping",
  },
  {
    id: "brand-ideas",
    group: "Today",
    title: "Brand strategy ideas",
  },
  {
    id: "landscape",
    group: "Yesterday",
    title: "Competitive landscape",
  },
  {
    id: "roadmap",
    group: "Yesterday",
    title: "Product roadmap draft",
  },
  {
    id: "onboarding",
    group: "Yesterday",
    title: "Agent onboarding critique",
  },
  {
    id: "memory",
    group: "Last 7 days",
    title: "Memory UX notes",
  },
  {
    id: "pricing",
    group: "Last 7 days",
    title: "Pricing page concepts",
  },
  {
    id: "launch-plan",
    group: "Last 7 days",
    title: "Launch plan outline",
  },
  {
    id: "assistant-eval",
    group: "Last 30 days",
    title: "Assistant eval checklist",
  },
  {
    id: "workflow-map",
    group: "Last 30 days",
    title: "Workflow builder map",
  },
];

export const initialMessages = [
  {
    id: "user-1",
    role: "user",
    body: "Can you help me analyze the market opportunity for AI agents?",
  },
  {
    id: "assistant-1",
    role: "assistant",
    body: "Absolutely. I'd be happy to help you analyze the market opportunity for AI agents. To get started, could you share more about your target market or specific focus areas?",
  },
];

export const threadMessages = {
  "design-agent": initialMessages,
  "market-report": [
    {
      id: "market-user",
      role: "user",
      body: "Build a quick market analysis report for AI agent tools.",
    },
    {
      id: "market-assistant",
      role: "assistant",
      body: "I'll structure it around audience demand, category maturity, competitive density, pricing signals, and gaps for a focused entrant.",
    },
  ],
  "journey-map": [
    {
      id: "journey-user",
      role: "user",
      body: "Map the user journey for a first-time AI agent workspace.",
    },
    {
      id: "journey-assistant",
      role: "assistant",
      body: "The core journey is discover, define the job, connect context, run the first task, inspect output, then save a reusable workflow.",
    },
  ],
  "brand-ideas": [
    {
      id: "brand-user",
      role: "user",
      body: "Give me brand strategy ideas for an AI agent product.",
    },
    {
      id: "brand-assistant",
      role: "assistant",
      body: "I'd position it around calm leverage: less prompt fiddling, more repeatable work systems that feel trustworthy and inspectable.",
    },
  ],
  landscape: [
    {
      id: "landscape-user",
      role: "user",
      body: "Summarize the competitive landscape.",
    },
    {
      id: "landscape-assistant",
      role: "assistant",
      body: "The landscape splits into general assistants, vertical copilots, workflow builders, and developer-first agent frameworks.",
    },
  ],
  roadmap: [
    {
      id: "roadmap-user",
      role: "user",
      body: "Draft a product roadmap for the next quarter.",
    },
    {
      id: "roadmap-assistant",
      role: "assistant",
      body: "Start with activation and reliability: templates, memory controls, run history, shareable outputs, and lightweight evaluations.",
    },
  ],
  onboarding: [
    {
      id: "onboarding-user",
      role: "user",
      body: "Review the first-run onboarding for an agent workspace.",
    },
    {
      id: "onboarding-assistant",
      role: "assistant",
      body: "The onboarding should collect intent, show one useful agent run, then explain how the user can edit or reuse the workflow.",
    },
  ],
  memory: [
    {
      id: "memory-user",
      role: "user",
      body: "What should memory controls look like?",
    },
    {
      id: "memory-assistant",
      role: "assistant",
      body: "Make memory inspectable, reversible, and scoped. Users need to know what was remembered and why it matters.",
    },
  ],
  pricing: [
    {
      id: "pricing-user",
      role: "user",
      body: "Sketch pricing tiers for an AI agent product.",
    },
    {
      id: "pricing-assistant",
      role: "assistant",
      body: "Use tiers around task volume, integrations, shared workspaces, memory depth, and evaluation history.",
    },
  ],
  "launch-plan": [
    {
      id: "launch-user",
      role: "user",
      body: "Draft a launch plan for the AI agent UI.",
    },
    {
      id: "launch-assistant",
      role: "assistant",
      body: "Start with a sharp demo, a focused landing page, three use-case videos, and a waitlist loop for feedback.",
    },
  ],
  "assistant-eval": [
    {
      id: "eval-user",
      role: "user",
      body: "Create an assistant evaluation checklist.",
    },
    {
      id: "eval-assistant",
      role: "assistant",
      body: "Track correctness, instruction following, tool success, latency, recovery behavior, and user-visible confidence.",
    },
  ],
  "workflow-map": [
    {
      id: "workflow-user",
      role: "user",
      body: "Map a workflow builder for agents.",
    },
    {
      id: "workflow-assistant",
      role: "assistant",
      body: "A strong workflow builder needs triggers, context sources, steps, approvals, outputs, and run history.",
    },
  ],
};
