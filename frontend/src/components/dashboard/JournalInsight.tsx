import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Book } from "lucide-react";

export const JournalInsight = () => {
  return (
    <Card className="glass-card h-full">
      <CardHeader>
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Book className="h-4 w-4" />
          <span>Journal Insight</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <blockquote className="italic text-sm text-muted-foreground mb-4 border-l-2 border-primary/50 pl-3">
            &quot;I&apos;m starting to notice that I feel much more grounded when I take
            time for myself in the morning...&quot;
          </blockquote>
          <div className="bg-secondary rounded-lg p-4">
            <h4 className="text-sm font-medium text-gradient mb-2">
              Your Accountabud noticed:
            </h4>
            <p className="text-sm text-foreground/90">
              Your recent journal entries show a positive correlation between
              morning routines and overall daily well-being. Try maintaining
              this routine for greater stability.
            </p>
          </div>
          <div className="text-xs text-muted-foreground mt-3 flex justify-between">
            <span>From journal entry - April 24</span>
            <span className="text-primary underline cursor-pointer">
              View full entry
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
