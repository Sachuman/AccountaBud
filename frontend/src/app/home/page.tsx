import React from "react";
import FallingText from "@/components/FallingText";
import Threads from "@/components/Threads/Threads";
import { LineShadowText } from "@/components/magicui/line-shadow-text";
import ScrollFloat from "@/components/ScrollFloat/ScrollFloat";
import Link from "next/link";

function Home() {
  return (
    <div className="w-full">
      <div className="flex flex-col items-center justify-center h-[70vh] text-center">
        {/* Centered the content within this div */}
        <div
          className="relative flex flex-col items-center justify-center"
          style={{ width: "100%", height: "1000px" }}
        >
          <Threads amplitude={1} distance={0} enableMouseInteraction={true} />
          {/* Wrapped text and component for better centering control */}
          <h1 className="flex text-7xl md:text-9xl items-center mt-4">
            {" "}
            {/* Added some margin-top for spacing if needed */}
            Here comes {"  "}
            <LineShadowText>Accountabud</LineShadowText>
          </h1>
        </div>
        <FallingText
          text="because committing to your goals is hard!"
          trigger="auto"
          gravity={0.5}
          wireframes={false}
          backgroundColor="transparent"
          mouseConstraintStiffness={0.2}
        />
      </div>

      <div className="h-[40vh]" />
      <div className="h-[40vh] flex flex-col items-center justify-start">
        <ScrollFloat
          animationDuration={1}
          ease="back.inOut(2)"
          scrollStart="center bottom+=10%"
          scrollEnd="bottom bottom-=30%"
          stagger={0.03}
          containerClassName="mb-10 md:mb-20"
        >
          Jump Right In!
        </ScrollFloat>
        <Link className="p-4 md:p-8 mt-2 md:mt-4 outline hover:bg-secondary/90" href="/">
          Get Started
        </Link>
      </div>
    </div>
  );
}

export default Home;
