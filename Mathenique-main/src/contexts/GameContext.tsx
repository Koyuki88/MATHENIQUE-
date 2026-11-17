import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { useAuth } from "./AuthContext";
import api from "@/api/axios";

interface LessonProgress {
  lessonId: number;
  stars: number;
  completed: boolean;
}

export interface GameStats {
  totalQuestions: number;
  correctAnswers: number;
  gamesPlayed: number;
  challengeBestStreak: number;
  apocalypseBestStreak: number;
  lessonsCompleted: number;
  challengeHighScore: number;
  apocalypseHighScore: number;
}

interface GameContextType {
  currentLesson: number;
  completedLessons: LessonProgress[];
  stats: GameStats;
  applyStats: (backend: any) => void;
  refreshStats: () => Promise<void>;
  refreshProgress: () => Promise<void>;
}

const defaultStats: GameStats = {
  totalQuestions: 0,
  correctAnswers: 0,
  gamesPlayed: 0,
  lessonsCompleted: 0,
  challengeBestStreak: 0,
  apocalypseBestStreak: 0,
  challengeHighScore: 0,
  apocalypseHighScore: 0,
};

const mapStats = (backend: any): GameStats => ({
  totalQuestions: backend?.total_questions ?? 0,
  correctAnswers: backend?.correct_answers ?? 0,
  gamesPlayed: backend?.games_played ?? 0,
  lessonsCompleted: backend?.lessons_completed ?? 0,
  challengeBestStreak: backend?.challenge_best_streak ?? 0,
  apocalypseBestStreak: backend?.apocalypse_best_streak ?? 0,
  challengeHighScore: backend?.challenge_high_score ?? 0,
  apocalypseHighScore: backend?.apocalypse_high_score ?? 0,
});

const GameContext = createContext<GameContextType | undefined>(undefined);

export function GameProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [currentLesson, setCurrentLesson] = useState(1);
  const [completedLessons, setCompletedLessons] = useState<LessonProgress[]>([]);
  const [stats, setStats] = useState<GameStats>(defaultStats);

  const applyStats = useCallback((backend: any) => {
    setStats(mapStats(backend));
  }, []);

  const refreshStats = useCallback(async () => {
    if (!user) return;
    try {
      const res = await api.get("/stats");
      setStats(mapStats(res.data));
    } catch (err) {
      console.error("Failed to refresh stats from backend:", err);
    }
  }, [user?.id]);

  const refreshProgress = useCallback(async () => {
    if (!user) return;
    try {
      const res = await api.get("/lessons/progress");
      const lessons: LessonProgress[] = res.data.map((l: any) => ({
        lessonId: l.lesson_id,
        stars: l.stars,
        completed: Boolean(l.completed),
      }));
      setCompletedLessons(lessons);

      const highestCompleted =
        lessons
          .filter((l) => l.completed)
          .map((l) => l.lessonId)
          .sort((a, b) => b - a)[0] ?? 0;
      setCurrentLesson(highestCompleted + 1);
    } catch (err) {
      console.error("Failed to refresh lesson progress from backend:", err);
    }
  }, [user?.id]);

  useEffect(() => {
    if (!user) {
      setStats(defaultStats);
      setCompletedLessons([]);
      setCurrentLesson(1);
      return;
    }

    refreshStats();
    refreshProgress();

    const syncOnVisible = () => {
      if (document.visibilityState === "visible") {
        refreshStats();
        refreshProgress();
      }
    };

    window.addEventListener("focus", syncOnVisible);
    document.addEventListener("visibilitychange", syncOnVisible);

    return () => {
      window.removeEventListener("focus", syncOnVisible);
      document.removeEventListener("visibilitychange", syncOnVisible);
    };
  }, [user?.id, refreshStats, refreshProgress]);

  return (
    <GameContext.Provider
      value={{
        currentLesson,
        completedLessons,
        stats,
        applyStats,
        refreshStats,
        refreshProgress,
      }}
    >
      {children}
    </GameContext.Provider>
  );
}

export function useGame() {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error("useGame must be used within a GameProvider");
  }
  return context;
}
