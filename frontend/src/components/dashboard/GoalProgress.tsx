import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

export const GoalProgress = () => {
  const goals = [
    { title: "Weekly Planning Session", completed: true, streak: 7 },
    { title: "Journal entry about gratitude", completed: true, streak: 4 },
    { title: "30 minutes of physical activity", completed: false, streak: 0 },
    { title: "Read for 20 minutes", completed: true, streak: 12 },
    { title: "Practice mindfulness during lunch", completed: false, streak: 0 },
  ];

  const completedGoals = goals.filter((goal) => goal.completed).length;
  const completionRate = (completedGoals / goals.length) * 100;

  return (
    <Card className="glass-card h-full">
      <CardHeader>
        <CardTitle className="flex justify-between items-center text-base font-medium">
          <span>Today&apos;s Goals</span>
          <span className="text-sm text-muted-foreground font-normal">
            {completedGoals}/{goals.length} ({completionRate}%)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {goals.map((goal, index) => (
            <li key={index} className="flex items-center gap-3">
              <div
                className={`h-5 w-5 rounded-full flex items-center justify-center ${
                  goal.completed ? "bg-primary" : "border border-muted"
                }`}
              >
                {goal.completed && <Check className="h-3 w-3 text-white" />}
              </div>
              <div className="flex-1">
                <p
                  className={`text-sm ${
                    goal.completed ? "text-foreground" : "text-muted-foreground"
                  }`}
                >
                  {goal.title}
                </p>
              </div>
              {goal.streak > 0 && (
                <div className="bg-secondary px-2 py-0.5 text-xs rounded-full flex items-center gap-1">
                  <span className="text-xs">🔥</span>
                  <span>{goal.streak}</span>
                </div>
              )}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};
