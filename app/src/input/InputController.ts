import { SCENE_IDS, type SceneId } from "../contracts";

export interface InputActions {
  readonly selectScene: (scene: SceneId) => void;
  readonly explore: () => void;
  readonly follow: () => void;
  readonly compare: () => void;
  readonly stress: () => void;
  readonly inspect: () => void;
  readonly ask: () => void;
  readonly statewide: () => void;
  readonly playTime: () => void;
  readonly close: () => void;
}

export class InputController {
  readonly #actions: InputActions;

  constructor(actions: InputActions) {
    this.#actions = actions;
  }

  connect(): void {
    document.addEventListener("keydown", this.#onKeyDown);
  }

  disconnect(): void {
    document.removeEventListener("keydown", this.#onKeyDown);
  }

  readonly #onKeyDown = (event: KeyboardEvent): void => {
    if (
      event.target instanceof HTMLInputElement ||
      event.target instanceof HTMLTextAreaElement
    )
      return;
    const sceneIndex = Number.parseInt(event.key, 10) - 1;
    const scene = SCENE_IDS[sceneIndex];
    if (scene) {
      this.#actions.selectScene(scene);
      return;
    }
    const action = event.key.toLowerCase();
    if (action === "e") this.#actions.explore();
    else if (action === "f") this.#actions.follow();
    else if (action === "c") this.#actions.compare();
    else if (action === "s") this.#actions.stress();
    else if (action === "i") this.#actions.inspect();
    else if (action === "a") this.#actions.ask();
    else if (action === "m") this.#actions.statewide();
    else if (action === "escape") this.#actions.close();
    else if (event.code === "Space") {
      event.preventDefault();
      this.#actions.playTime();
    }
  };
}
