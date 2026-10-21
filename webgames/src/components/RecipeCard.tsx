import React from "react";
import { Recipe } from "../pages/recipes/recipes";

interface RecipeCardProps {
  recipe: Recipe;
  isSelected?: boolean;
  onClick?: (recipe: Recipe) => void;
}

const RecipeCard: React.FC<RecipeCardProps> = ({
  recipe,
  isSelected = false,
  onClick,
}) => {
  return (
    <div
      className={`bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer ${
        isSelected ? "ring-2 ring-blue-500" : ""
      }`}
      onClick={() => onClick?.(recipe)}
    >
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-4xl">{recipe.imageEmoji}</span>
          <div className="text-right">
            <div className="flex items-center">
              <span className="text-gray-500 text-sm">
                {recipe.prepTime + recipe.cookTime} mins
              </span>
            </div>
          </div>
        </div>

        <h3 className="text-xl font-bold mb-2">{recipe.name}</h3>
        <p className="text-gray-600 text-sm mb-3">{recipe.description}</p>

        <div className="flex flex-wrap gap-2 mb-3">
          {recipe.tags.map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="flex justify-between text-sm text-gray-500">
          <span>{recipe.cuisine}</span>
          <span
            className={`
            ${recipe.difficulty === "Easy" ? "text-green-500" : ""}
            ${recipe.difficulty === "Medium" ? "text-yellow-500" : ""}
            ${recipe.difficulty === "Hard" ? "text-red-500" : ""}
          `}
          >
            {recipe.difficulty}
          </span>
        </div>
      </div>
    </div>
  );
};

export default RecipeCard;
