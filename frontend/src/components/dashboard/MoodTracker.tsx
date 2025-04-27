import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export const MoodTracker = () => {
  const today = new Date();
  const currentDay = today.getDay();

  const moodData = [
    { day: "Mon", value: 70, color: "bg-green-500" },
    { day: "Tue", value: 60, color: "bg-green-400" },
    { day: "Wed", value: 40, color: "bg-yellow-500" },
    { day: "Thu", value: 75, color: "bg-green-500" },
    { day: "Fri", value: 55, color: "bg-yellow-400" },
    { day: "Sat", value: 80, color: "bg-green-600" },
    { day: "Sun", value: 65, color: "bg-green-400" },
  ];

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base font-medium">Weekly Mood</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {moodData.map((item, index) => (
            <div
              key={item.day}
              className="grid grid-cols-12 items-center gap-2"
            >
              <div
                className={`text-xs col-span-1 ${
                  currentDay === index
                    ? "text-primary font-medium"
                    : "text-muted-foreground"
                }`}
              >
                {item.day}
              </div>
              <div className="col-span-10">
                <Progress value={item.value} className="h-2" />
              </div>
              <div className="text-xs col-span-1 text-right text-muted-foreground">
                {item.value}%
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-between items-center text-xs text-muted-foreground">
          <span>Not so good</span>
          <span>Amazing</span>
        </div>
      </CardContent>
    </Card>
  );
};
