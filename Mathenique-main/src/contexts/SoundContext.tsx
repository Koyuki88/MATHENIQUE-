import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { soundEngine } from "@/lib/sound";

interface SoundContextType {
  enabled: boolean;
  volume: number;
  setEnabled: (enabled: boolean) => void;
  toggleSound: () => boolean;
  setVolume: (volume: number) => void;
}

const SoundContext = createContext<SoundContextType | undefined>(undefined);

export function SoundProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabledState] = useState(() => soundEngine.getEnabled());
  const [volume, setVolumeState] = useState(() => soundEngine.getVolume());

  useEffect(() => {
    const unsubscribe = soundEngine.subscribe(() => {
      setEnabledState(soundEngine.getEnabled());
      setVolumeState(soundEngine.getVolume());
    });

    const unlockAudio = () => soundEngine.unlock();
    window.addEventListener("pointerdown", unlockAudio, { once: true, passive: true });
    window.addEventListener("keydown", unlockAudio, { once: true, passive: true });

    return () => {
      unsubscribe();
      window.removeEventListener("pointerdown", unlockAudio);
      window.removeEventListener("keydown", unlockAudio);
    };
  }, []);

  return (
    <SoundContext.Provider
      value={{
        enabled,
        volume,
        setEnabled: (val) => soundEngine.setEnabled(val),
        toggleSound: () => soundEngine.toggleEnabled(),
        setVolume: (val) => soundEngine.setVolume(val),
      }}
    >
      {children}
    </SoundContext.Provider>
  );
}

export function useSound() {
  const context = useContext(SoundContext);
  if (context === undefined) {
    throw new Error("useSound must be used within a SoundProvider");
  }
  return context;
}
