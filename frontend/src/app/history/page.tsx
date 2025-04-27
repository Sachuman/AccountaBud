"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDistanceToNow } from "date-fns";

interface Reminder {
  _id: string;
  type: string;
  date: string;
  time: string;
  description: string;
  phone: string;
  created_at: string;
}

interface Restriction {
  _id: string;
  type: string;
  hostname: string;
  description: string;
  phone: string;
  created_at: string;
}

export default function HistoryPage() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  console.log(activeTab);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);

        // Fetch reminders
        const remindersResponse = await fetch("/api/reminders");
        const remindersData = await remindersResponse.json();

        // Fetch restrictions
        const restrictionsResponse = await fetch("/api/restrictions");
        const restrictionsData = await restrictionsResponse.json();

        if (remindersData.status === "success") {
          setReminders(remindersData.data);
        }

        if (restrictionsData.status === "success") {
          setRestrictions(restrictionsData.data);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format the date for display
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  // Format the time for display
  const formatTime = (timeString: string) => {
    try {
      // Expected format: "HH:MM"
      const [hours, minutes] = timeString.split(":");
      const date = new Date();
      date.setHours(parseInt(hours, 10));
      date.setMinutes(parseInt(minutes, 10));

      return date.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return timeString;
    }
  };

  // Get relative time from now
  const getRelativeTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  };

  // All items sorted by created_at
  const allItems = [...reminders, ...restrictions].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-transparent bg-clip-text">
        Agentic Workflow History
      </h1>

      <div className="flex justify-center mb-8">
        <Tabs defaultValue="all" className="w-full max-w-4xl" onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">All Activity</TabsTrigger>
            <TabsTrigger value="reminders">Reminders</TabsTrigger>
            <TabsTrigger value="restrictions">Restrictions</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-6">
            <div className="relative">
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 via-indigo-400 to-blue-400"></div>
              <ScrollArea className="h-[70vh] pr-4">
                {isLoading ? (
                  <div className="flex justify-center items-center h-40">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
                  </div>
                ) : allItems.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center text-gray-500">
                      No activity recorded yet.
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-4">
                    {allItems.map((item, index) => {
                      const isReminder = 'date' in item;
                      return (
                        <Card key={index} className="border-none shadow-lg hover:shadow-xl transition-shadow duration-300">
                          <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                              <div className="flex items-center">
                                <div className="h-6 w-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mr-3 shadow-md relative z-10">
                                  {isReminder ? (
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                      <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                                    </svg>
                                  ) : (
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                      <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
                                      <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
                                      <line x1="6" y1="1" x2="6" y2="4"></line>
                                      <line x1="10" y1="1" x2="10" y2="4"></line>
                                      <line x1="14" y1="1" x2="14" y2="4"></line>
                                    </svg>
                                  )}
                                </div>
                                <div>
                                  <CardTitle className="text-lg">
                                    {isReminder ? item.description : `Restrict ${item.hostname}`}
                                  </CardTitle>
                                  <CardDescription className="text-sm">
                                    {getRelativeTime(item.created_at)}
                                  </CardDescription>
                                </div>
                              </div>
                              <Badge className={isReminder ? "bg-indigo-500" : "bg-purple-600"}>
                                {isReminder ? "Reminder" : "Restriction"}
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="pl-9 space-y-2">
                              {isReminder ? (
                                <>
                                  <div className="flex justify-between">
                                    <span className="text-sm font-medium text-gray-500">Date:</span>
                                    <span className="text-sm">{formatDate(item.date)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-sm font-medium text-gray-500">Time:</span>
                                    <span className="text-sm">{formatTime(item.time)}</span>
                                  </div>
                                </>
                              ) : (
                                <div className="flex justify-between">
                                  <span className="text-sm font-medium text-gray-500">Reason:</span>
                                  <span className="text-sm">{item.description}</span>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span className="text-sm font-medium text-gray-500">Phone:</span>
                                <span className="text-sm">{item.phone}</span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="reminders" className="mt-6">
            <ScrollArea className="h-[70vh] pr-4">
              {isLoading ? (
                <div className="flex justify-center items-center h-40">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
                </div>
              ) : reminders.length === 0 ? (
                <Card>
                  <CardContent className="pt-6 text-center text-gray-500">
                    No reminders recorded yet.
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {reminders.map((reminder, index) => (
                    <Card key={index} className="border-2 border-indigo-100 hover:border-indigo-300 transition-colors duration-300">
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-xl">{reminder.description}</CardTitle>
                          <Badge className="bg-indigo-500">Reminder</Badge>
                        </div>
                        <CardDescription>{getRelativeTime(reminder.created_at)}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-indigo-50 p-3 rounded-lg">
                            <div className="text-xs text-indigo-600 font-semibold mb-1">DATE</div>
                            <div className="text-xs text-indigo-600 font-semibold mb-1">{formatDate(reminder.date)}</div>
                          </div>
                          <div className="bg-indigo-50 p-3 rounded-lg">
                            <div className="text-xs text-indigo-600 font-semibold mb-1">TIME</div>
                            <div className="text-xs text-indigo-600 font-semibold mb-1">{formatTime(reminder.time)}</div>
                          </div>
                          <div className="bg-indigo-50 p-3 rounded-lg col-span-2">
                            <div className="text-xs text-indigo-600 font-semibold mb-1">PHONE</div>
                            <div className="text-xs text-indigo-600 font-semibold mb-1">{reminder.phone}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="restrictions" className="mt-6">
            <ScrollArea className="h-[70vh] pr-4">
              {isLoading ? (
                <div className="flex justify-center items-center h-40">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
                </div>
              ) : restrictions.length === 0 ? (
                <Card>
                  <CardContent className="pt-6 text-center text-gray-500">
                    No restrictions recorded yet.
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {restrictions.map((restriction, index) => (
                    <Card key={index} className="border-2 border-purple-100 hover:border-purple-300 transition-colors duration-300">
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-xl font-mono">{restriction.hostname}</CardTitle>
                          <Badge className="bg-purple-600">Restriction</Badge>
                        </div>
                        <CardDescription>{getRelativeTime(restriction.created_at)}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 gap-4">
                          <div className="bg-purple-50 p-3 rounded-lg">
                            <div className="text-xs text-purple-600 font-semibold mb-1">REASON</div>
                            <div className="text-xs text-indigo-600 font-semibold mb-1">{restriction.description}</div>
                          </div>
                          <div className="bg-purple-50 p-3 rounded-lg">
                            <div className="text-xs text-purple-600 font-semibold mb-1">PHONE</div>
                            <div className="text-xs text-indigo-600 font-semibold mb-1">{restriction.phone}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 