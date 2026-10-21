import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import BannerAd from "../components/BannerAd";
import RecipeCard from "../components/RecipeCard";
import { recipes } from "./recipes/recipes";

export default function RecipeList() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedCuisine, setSelectedCuisine] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearchTerm, setActiveSearchTerm] = useState("");
  const itemsPerPage = 6;

  const categories = ["All", ...new Set(recipes.map((p) => p.category))];
  const cuisines = ["All", ...new Set(recipes.map((p) => p.cuisine))];

  const filteredRecipes = recipes.filter((recipe) => {
    const matchesSearch = activeSearchTerm
      ? recipe.name.toLowerCase().includes(activeSearchTerm.toLowerCase()) ||
        recipe.description
          .toLowerCase()
          .includes(activeSearchTerm.toLowerCase()) ||
        recipe.tags.some((tag) =>
          tag.toLowerCase().includes(activeSearchTerm.toLowerCase())
        )
      : true;

    const matchesCategory =
      selectedCategory === "All" || recipe.category === selectedCategory;
    const matchesCuisine =
      selectedCuisine === "All" || recipe.cuisine === selectedCuisine;

    return matchesSearch && matchesCategory && matchesCuisine;
  });

  const totalPages = Math.ceil(filteredRecipes.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const displayedRecipes = filteredRecipes.slice(
    startIndex,
    startIndex + itemsPerPage
  );

  const handleSearch = () => {
    setActiveSearchTerm(searchTerm);
    setCurrentPage(1);
  };

  return (
    <div>
      {/* Main Navigation Header */}
      <nav className="bg-white border-b border-gray-200">
        {/* Top Bar */}
        <div className="container mx-auto px-4 py-2 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button className="text-gray-600 hover:text-blue-500">
              Subscribe
            </button>
            <button className="text-gray-600 hover:text-blue-500">
              Sign In
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-gray-600 hover:text-blue-500">
              Join PRO
            </button>
            <button className="bg-blue-500 text-white px-4 py-1 rounded-full hover:bg-blue-600">
              Get the Magazine
            </button>
          </div>
        </div>

        {/* Main Navigation */}
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold">Recipe Book</h1>
            <div className="relative">
              <input
                type="text"
                placeholder="Search recipes, ingredients, tips..."
                className="w-[300px] px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6 text-sm">
            <div className="group relative">
              <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
                RECIPES ▾
              </button>
              <div className="absolute hidden group-hover:block w-48 bg-white border shadow-lg rounded-lg mt-1 py-2 z-50">
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Quick & Easy
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Breakfast
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Lunch
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Dinner
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Desserts
                </a>
              </div>
            </div>
            <div className="group relative">
              <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
                INGREDIENTS ▾
              </button>
              <div className="absolute hidden group-hover:block w-48 bg-white border shadow-lg rounded-lg mt-1 py-2 z-50">
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Meat & Poultry
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Seafood
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Vegetables
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Fruits
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Grains
                </a>
              </div>
            </div>
            <div className="group relative">
              <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
                OCCASIONS ▾
              </button>
              <div className="absolute hidden group-hover:block w-48 bg-white border shadow-lg rounded-lg mt-1 py-2 z-50">
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Holidays
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Birthday
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Game Day
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Parties
                </a>
              </div>
            </div>
            <div className="group relative">
              <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
                CUISINES ▾
              </button>
              <div className="absolute hidden group-hover:block w-48 bg-white border shadow-lg rounded-lg mt-1 py-2 z-50">
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Italian
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Mexican
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Asian
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Mediterranean
                </a>
              </div>
            </div>
            <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
              TIPS & TECHNIQUES
            </button>
            <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
              NEWS
            </button>
            <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
              FEATURES
            </button>
            <div className="group relative">
              <button className="py-2 text-gray-700 hover:text-blue-500 font-medium">
                MORE ▾
              </button>
              <div className="absolute hidden group-hover:block w-48 bg-white border shadow-lg rounded-lg mt-1 py-2 z-50 right-0">
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  About Us
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Contact
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Careers
                </a>
                <a href="#" className="block px-4 py-2 hover:bg-gray-100">
                  Advertise
                </a>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Top Banner Ad */}
        <div className="mb-8">
          <BannerAd category="recipe" />
        </div>

        {/* Secondary Banner Ad */}
        <div className="mb-8">
          <BannerAd category="general" />
        </div>

        {/* Filters and Search */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-4 justify-between items-center">
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => {
                    setSelectedCategory(category);
                    setCurrentPage(1);
                  }}
                  className={`px-4 py-2 rounded ${
                    selectedCategory === category
                      ? "bg-blue-500 text-white"
                      : "bg-gray-200"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <select
                className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                value={selectedCuisine}
                onChange={(e) => {
                  setSelectedCuisine(e.target.value);
                  setCurrentPage(1);
                }}
              >
                {cuisines.map((cuisine) => (
                  <option key={cuisine} value={cuisine}>
                    {cuisine}
                  </option>
                ))}
              </select>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search recipes..."
                  className="px-4 py-2 border rounded"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSearch();
                    }
                  }}
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Search
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Side Banner Ad */}
        <div className="lg:flex gap-8">
          <div className="hidden lg:block w-64 shrink-0">
            <div className="sticky top-4">
              <BannerAd />
            </div>
          </div>

          <div className="flex-1">
            {/* Recipe Grid with Interspersed Ads */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6 mb-8">
              {displayedRecipes.map((recipe, index) => (
                <React.Fragment key={recipe.id}>
                  <RecipeCard
                    recipe={recipe}
                    onClick={(recipe) => navigate(`/recipes/${recipe.id}`)}
                  />
                  {/* Add banner ad after every 2 recipes (increased frequency) */}
                  {(index + 1) % 2 === 0 &&
                    index < displayedRecipes.length - 1 && (
                      <div className="col-span-full my-4">
                        <BannerAd />
                      </div>
                    )}
                </React.Fragment>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex justify-center space-x-4 mb-8">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() =>
                  setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                }
                disabled={currentPage === totalPages}
                className="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>

          {/* Right Side Banner Ad */}
          <div className="hidden lg:block w-64 shrink-0">
            <div className="sticky top-4">
              <BannerAd />
            </div>
          </div>
        </div>

        {/* Bottom Banner Ads */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <BannerAd />
          <BannerAd />
        </div>
      </div>
    </div>
  );
}
