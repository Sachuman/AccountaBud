import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MessageCircle } from "lucide-react";

export const QuickChat = () => {
  const messages = [
    {
      id: 1,
      sender: "ai",
      message: "Hi there! What are your plans for this week? Let me help you achieve the most of your goals!",
      timestamp: new Date(new Date().getTime() - 60000 * 5),
    },
    {
      id: 2,
      sender: "user",
      message: "Hey there, I want to make sure that I go to the gym at least 3 times this week, preferably in the mornings. I also want to reduce my screen time on Instagram this week!",
      timestamp: new Date(new Date().getTime() - 60000 * 4),
    },
    {
      id: 3,
      sender: "ai",
      message:
        "Great, Let me get that set for you! I will remind you to go to the gym every morning at 7 AM and I will notify you if and when you visit Instagram!",
      timestamp: new Date(new Date().getTime() - 60000 * 3),
    },
  ];

  return (
    <Card className="glass-card flex flex-col h-full">
      <CardHeader>
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <MessageCircle className="h-4 w-4" />
          <span>Chat with Accountabud</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto scrollbar-none mb-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`flex gap-2 ${
                  msg.sender === "user" ? "flex-row-reverse" : "flex-row"
                } max-w-[80%]`}
              >
                {msg.sender === "ai" ? (
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder.svg" />
                    <AvatarFallback className="bg-primary text-xs">
                      MS
                    </AvatarFallback>
                  </Avatar>
                ) : (
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-accent/20 text-xs">
                      JD
                    </AvatarFallback>
                  </Avatar>
                )}
                <div
                  className={`rounded-lg p-3 text-sm ${
                    msg.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary"
                  }`}
                >
                  <p>{msg.message}</p>
                  <div
                    className={`text-xs mt-1 ${
                      msg.sender === "user"
                        ? "text-primary-foreground/70"
                        : "text-muted-foreground"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Type a message..."
            className="bg-secondary border-0"
          />
          <Button>Send</Button>
        </div>
      </CardContent>
    </Card>
  );
};
