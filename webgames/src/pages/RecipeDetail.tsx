import React from "react";
import { useParams } from "react-router-dom";
import BannerAd from "../components/BannerAd";
import { getAverageRating, recipes } from "./recipes/recipes";

export default function RecipeDetail() {
  const { recipeId } = useParams();
  const recipe = recipes.find((r) => r.id === parseInt(recipeId || ""));

  if (!recipe) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800">Recipe not found</h1>
        </div>
      </div>
    );
  }

  const avgRating = getAverageRating(recipe);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Top Banner Ad */}
      <div className="mb-8">
        <BannerAd category="recipe" />
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <span className="text-6xl">{recipe.imageEmoji}</span>
            <div>
              <h1 className="text-3xl font-bold mb-2">{recipe.name}</h1>
              <p className="text-gray-600">{recipe.description}</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <div className="flex items-center">
              <span className="text-yellow-400 text-xl mr-1">⭐</span>
              <span className="font-semibold">{avgRating}</span>
              <span className="ml-1">({recipe.reviews.length} reviews)</span>
            </div>
            <div>🕒 Prep: {recipe.prepTime} mins</div>
            <div>👨‍🍳 Cook: {recipe.cookTime} mins</div>
            <div>🍽️ Serves: {recipe.servings}</div>
            <div
              className={`
              ${recipe.difficulty === "Easy" ? "text-green-500" : ""}
              ${recipe.difficulty === "Medium" ? "text-yellow-500" : ""}
              ${recipe.difficulty === "Hard" ? "text-red-500" : ""}
            `}
            >
              {recipe.difficulty}
            </div>
          </div>
        </div>

        {/* Pre-content Banner Ad */}
        <div className="mb-8">
          <BannerAd category="general" />
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-3 gap-8">
          {/* Left Side Banner */}
          <div className="hidden lg:block">
            <div className="sticky top-4">
              <BannerAd category="recipe" />
            </div>
          </div>

          {/* Ingredients */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Ingredients</h2>
              <ul className="space-y-2">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index} className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-3 h-4 w-4 text-blue-500 rounded"
                    />
                    <span>
                      {ingredient.amount} {ingredient.unit} {ingredient.item}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Mid-content Banner Ad */}
            <div className="mt-8">
              <BannerAd category="general" />
            </div>
          </div>

          {/* Instructions */}
          <div className="md:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Instructions</h2>
              <ol className="space-y-4">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex">
                    <span className="font-bold mr-4">{index + 1}.</span>
                    <span>{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {/* Right Side Banner */}
          <div className="hidden lg:block">
            <div className="sticky top-4">
              <BannerAd category="recipe" />
            </div>
          </div>
        </div>

        {/* Pre-reviews Banner Ad */}
        <div className="my-8">
          <BannerAd category="general" />
        </div>

        {/* Reviews */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-4">Reviews</h2>
          <div className="space-y-4">
            {recipe.reviews.map((review, index) => (
              <React.Fragment key={review.id}>
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold">{review.userId}</div>
                    <div className="flex items-center">
                      <span className="text-yellow-400 mr-1">⭐</span>
                      <span>{review.rating}</span>
                    </div>
                  </div>
                  <p className="text-gray-600">{review.comment}</p>
                </div>
                {/* Add banner ad after every 3 reviews */}
                {(index + 1) % 3 === 0 && index < recipe.reviews.length - 1 && (
                  <div className="my-4">
                    <BannerAd
                      category={index % 2 === 0 ? "recipe" : "general"}
                    />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Bottom Banner Ads */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <BannerAd category="recipe" />
          <BannerAd category="general" />
        </div>
      </div>
    </div>
  );
}
