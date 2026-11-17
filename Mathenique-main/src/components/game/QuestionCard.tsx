import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { GameButton } from "@/components/ui/GameButton";
import { Check, X } from "lucide-react";
import { soundEngine } from "@/lib/sound";
import { MathText } from "@/components/game/MathText";

export interface Question {
  id: number;
  question: string;
  options: string[];
}

export interface AnswerEvaluation {
  isCorrect: boolean;
  correctAnswer: number;
  streak?: number;
}

interface QuestionCardProps {
  question: Question;
  onSubmitAnswer: (selectedIndex: number) => Promise<AnswerEvaluation>;
  onResultComplete: (evaluation: AnswerEvaluation) => void;
  disabled?: boolean;
}

export function QuestionCard({
  question,
  onSubmitAnswer,
  onResultComplete,
  disabled,
}: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [correctAnswerIndex, setCorrectAnswerIndex] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    setSelectedAnswer(null);
    setCorrectAnswerIndex(null);
    setShowResult(false);
    setIsSubmitting(false);

    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [question.id]);

  const handleSelect = (index: number) => {
    if (showResult || isSubmitting || disabled) return;
    soundEngine.playSelect();
    setSelectedAnswer(index);
  };

  const handleSubmit = async () => {
    if (selectedAnswer === null || showResult || isSubmitting || disabled) return;
    setIsSubmitting(true);

    try {
      const evaluation = await onSubmitAnswer(selectedAnswer);
      setCorrectAnswerIndex(evaluation.correctAnswer);
      setShowResult(true);

      if (evaluation.isCorrect) {
        soundEngine.playCorrect(evaluation.streak ?? 1);
      } else {
        soundEngine.playWrong();
      }

      timerRef.current = window.setTimeout(() => {
        timerRef.current = null;
        setSelectedAnswer(null);
        setCorrectAnswerIndex(null);
        setShowResult(false);
        setIsSubmitting(false);
        onResultComplete(evaluation);
      }, 1500);
    } catch {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="game-card p-6 md:p-8 max-w-2xl mx-auto">
      {/* Question */}
      <h2 className="text-2xl md:text-3xl font-fredoka font-bold text-center mb-8">
        <MathText text={question.question} />
      </h2>

      {/* Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {question.options.map((option, index) => {
          const isSelected = selectedAnswer === index;
          const isCorrect = correctAnswerIndex !== null && index === correctAnswerIndex;
          const showCorrect = showResult && isCorrect;
          const showWrong = showResult && isSelected && !isCorrect;

          return (
            <button
              key={index}
              type="button"
              onClick={() => handleSelect(index)}
              disabled={showResult || isSubmitting || disabled}
              className={cn(
                "relative p-4 md:p-5 rounded-xl border-2 text-lg font-semibold transition-all duration-300",
                "hover:scale-102 active:scale-98",
                !showResult && !isSelected && "bg-card border-primary/20 hover:border-primary/50",
                !showResult && isSelected && "bg-primary/10 border-primary",
                showCorrect && "bg-success/20 border-success",
                showWrong && "bg-destructive/20 border-destructive shake"
              )}
            >
              <span className="flex items-center justify-center gap-2">
                <span>
                  <MathText text={option} />
                </span>
                {showCorrect && (
                  <Check className="w-6 h-6 text-success bounce-in" strokeWidth={3} />
                )}
                {showWrong && (
                  <X className="w-6 h-6 text-destructive bounce-in" strokeWidth={3} />
                )}
              </span>
            </button>
          );
        })}
      </div>

      {/* Submit Button */}
      <div className="flex justify-center">
        <GameButton
          variant="primary"
          size="lg"
          onClick={handleSubmit}
          disabled={selectedAnswer === null || showResult || isSubmitting || disabled}
        >
          {isSubmitting && !showResult ? "Checking..." : "Check Answer"}
        </GameButton>
      </div>
    </div>
  );
}
