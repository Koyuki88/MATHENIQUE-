
import { Navigation } from "@/components/layout/Navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { BookOpen, Trophy, User } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();

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
                         <Trophy className="h-6 w-6 text-primary" />
                         <CardTitle>Statistics</CardTitle>
                    </div>
                    <CardDescription>Your learning journey progress</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 mb-4">
                         <BookOpen className="h-5 w-5 text-muted-foreground"/>
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
