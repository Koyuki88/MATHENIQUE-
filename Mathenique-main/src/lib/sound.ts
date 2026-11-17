const SOUND_ENABLED_KEY = "mathenique_sound_enabled";
const SOUND_VOLUME_KEY = "mathenique_sound_volume";

type SoundListener = () => void;

class SoundEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private enabled: boolean;
  private volume: number;
  private listeners = new Set<SoundListener>();

  constructor() {
    this.enabled = this.readEnabled();
    this.volume = this.readVolume();
  }

  private readEnabled(): boolean {
    try {
      const saved = localStorage.getItem(SOUND_ENABLED_KEY);
      return saved === null ? true : saved === "true";
    } catch {
      return true;
    }
  }

  private readVolume(): number {
    try {
      const raw = localStorage.getItem(SOUND_VOLUME_KEY);
      if (raw === null) return 0.7;
      const parsed = Number(raw);
      return Number.isFinite(parsed) ? Math.min(1, Math.max(0, parsed)) : 0.7;
    } catch {
      return 0.7;
    }
  }

  private notify(): void {
    this.listeners.forEach((listener) => listener());
  }

  subscribe(listener: SoundListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  getEnabled(): boolean {
    return this.enabled;
  }

  getVolume(): number {
    return this.volume;
  }

  setEnabled(value: boolean): void {
    this.enabled = value;
    try {
      localStorage.setItem(SOUND_ENABLED_KEY, String(value));
    } catch {
      // Ignore storage errors
    }
    this.syncMasterGain();
    this.notify();
  }

  toggleEnabled(): boolean {
    const next = !this.enabled;
    this.setEnabled(next);
    if (next) {
      this.playClick();
    }
    return next;
  }

  setVolume(value: number): void {
    const clamped = Math.min(1, Math.max(0, value));
    this.volume = clamped;
    try {
      localStorage.setItem(SOUND_VOLUME_KEY, String(clamped));
    } catch {
      // Ignore storage errors
    }
    this.syncMasterGain();
    this.notify();
  }

  private getAudioContextCtor(): typeof AudioContext | null {
    if (typeof window === "undefined") return null;
    return (
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext ||
      null
    );
  }

  private ensureContext(): AudioContext | null {
    const Ctor = this.getAudioContextCtor();
    if (!Ctor) return null;

    if (!this.ctx) {
      this.ctx = new Ctor();
      const compressor = this.ctx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-16, this.ctx.currentTime);
      compressor.knee.setValueAtTime(18, this.ctx.currentTime);
      compressor.ratio.setValueAtTime(6, this.ctx.currentTime);
      compressor.attack.setValueAtTime(0.005, this.ctx.currentTime);
      compressor.release.setValueAtTime(0.15, this.ctx.currentTime);

      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(
        this.enabled ? this.volume : 0,
        this.ctx.currentTime
      );

      this.masterGain.connect(compressor);
      compressor.connect(this.ctx.destination);
    }

    if (this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {
        // Autoplay restriction until user gesture
      });
    }

    return this.ctx;
  }

  private syncMasterGain(): void {
    if (!this.ctx || !this.masterGain) return;
    const target = this.enabled ? this.volume : 0;
    this.masterGain.gain.setTargetAtTime(target, this.ctx.currentTime, 0.015);
  }

  unlock(): void {
    this.ensureContext();
  }

  private canPlay(): AudioContext | null {
    if (!this.enabled || this.volume <= 0) return null;
    return this.ensureContext();
  }

  private tone(
    ctx: AudioContext,
    opts: {
      freq: number;
      endFreq?: number;
      type?: OscillatorType;
      delay?: number;
      duration: number;
      gain?: number;
      filterFreq?: number;
    }
  ): void {
    if (!this.masterGain) return;

    const start = ctx.currentTime + (opts.delay ?? 0);
    const end = start + opts.duration;
    const peakGain = Math.max(0.001, opts.gain ?? 0.18);

    const osc = ctx.createOscillator();
    const env = ctx.createGain();

    osc.type = opts.type ?? "sine";
    osc.frequency.setValueAtTime(opts.freq, start);
    if (opts.endFreq !== undefined) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(20, opts.endFreq), end);
    }

    env.gain.setValueAtTime(0.0001, start);
    env.gain.linearRampToValueAtTime(peakGain, start + 0.008);
    env.gain.exponentialRampToValueAtTime(0.0001, end);

    if (opts.filterFreq) {
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(opts.filterFreq, start);
      osc.connect(filter);
      filter.connect(env);
    } else {
      osc.connect(env);
    }

    env.connect(this.masterGain);
    osc.start(start);
    osc.stop(end + 0.02);
  }

  playClick(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: 520,
      endFreq: 320,
      type: "triangle",
      duration: 0.045,
      gain: 0.14,
    });
  }

  playNav(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: 440,
      endFreq: 580,
      type: "sine",
      duration: 0.04,
      gain: 0.1,
    });
  }

  playSelect(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: 620,
      endFreq: 860,
      type: "sine",
      duration: 0.045,
      gain: 0.13,
    });
  }

  playStart(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5 E5 G5 C6
    notes.forEach((freq, idx) => {
      this.tone(ctx, {
        freq,
        type: "triangle",
        delay: idx * 0.055,
        duration: idx === notes.length - 1 ? 0.22 : 0.11,
        gain: 0.16,
      });
    });
  }

  playCorrect(streak = 1): void {
    const ctx = this.canPlay();
    if (!ctx) return;

    const semitoneBoost = Math.min(Math.max(0, streak - 1), 7);
    const factor = Math.pow(2, semitoneBoost / 12);
    const root = 523.25 * factor; // C5 shifted up with streak
    const fifth = 783.99 * factor; // G5 shifted up with streak

    this.tone(ctx, {
      freq: root,
      type: "sine",
      delay: 0,
      duration: 0.12,
      gain: 0.2,
    });
    this.tone(ctx, {
      freq: fifth,
      type: "triangle",
      delay: 0.07,
      duration: 0.24,
      gain: 0.22,
    });

    // Extra shimmer on hot streaks (3+)
    if (streak >= 3) {
      this.tone(ctx, {
        freq: root * 2,
        type: "sine",
        delay: 0.14,
        duration: 0.22,
        gain: 0.14,
      });
    }
  }

  playStreak(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    const sparkle = [783.99, 987.77, 1174.66, 1567.98]; // G5 B5 D6 G6
    sparkle.forEach((freq, idx) => {
      this.tone(ctx, {
        freq,
        type: "sine",
        delay: idx * 0.045,
        duration: 0.18,
        gain: 0.15,
      });
    });
  }

  playWrong(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: 290,
      endFreq: 190,
      type: "sawtooth",
      delay: 0,
      duration: 0.14,
      gain: 0.12,
      filterFreq: 750,
    });
    this.tone(ctx, {
      freq: 210,
      endFreq: 145,
      type: "triangle",
      delay: 0.09,
      duration: 0.2,
      gain: 0.18,
    });
  }

  playTick(urgent = false): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: urgent ? 1150 : 840,
      endFreq: urgent ? 720 : 540,
      type: "triangle",
      duration: urgent ? 0.05 : 0.035,
      gain: urgent ? 0.16 : 0.09,
    });
  }

  playTimeout(): void {
    const ctx = this.canPlay();
    if (!ctx) return;
    this.tone(ctx, {
      freq: 440,
      endFreq: 330,
      type: "sawtooth",
      delay: 0,
      duration: 0.16,
      gain: 0.13,
      filterFreq: 1100,
    });
    this.tone(ctx, {
      freq: 311.13,
      endFreq: 196,
      type: "triangle",
      delay: 0.14,
      duration: 0.28,
      gain: 0.18,
    });
  }

  playVictory(stars = 0): void {
    const ctx = this.canPlay();
    if (!ctx) return;

    const fanfare = [
      { freq: 523.25, delay: 0, duration: 0.12 }, // C5
      { freq: 659.25, delay: 0.09, duration: 0.12 }, // E5
      { freq: 783.99, delay: 0.18, duration: 0.14 }, // G5
      { freq: 1046.5, delay: 0.28, duration: 0.42 }, // C6
    ];

    fanfare.forEach((note) => {
      this.tone(ctx, {
        freq: note.freq,
        type: "triangle",
        delay: note.delay,
        duration: note.duration,
        gain: 0.18,
      });
    });

    // Warm final harmony chord
    [523.25, 659.25, 783.99].forEach((freq) => {
      this.tone(ctx, {
        freq,
        type: "sine",
        delay: 0.28,
        duration: 0.45,
        gain: 0.09,
      });
    });

    // Extra star twinkle for 3-star wins
    if (stars >= 3) {
      [1318.51, 1567.98].forEach((freq, idx) => {
        this.tone(ctx, {
          freq,
          type: "sine",
          delay: 0.46 + idx * 0.07,
          duration: 0.22,
          gain: 0.12,
        });
      });
    }
  }

  playDefeat(): void {
    const ctx = this.canPlay();
    if (!ctx) return;

    const notes = [
      { freq: 329.63, delay: 0, duration: 0.16 }, // E4
      { freq: 293.66, delay: 0.14, duration: 0.16 }, // D4
      { freq: 261.63, delay: 0.28, duration: 0.18 }, // C4
      { freq: 220.0, delay: 0.44, duration: 0.38 }, // A3
    ];

    notes.forEach((note) => {
      this.tone(ctx, {
        freq: note.freq,
        type: "triangle",
        delay: note.delay,
        duration: note.duration,
        gain: 0.16,
      });
    });
  }
}

export const soundEngine = new SoundEngine();
