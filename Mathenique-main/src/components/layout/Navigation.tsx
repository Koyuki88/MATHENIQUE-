import { Link, useLocation } from "react-router-dom";
import { BookOpen, Swords, Flag, LogOut, User, Trophy, Settings as SettingsIcon, Volume2, VolumeX } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useSound } from "@/contexts/SoundContext";
import { soundEngine } from "@/lib/sound";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const navItems = [
  { path: "/lessons", label: "Adventure", icon: Flag },
  { path: "/play", label: "Arena", icon: Swords },
  { path: "/progress", label: "Progress", icon: BookOpen },
  { path: "/leaderboard", label: "Leaderboard", icon: Trophy },
];

export function Navigation() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { enabled: soundEnabled, toggleSound } = useSound();

  return (
    <nav className="fixed bottom-0 left-0 right-0 md:top-0 md:bottom-auto z-50">
      <div className="bg-card border-t md:border-b md:border-t-0 border-primary/20 card-shadow">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Logo - Hidden on mobile */}
            <Link to="/" onClick={() => soundEngine.playNav()} className="hidden md:flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
                <span className="text-primary-foreground font-fredoka font-bold text-xl">M</span>
              </div>
              <span className="font-fredoka font-bold text-xl text-foreground">Mathenique</span>
            </Link>

            {/* Navigation Items */}
            <div className="flex items-center justify-around md:justify-center gap-2 md:gap-8 flex-1 md:flex-none">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => soundEngine.playNav()}
                    className={cn(
                      "flex flex-col md:flex-row items-center gap-1 md:gap-2 px-3 md:px-4 py-2 rounded-xl transition-all duration-200",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <item.icon className="w-5 h-5 md:w-6 md:h-6" />
                    <span className="text-xs md:text-base font-semibold">{item.label}</span>
                  </Link>
                );
              })}

              <button
                type="button"
                onClick={toggleSound}
                aria-label={soundEnabled ? "Mute sound effects" : "Unmute sound effects"}
                title={soundEnabled ? "Sound On" : "Sound Muted"}
                className="flex md:hidden flex-col items-center gap-1 px-3 py-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-all duration-200"
              >
                {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                <span className="text-xs font-semibold">{soundEnabled ? "Sound" : "Muted"}</span>
              </button>
            </div>

            {/* User Menu - Hidden on mobile */}
            <div className="hidden md:flex items-center gap-2">
              <button
                type="button"
                onClick={toggleSound}
                aria-label={soundEnabled ? "Mute sound effects" : "Unmute sound effects"}
                title={soundEnabled ? "Mute sound effects" : "Unmute sound effects"}
                className="flex items-center justify-center w-10 h-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors outline-none px-3 py-2 rounded-xl hover:bg-muted">
                    <User className="w-5 h-5" />
                    <span className="font-medium">{user?.name}</span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/settings" onClick={() => soundEngine.playNav()} className="w-full flex items-center cursor-pointer">
                      <SettingsIcon className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
