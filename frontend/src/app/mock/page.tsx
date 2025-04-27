import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { GoalProgress } from "@/components/dashboard/GoalProgress";
import { JournalInsight } from "@/components/dashboard/JournalInsight";
import { MoodTracker } from "@/components/dashboard/MoodTracker";
import { QuickChat } from "@/components/dashboard/QuickChat";
import { UpcomingReminders } from "@/components/dashboard/UpcomingReminders";
import { Heart } from "lucide-react";

const Index = () => {
  const getTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "morning";
    if (hour < 18) return "afternoon";
    return "evening";
  };

  return (
    <div className="py-6 space-y-6 max-w-7xl mx-auto px-4 md:px-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-heading font-semibold">
            Good {getTimeOfDay()}, John
          </h1>
          <p className="text-muted-foreground">
            Here&apos;s your mental wellness snapshot for today
          </p>
        </div>
        <Button variant="ghost" className="text-primary gap-2">
          <Heart className="h-4 w-4 text-pink-400" />
          <span>Check in</span>
        </Button>
      </div>

      <Card className="bg-gradient-to-r from-primary/10 to-accent/5 border-primary/20">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center animate-pulse-subtle">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold">76%</span>
              </div>
            </div>
            <div>
              <h2 className="text-lg font-heading font-medium">
                Your wellness score is looking good
              </h2>
              <p className="text-sm text-muted-foreground">
                You&apos;re making progress on your goals and maintaining consistent
                mood.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <QuickChat />
        </div>
        <div className="space-y-6">
          <GoalProgress />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <JournalInsight />
        <UpcomingReminders />
      </div>
    </div>
  );
};

export default Index;
