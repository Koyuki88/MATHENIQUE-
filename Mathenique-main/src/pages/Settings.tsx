import { Navigation } from "@/components/layout/Navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GameButton } from "@/components/ui/GameButton";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/contexts/AuthContext";
import { useSound } from "@/contexts/SoundContext";
import { soundEngine } from "@/lib/sound";
import { BookOpen, Trophy, User, Volume2 } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  const { enabled, volume, setEnabled, setVolume } = useSound();

  return (
    <div className="min-h-screen bg-background pb-20 md:pb-0 font-inter">
      <Navigation />

      <main className="container mx-auto px-4 py-8 md:py-12 mt-4 md:mt-12">
        <div className="max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-fredoka font-bold text-foreground mb-4">
              Settings
            </h1>
            <p className="text-muted-foreground text-lg">
              Manage your account and preferences
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <User className="h-6 w-6 text-primary" />
                  <CardTitle>Profile Information</CardTitle>
                </div>
                <CardDescription>Your personal account details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Username</p>
                  <p className="text-lg font-semibold">{user?.name}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Email</p>
                  <p className="text-lg font-semibold">{user?.email}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Volume2 className="h-6 w-6 text-primary" />
                  <CardTitle>Sound & Audio</CardTitle>
                </div>
                <CardDescription>Configure interactive game sound effects</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="sound-toggle" className="text-base font-medium">
                      Sound Effects
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Play chimes, timer ticks, and victory fanfares
                    </p>
                  </div>
                  <Switch
                    id="sound-toggle"
                    checked={enabled}
                    onCheckedChange={(checked) => {
                      setEnabled(checked);
                      if (checked) soundEngine.playClick();
                    }}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Volume</Label>
                    <span className="text-sm font-semibold text-muted-foreground">
                      {Math.round(volume * 100)}%
                    </span>
                  </div>
                  <Slider
                    value={[Math.round(volume * 100)]}
                    min={0}
                    max={100}
                    step={5}
                    disabled={!enabled}
                    onValueChange={([val]) => setVolume(val / 100)}
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Preview Sounds</p>
                  <div className="flex flex-wrap gap-2">
                    <GameButton
                      type="button"
                      variant="outline"
                      size="sm"
                      sound="none"
                      disabled={!enabled}
                      onClick={() => soundEngine.playCorrect(1)}
                    >
                      Correct
                    </GameButton>
                    <GameButton
                      type="button"
                      variant="outline"
                      size="sm"
                      sound="none"
                      disabled={!enabled}
                      onClick={() => soundEngine.playStreak()}
                    >
                      Streak
                    </GameButton>
                    <GameButton
                      type="button"
                      variant="outline"
                      size="sm"
                      sound="none"
                      disabled={!enabled}
                      onClick={() => soundEngine.playVictory(3)}
                    >
                      Victory
                    </GameButton>
                    <GameButton
                      type="button"
                      variant="outline"
                      size="sm"
                      sound="none"
                      disabled={!enabled}
                      onClick={() => soundEngine.playWrong()}
                    >
                      Wrong
                    </GameButton>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Trophy className="h-6 w-6 text-primary" />
                  <CardTitle>Statistics</CardTitle>
                </div>
                <CardDescription>Your learning journey progress</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium text-muted-foreground">Learning Stats</span>
                </div>
                <p className="text-muted-foreground">More detailed statistics coming soon...</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
