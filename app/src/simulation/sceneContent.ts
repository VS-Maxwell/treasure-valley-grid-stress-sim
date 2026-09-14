import type { SceneId } from "../contracts";

export interface SceneContent {
  readonly eyebrow: string;
  readonly title: string;
  readonly copy: string;
  readonly metrics: readonly {
    readonly value: string;
    readonly label: string;
  }[];
}

export const SCENE_CONTENT: Record<SceneId, SceneContent> = {
  time: {
    eyebrow: "TIME · RECONSTRUCTION TO FUTURES",
    title: "Move through the valley's changing systems",
    copy: "Deep time is reconstructed, historical records are observed or ingested, and future motion is modeled. The timeline never disguises one state as another.",
    metrics: [
      { value: "17,100 yr", label: "timeline span" },
      { value: "3", label: "truth regimes" },
    ],
  },
  water: {
    eyebrow: "WATER · USGS BASELINE REPRODUCED",
    title: "Enter the six-layer Treasure Valley aquifer model",
    copy: "The blue footprint comes from the verified USGS MODFLOW 6 archive. Its 1986–2015 baseline now runs to normal termination and matches archived heads and observation tables within recorded tolerances; new scenarios still require domain review.",
    metrics: [
      { value: "6", label: "model layers" },
      { value: "4,055", label: "active top cells" },
      { value: "0.00%", label: "budget discrepancy" },
    ],
  },
  energy: {
    eyebrow: "ENERGY · PRESENT SYSTEM",
    title: "Follow electricity across the valley",
    copy: "Exact extracted corridor geometry is draped over a reconstructed preview surface. Select a system to see what is connected and what remains unknown.",
    metrics: [
      { value: "244", label: "visible corridors" },
      { value: "94 / 156", label: "screening buses / lines" },
      { value: "12", label: "interactive buses" },
    ],
  },
  nexus: {
    eyebrow: "NEXUS · CONNECTED CONSEQUENCES",
    title: "See how heat and drought cross system boundaries",
    copy: "Scenario H will connect climate, snow, canal supply, crops, recharge, pumping, electricity, wildfire, costs, and unequal exposure through typed handoffs.",
    metrics: [
      { value: "13", label: "flagship domains" },
      { value: "H", label: "first coupled scenario" },
    ],
  },
  risk: {
    eyebrow: "RISK · UNVALIDATED PREVIEW",
    title: "Separate hazards from evidence and decisions",
    copy: "Risk cards remain disabled until RAVEN inputs, distributions, version, seeds, outputs, and acceptance receipts can reproduce the result.",
    metrics: [
      { value: "RAVEN", label: "planned engine" },
      { value: "NO RECEIPT", label: "release state" },
    ],
  },
  record: {
    eyebrow: "RECORD · PROVENANCE",
    title: "Inspect the evidence behind every visible claim",
    copy: "Sources, transformations, units, coordinate systems, time bases, uncertainty, authority, and downstream use belong to the scientific state—not to the renderer.",
    metrics: [
      { value: "SHA-256", label: "source receipts" },
      { value: "7", label: "truth states" },
    ],
  },
  learning: {
    eyebrow: "LEARNING · GUIDED EXPLORATION",
    title: "Teach the system without hiding uncertainty",
    copy: "Guided paths will let educators follow water, energy, nexus, risk, and evidence while preserving local authority and clear modeled-versus-observed labels.",
    metrics: [
      { value: "5", label: "planned guided paths" },
      { value: "OFFLINE", label: "target mode" },
    ],
  },
};
