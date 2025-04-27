"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  
  const navItems = [
    { name: "Home", href: "/" },
    { name: "History", href: "/history" },
  ];
  
  return (
    <nav className="border-b border-border bg-background fixed top-0 left-0 right-0 z-50">
      <div className="container flex h-16 items-center">
        <div className="flex items-center space-x-4 lg:space-x-6">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "text-sm font-medium transition-colors hover:text-primary",
                pathname === item.href
                  ? "text-foreground font-bold"
                  : "text-muted-foreground"
              )}
            >
              {item.name}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
} 