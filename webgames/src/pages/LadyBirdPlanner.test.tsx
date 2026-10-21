import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LadyBirdPlanner from "./LadyBirdPlanner";

describe("LadyBirdPlanner", () => {
  beforeEach(() => {
    // Don't mock console.log for debugging
    // vi.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("moves ladybird down when down arrow is clicked", async () => {
    render(<LadyBirdPlanner />);

    // Initial ladybird position is at (4,0)
    const downArrowButton = screen.getByRole("button", { name: "⬇️" });

    await act(async () => {
      downArrowButton.click();
      // Add a small delay to let React process the state updates
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // Get all cells (divs with coordinates)
    const cells = screen.getAllByTestId("grid-cell");

    // Find the cell at position (4,1) - it should have the yellow highlight
    const targetCell = cells.find((cell: HTMLElement) => {
      const coordSpan = cell.querySelector(".coordinate-text");
      return coordSpan?.textContent === "4,1";
    });

    console.log("Target cell:", {
      found: !!targetCell,
      coords: targetCell?.querySelector(".coordinate-text")?.textContent,
      currentPosition: targetCell?.getAttribute("data-current-position"),
      className: targetCell?.className,
    });

    expect(targetCell).toBeDefined();
    expect(targetCell?.getAttribute("data-current-position")).toBe("true");
  });
});
