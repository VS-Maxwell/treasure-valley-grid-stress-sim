import {
  INITIAL_STATE,
  clampYear,
  isSceneId,
  truthStateForYear,
  truthStateForView,
  type SceneId,
  type EnergyScenario,
  type SimulationState,
} from "../contracts";

type Subscriber = (state: SimulationState, previous: SimulationState) => void;

export class SimulationStore {
  readonly #subscribers = new Set<Subscriber>();
  #state: SimulationState;

  constructor(initial: SimulationState = INITIAL_STATE) {
    this.#state = { ...initial };
  }

  get state(): SimulationState {
    return this.#state;
  }

  subscribe(subscriber: Subscriber): () => void {
    this.#subscribers.add(subscriber);
    subscriber(this.#state, this.#state);
    return () => this.#subscribers.delete(subscriber);
  }

  selectScene(scene: SceneId): void {
    this.#commit({
      scene,
      drawer: scene === "record" ? "evidence" : this.#state.drawer,
      truthState: truthStateForView(scene, this.#state.year),
    });
  }

  selectSceneFromInput(value: string): boolean {
    if (!isSceneId(value)) return false;
    this.selectScene(value);
    return true;
  }

  setYear(year: number): void {
    const boundedYear = clampYear(year);
    this.#commit({
      year: boundedYear,
      truthState: truthStateForView(this.#state.scene, boundedYear),
    });
  }

  setEnergyScenario(energyScenario: EnergyScenario): void {
    this.#commit({
      energyScenario,
      scene: "energy",
      truthState: "modeled-screening",
    });
  }

  togglePlaying(): void {
    this.#commit({ playing: !this.#state.playing });
  }

  toggleCompare(): void {
    this.#commit({ compare: !this.#state.compare });
  }

  stress(): void {
    this.#commit({
      scene: "nexus",
      year: 2050,
      compare: true,
      climateScenario: "heat-drought-2050",
      truthState: "modeled-screening",
    });
  }

  explore(): void {
    this.#commit({
      scene: "time",
      drawer: "closed",
      truthState: truthStateForYear(this.#state.year),
    });
  }

  follow(): void {
    const path: SceneId[] = ["energy", "water", "nexus", "risk"];
    const current = path.indexOf(this.#state.scene);
    const scene = path[(current + 1 + path.length) % path.length] ?? "energy";
    this.#commit({
      scene,
      truthState: truthStateForView(scene, this.#state.year),
    });
  }

  openDrawer(drawer: Exclude<SimulationState["drawer"], "closed">): void {
    this.#commit({ drawer });
  }

  closeDrawer(): void {
    this.#commit({ drawer: "closed" });
  }

  tick(years = 5): void {
    if (!this.#state.playing) return;
    const nextYear =
      this.#state.year + years > 2100 ? -15_000 : this.#state.year + years;
    this.setYear(nextYear);
  }

  #commit(patch: Partial<SimulationState>): void {
    const previous = this.#state;
    const next = { ...previous, ...patch };
    if (
      Object.keys(patch).every(
        (key) =>
          previous[key as keyof SimulationState] ===
          next[key as keyof SimulationState],
      )
    ) {
      return;
    }
    this.#state = next;
    this.#subscribers.forEach((subscriber) => subscriber(next, previous));
  }
}
