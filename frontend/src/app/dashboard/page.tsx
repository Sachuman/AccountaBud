"use client";
import { useState, useEffect, useMemo } from "react";
import { Label, Pie, PieChart } from "recharts";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";

// Define the expected shape of a reminder object
interface Reminder {
    _id: string; // Assuming MongoDB ObjectId as string
    description: string;
    date: string; // Assuming date is stored as string
    time: string; // Assuming time is stored as string
    // Add other fields if necessary
}

// Define the shape of the data expected by the Pie chart
interface ChartDataItem {
    description: string;
    count: number;
    fill: string;
}

// Helper function to generate chart colors dynamically
const generateColor = (index: number): string => {
    // Use predefined chart colors from shadcn/ui theme if available
    // Cycle through 5 default chart colors
    return `hsl(var(--chart-${(index % 5) + 1}))`;
};

const generateFill = (index: number): string => {
    // Use CSS variables for fill colors consistent with shadcn/ui chart
    return `var(--color-chart-${(index % 5) + 1})`;
};


export default function DashboardPage() {
    const [reminders, setReminders] = useState<Reminder[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch reminders on component mount
    useEffect(() => {
        const fetchReminders = async () => {
            setIsLoading(true);
            setError(null);
            try {
                // NOTE: Fetching directly from MongoDB in a client component is not recommended.
                // This should be replaced with an API call to a backend endpoint or a Server Action.
                // Example using a placeholder API route:
                // const response = await fetch('/api/reminders');
                // if (!response.ok) {
                //   throw new Error('Failed to fetch reminders');
                // }
                // const data = await response.json();
                // setReminders(data);

                // *** Placeholder Data Fetching Simulation ***
                // Replace this with your actual data fetching logic (e.g., API call)
                console.warn("Using placeholder data. Replace with actual API call to fetch reminders.");
                await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate network delay
                const mockReminders: Reminder[] = [
                    { _id: "1", description: "Follow up with client A", date: "2024-07-20", time: "10:00" },
                    { _id: "2", description: "Prepare presentation", date: "2024-07-21", time: "14:00" },
                    { _id: "3", description: "Follow up with client A", date: "2024-07-22", time: "09:00" },
                    { _id: "4", description: "Team meeting", date: "2024-07-20", time: "11:00" },
                    { _id: "5", description: "Prepare presentation", date: "2024-07-23", time: "16:00" },
                    { _id: "6", description: "Review project proposal", date: "2024-07-24", time: "13:00" },
                    { _id: "7", description: "Follow up with client A", date: "2024-07-25", time: "15:00" },
                    { _id: "8", description: "No Description", date: "2024-07-26", time: "17:00" }, // Example with no description
                    { _id: "9", description: "Team meeting", date: "2024-07-27", time: "10:30" },
                ];
                setReminders(mockReminders);
                // *** End Placeholder ***

            } catch (err) {
                console.error("Failed to fetch reminders:", err);
                setError(err instanceof Error ? err.message : "An unknown error occurred");
                setReminders([]); // Clear reminders on error
            } finally {
                setIsLoading(false);
            }
        };

        fetchReminders();
    }, []); // Empty dependency array ensures this runs only once on mount

    // Process reminders to get data and config for the chart based on description counts
    const { chartData, chartConfig, totalCount } = useMemo(() => {
        if (!reminders || reminders.length === 0) {
            return { chartData: [], chartConfig: { count: { label: "Count" } }, totalCount: 0 };
        }

        const descriptionCounts = reminders.reduce<Record<string, number>>((acc, reminder) => {
            const desc = reminder.description?.trim() || "No Description"; // Use "No Description" if empty or null
            acc[desc] = (acc[desc] || 0) + 1;
            return acc;
        }, {});

        const processedChartData: ChartDataItem[] = Object.entries(descriptionCounts)
            .map(([desc, count], index) => ({
                description: desc,
                count: count,
                fill: generateFill(index),
            }))
            .sort((a, b) => b.count - a.count); // Sort by count descending

        const processedChartConfig: ChartConfig = {
            count: {
                label: "Count",
            },
            ...processedChartData.reduce<ChartConfig>((config, item, index) => {
                // Ensure the key used here matches the `nameKey` in the Pie component
                config[item.description] = {
                    label: item.description,
                    color: generateColor(index),
                };
                return config;
            }, {}),
        };

        const total = reminders.length;

        return { chartData: processedChartData, chartConfig: processedChartConfig, totalCount: total };
    }, [reminders]); // Recalculate when reminders data changes

    if (isLoading) {
        return <div className="container mx-auto py-10">Loading reminders...</div>;
    }

    if (error) {
        return <div className="container mx-auto py-10 text-red-600">Error: {error}</div>;
    }

    return (
        <div className="container mx-auto py-10">
             {chartData.length > 0 ? (
                <Card className="flex flex-col">
                    <CardHeader className="items-center pb-0">
                        <CardTitle>Reminders by Description</CardTitle>
                        <CardDescription>Distribution of reminder types</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 pb-0">
                        <ChartContainer
                            config={chartConfig}
                            className="mx-auto aspect-square max-h-[300px]" // Increased max height slightly
                        >
                            <PieChart>
                                <ChartTooltip
                                    cursor={false}
                                    content={<ChartTooltipContent hideLabel nameKey="description" />} // Use description as nameKey
                                />
                                <Pie
                                    data={chartData}
                                    dataKey="count"
                                    nameKey="description" // Key in chartData for names (matches chartConfig keys)
                                    innerRadius={60}
                                    strokeWidth={5}
                                    labelLine={false} // Hide connector lines if labels are inside or not shown
                                    // Optional: Add labels directly on slices if needed
                                    // label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                                >
                                    <Label
                                        content={({ viewBox }) => {
                                            if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                                return (
                                                    <text
                                                        x={viewBox.cx}
                                                        y={viewBox.cy}
                                                        textAnchor="middle"
                                                        dominantBaseline="middle"
                                                    >
                                                        <tspan
                                                            x={viewBox.cx}
                                                            y={viewBox.cy}
                                                            className="fill-foreground text-3xl font-bold"
                                                        >
                                                            {totalCount.toLocaleString()}
                                                        </tspan>
                                                        <tspan
                                                            x={viewBox.cx}
                                                            y={(viewBox.cy || 0) + 24}
                                                            className="fill-muted-foreground"
                                                        >
                                                            Reminders
                                                        </tspan>
                                                    </text>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                </Pie>
                            </PieChart>
                        </ChartContainer>
                    </CardContent>
                    <CardFooter className="flex-col gap-2 text-sm mt-4"> {/* Added margin-top */}
                        {/* Example Footer Content - Adapt as needed */}
                        {/* <div className="flex items-center gap-2 font-medium leading-none">
                            Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
                        </div> */}
                        <div className="leading-none text-muted-foreground">
                            Showing total reminders grouped by description.
                        </div>
                    </CardFooter>
                </Card>
            ) : (
                <p>No reminder data available to display.</p>
            )}
        </div>
    );
}

