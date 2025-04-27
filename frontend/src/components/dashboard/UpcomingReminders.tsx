import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock } from "lucide-react";

export const UpcomingReminders = () => {
  const reminders = [
    {
      title: "Morning Gym Session",
      time: "Today, 7:00 AM",
      tag: "Wellness",
    },
    {
      title: "Journaling session",
      time: "Today, 9:30 AM",
      tag: "Reflection",
    },
    {
      title: "Reduce Instagram usage",
      tag: "Social Media Restriction",
    },
    {
      title: "Weekly goal setting",
      time: "Next Week, 9:00 AM",
      tag: "Planning",
    },
  ];

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span>Upcoming Reminders</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {reminders.map((reminder, index) => (
            <li key={index} className="flex items-center justify-between">
              <div>
                <p className="text-sm">{reminder.title}</p>
                <p className="text-xs text-muted-foreground">{reminder.time}</p>
              </div>
              <span className="text-xs px-2 py-1 bg-secondary rounded-full">
                {reminder.tag}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};
