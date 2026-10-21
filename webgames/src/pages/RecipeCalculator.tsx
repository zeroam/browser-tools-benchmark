import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";
import { recipes } from "./recipes/recipes";

export const PASSWORD_RecipeCalculator = "RECIPE_CALC_2024";
export const TASK_ID_RecipeCalculator = "recipe-calculator";

const RecipeCalculator: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_RecipeCalculator);
  const [answer, setAnswer] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  // The target recipe is Spaghetti Carbonara, and we want to calculate for 8 servings
  const targetRecipe = recipes.find(
    (r) => r.name === "Classic Spaghetti Carbonara"
  );
  const targetServings = 8;
  const targetIngredient = "pancetta";

  const calculateExpectedAmount = () => {
    if (!targetRecipe) return 0;
    const originalAmount =
      targetRecipe.ingredients.find((i) => i.item === targetIngredient)
        ?.amount || 0;
    return (originalAmount * targetServings) / targetRecipe.servings;
  };

  const handleSubmit = () => {
    const expectedAmount = calculateExpectedAmount();
    const userAnswer = parseFloat(answer);

    if (Math.abs(userAnswer - expectedAmount) < 0.01) {
      setPassword(PASSWORD_RecipeCalculator);
      setMessage(
        "Congratulations! You've correctly calculated the amount of pancetta needed!"
      );
      recordSuccess();
    } else {
      setMessage("That's not quite right. Try again!");
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold">Recipe Calculator Challenge</h1>
          </div>

          <div className="mb-6">
            <p className="text-gray-700 mb-4">
              Your friend is hosting a dinner party for 8 people and wants to
              make a classic Italian pasta dish. They've heard that the
              Spaghetti Carbonara recipe is perfect, but they need help
              adjusting the ingredients.
            </p>
            <p className="text-gray-700 mb-4">
              Find the Spaghetti Carbonara recipe in our{" "}
              <Link to="/recipes" className="text-blue-600 hover:text-blue-800">
                recipe collection
              </Link>{" "}
              and calculate how many grams of pancetta they'll need for 8
              servings.
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How many grams of pancetta are needed?
            </label>
            <div className="flex gap-4">
              <input
                type="number"
                step="0.01"
                className="flex-1 px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Enter amount in grams..."
              />
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                Check Answer
              </button>
            </div>
          </div>

          {message && (
            <div
              className={`p-4 rounded-lg ${
                password ? "bg-green-50" : "bg-red-50"
              }`}
            >
              <p className={`${password ? "text-green-800" : "text-red-800"}`}>
                {message}
              </p>
              {password && (
                <p className="mt-2 font-bold text-green-800">
                  Password: {password}
                </p>
              )}
            </div>
          )}
        </div>
        <div className="flex justify-center mt-6">
          <Link
            to="/recipes"
            className="inline-flex items-center px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors duration-200"
          >
            Go to recipe site →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RecipeCalculator;
