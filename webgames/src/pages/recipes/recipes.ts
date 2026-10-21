export interface Review {
  id: number;
  userId: string;
  rating: number; // 1-5
  comment: string;
  date: string;
}

export interface Recipe {
  id: number;
  name: string;
  description: string;
  imageEmoji: string; // Using emojis for now, can be replaced with real images
  prepTime: number; // in minutes
  cookTime: number; // in minutes
  servings: number;
  difficulty: "Easy" | "Medium" | "Hard";
  ingredients: {
    item: string;
    amount: number;
    unit: string;
  }[];
  instructions: string[];
  category:
    | "Main Course"
    | "Appetizer"
    | "Dessert"
    | "Breakfast"
    | "Soup"
    | "Salad"
    | "Snack";
  cuisine:
    | "Italian"
    | "Mexican"
    | "Chinese"
    | "Japanese"
    | "Indian"
    | "American"
    | "French"
    | "Mediterranean"
    | "Thai"
    | "Vietnamese";
  reviews: Review[];
  tags: string[];
}

// Helper function to calculate average rating
export const getAverageRating = (recipe: Recipe): number => {
  if (recipe.reviews.length === 0) return 0;
  const sum = recipe.reviews.reduce((acc, review) => acc + review.rating, 0);
  return Math.round((sum / recipe.reviews.length) * 10) / 10;
};

// Initial recipes data
export const recipes: Recipe[] = [
  {
    id: 1,
    name: "Beef Bourguignon",
    description:
      "A classic French stew with beef braised in red wine, beef broth, and vegetables",
    imageEmoji: "🍲",
    prepTime: 30,
    cookTime: 180,
    servings: 6,
    difficulty: "Medium",
    ingredients: [
      { item: "beef chuck", amount: 1500, unit: "g" },
      { item: "red wine", amount: 750, unit: "ml" },
      { item: "beef broth", amount: 500, unit: "ml" },
      { item: "bacon", amount: 200, unit: "g" },
      { item: "onion", amount: 2, unit: "pieces" },
      { item: "carrots", amount: 3, unit: "pieces" },
      { item: "garlic", amount: 3, unit: "cloves" },
      { item: "tomato paste", amount: 2, unit: "tbsp" },
      { item: "thyme", amount: 1, unit: "tsp" },
      { item: "bay leaves", amount: 2, unit: "pieces" },
      { item: "mushrooms", amount: 250, unit: "g" },
      { item: "pearl onions", amount: 200, unit: "g" },
    ],
    instructions: [
      "Cut beef into cubes and brown in a large pot",
      "Remove beef and sauté bacon until crispy",
      "Add onions, carrots, and garlic to the pot",
      "Stir in tomato paste, thyme, and bay leaves",
      "Pour in red wine and beef broth",
      "Return beef to the pot and simmer for 2-3 hours",
      "In a separate pan, sauté mushrooms and pearl onions",
      "Add mushrooms and pearl onions to the stew in the last 30 minutes",
    ],
    category: "Main Course",
    cuisine: "French",
    reviews: [
      {
        id: 30,
        userId: "frenchCuisine",
        rating: 5,
        comment: "Absolutely delicious, just like in Paris!",
        date: "2024-03-26",
      },
      {
        id: 31,
        userId: "stewLover",
        rating: 4,
        comment: "Rich and flavorful, perfect for a cold evening",
        date: "2024-03-25",
      },
    ],
    tags: ["stew", "french", "beef", "wine", "hearty"],
  },
  {
    id: 2,
    name: "Chocolate Chip Cookies",
    description:
      "Classic chewy chocolate chip cookies that are crispy on the outside, soft on the inside",
    imageEmoji: "🍪",
    prepTime: 20,
    cookTime: 12,
    servings: 24,
    difficulty: "Easy",
    ingredients: [
      { item: "all-purpose flour", amount: 280, unit: "g" },
      { item: "butter", amount: 230, unit: "g" },
      { item: "brown sugar", amount: 200, unit: "g" },
      { item: "white sugar", amount: 100, unit: "g" },
      { item: "eggs", amount: 2, unit: "pieces" },
      { item: "vanilla extract", amount: 2, unit: "tsp" },
      { item: "chocolate chips", amount: 340, unit: "g" },
    ],
    instructions: [
      "Cream together butter and sugars",
      "Beat in eggs and vanilla",
      "Mix in dry ingredients",
      "Fold in chocolate chips",
      "Drop spoonfuls onto baking sheet",
      "Bake at 375°F for 10-12 minutes",
    ],
    category: "Dessert",
    cuisine: "American",
    reviews: [
      {
        id: 3,
        userId: "baker789",
        rating: 5,
        comment: "Best cookie recipe ever!",
        date: "2024-03-10",
      },
    ],
    tags: ["dessert", "cookies", "chocolate", "baking"],
  },
  {
    id: 3,
    name: "Chicken Tikka Masala",
    description:
      "A rich and creamy curry with tender chicken pieces in a spiced tomato sauce",
    imageEmoji: "🍛",
    prepTime: 30,
    cookTime: 45,
    servings: 6,
    difficulty: "Medium",
    ingredients: [
      { item: "chicken breast", amount: 750, unit: "g" },
      { item: "yogurt", amount: 200, unit: "g" },
      { item: "tomato sauce", amount: 400, unit: "g" },
      { item: "heavy cream", amount: 200, unit: "ml" },
      { item: "garam masala", amount: 2, unit: "tbsp" },
      { item: "turmeric", amount: 1, unit: "tsp" },
      { item: "ginger", amount: 2, unit: "tbsp" },
      { item: "garlic", amount: 4, unit: "cloves" },
    ],
    instructions: [
      "Marinate chicken in yogurt and spices",
      "Grill chicken until charred",
      "Prepare sauce with tomatoes and cream",
      "Combine chicken and sauce",
      "Simmer until thickened",
    ],
    category: "Main Course",
    cuisine: "Indian",
    reviews: [
      {
        id: 4,
        userId: "spiceLover",
        rating: 5,
        comment: "Perfect balance of spices!",
        date: "2024-03-12",
      },
    ],
    tags: ["curry", "indian", "chicken", "spicy"],
  },
  {
    id: 4,
    name: "Sushi Rolls",
    description:
      "Fresh and delicious California rolls with crab, avocado, and cucumber",
    imageEmoji: "🍱",
    prepTime: 45,
    cookTime: 30,
    servings: 4,
    difficulty: "Hard",
    ingredients: [
      { item: "sushi rice", amount: 400, unit: "g" },
      { item: "nori sheets", amount: 6, unit: "pieces" },
      { item: "crab meat", amount: 200, unit: "g" },
      { item: "avocado", amount: 2, unit: "pieces" },
      { item: "cucumber", amount: 1, unit: "piece" },
      { item: "rice vinegar", amount: 60, unit: "ml" },
    ],
    instructions: [
      "Cook sushi rice and season with vinegar",
      "Prepare fillings",
      "Assemble rolls with nori",
      "Roll tightly and slice",
    ],
    category: "Main Course",
    cuisine: "Japanese",
    reviews: [
      {
        id: 5,
        userId: "sushiMaster",
        rating: 4,
        comment: "Great starter sushi recipe",
        date: "2024-03-10",
      },
    ],
    tags: ["sushi", "japanese", "seafood", "rice"],
  },
  {
    id: 5,
    name: "Beef Tacos",
    description:
      "Authentic Mexican tacos with seasoned ground beef and fresh toppings",
    imageEmoji: "🌮",
    prepTime: 20,
    cookTime: 25,
    servings: 6,
    difficulty: "Easy",
    ingredients: [
      { item: "ground beef", amount: 500, unit: "g" },
      { item: "taco seasoning", amount: 2, unit: "tbsp" },
      { item: "corn tortillas", amount: 12, unit: "pieces" },
      { item: "onion", amount: 1, unit: "piece" },
      { item: "cilantro", amount: 1, unit: "bunch" },
      { item: "lime", amount: 2, unit: "pieces" },
    ],
    instructions: [
      "Brown the ground beef",
      "Add seasoning and simmer",
      "Warm tortillas",
      "Assemble tacos with toppings",
    ],
    category: "Main Course",
    cuisine: "Mexican",
    reviews: [
      {
        id: 6,
        userId: "tacoTuesday",
        rating: 5,
        comment: "So simple yet delicious!",
        date: "2024-03-08",
      },
    ],
    tags: ["tacos", "mexican", "beef", "quick"],
  },
  {
    id: 6,
    name: "French Croissants",
    description: "Flaky, buttery croissants made from scratch",
    imageEmoji: "🥐",
    prepTime: 120,
    cookTime: 25,
    servings: 12,
    difficulty: "Hard",
    ingredients: [
      { item: "all-purpose flour", amount: 500, unit: "g" },
      { item: "butter", amount: 250, unit: "g" },
      { item: "yeast", amount: 7, unit: "g" },
      { item: "milk", amount: 300, unit: "ml" },
      { item: "sugar", amount: 50, unit: "g" },
      { item: "salt", amount: 10, unit: "g" },
    ],
    instructions: [
      "Make dough and chill",
      "Laminate with butter",
      "Shape croissants",
      "Proof and bake",
    ],
    category: "Breakfast",
    cuisine: "French",
    reviews: [
      {
        id: 7,
        userId: "pastryCook",
        rating: 4,
        comment: "Takes practice but worth it!",
        date: "2024-03-05",
      },
    ],
    tags: ["pastry", "french", "breakfast", "baking"],
  },
  {
    id: 7,
    name: "Thai Green Curry",
    description:
      "Aromatic and spicy Thai curry with coconut milk, vegetables, and your choice of protein",
    imageEmoji: "🥘",
    prepTime: 25,
    cookTime: 35,
    servings: 4,
    difficulty: "Medium",
    ingredients: [
      { item: "coconut milk", amount: 400, unit: "ml" },
      { item: "green curry paste", amount: 3, unit: "tbsp" },
      { item: "chicken breast", amount: 500, unit: "g" },
      { item: "bamboo shoots", amount: 200, unit: "g" },
      { item: "bell peppers", amount: 2, unit: "pieces" },
      { item: "fish sauce", amount: 2, unit: "tbsp" },
      { item: "palm sugar", amount: 1, unit: "tbsp" },
      { item: "thai basil", amount: 1, unit: "cup" },
    ],
    instructions: [
      "Heat coconut cream until oil separates",
      "Fry curry paste until fragrant",
      "Add chicken and cook until sealed",
      "Add remaining coconut milk and simmer",
      "Add vegetables and season",
      "Finish with thai basil",
    ],
    category: "Main Course",
    cuisine: "Thai",
    reviews: [
      {
        id: 8,
        userId: "curryKing",
        rating: 5,
        comment: "Authentic taste, just like in Bangkok!",
        date: "2024-03-01",
      },
      {
        id: 9,
        userId: "spiceLover",
        rating: 4,
        comment: "Great flavor but could be spicier",
        date: "2024-02-28",
      },
    ],
    tags: ["curry", "thai", "spicy", "coconut"],
  },
  {
    id: 8,
    name: "Homemade Pizza",
    description:
      "Classic Neapolitan-style pizza with a crispy crust and fresh toppings",
    imageEmoji: "🍕",
    prepTime: 120,
    cookTime: 15,
    servings: 4,
    difficulty: "Medium",
    ingredients: [
      { item: "bread flour", amount: 500, unit: "g" },
      { item: "yeast", amount: 7, unit: "g" },
      { item: "olive oil", amount: 30, unit: "ml" },
      { item: "salt", amount: 10, unit: "g" },
      { item: "tomato sauce", amount: 200, unit: "g" },
      { item: "mozzarella", amount: 200, unit: "g" },
      { item: "basil", amount: 10, unit: "leaves" },
    ],
    instructions: [
      "Make dough and let rise for 2 hours",
      "Shape into pizza base",
      "Add sauce and toppings",
      "Bake at highest oven temperature",
      "Finish with fresh basil",
    ],
    category: "Main Course",
    cuisine: "Italian",
    reviews: [
      {
        id: 10,
        userId: "pizzaMaster",
        rating: 5,
        comment: "Perfect Neapolitan style!",
        date: "2024-03-05",
      },
      {
        id: 11,
        userId: "italianChef",
        rating: 4,
        comment: "Good recipe, but needs longer fermentation",
        date: "2024-03-02",
      },
    ],
    tags: ["pizza", "italian", "baking", "vegetarian"],
  },
  {
    id: 9,
    name: "Beef Pho",
    description:
      "Vietnamese noodle soup with rich beef broth, rice noodles, and fresh herbs",
    imageEmoji: "🍜",
    prepTime: 45,
    cookTime: 180,
    servings: 6,
    difficulty: "Hard",
    ingredients: [
      { item: "beef bones", amount: 2, unit: "kg" },
      { item: "rice noodles", amount: 500, unit: "g" },
      { item: "beef slices", amount: 300, unit: "g" },
      { item: "onion", amount: 2, unit: "pieces" },
      { item: "ginger", amount: 100, unit: "g" },
      { item: "star anise", amount: 3, unit: "pieces" },
      { item: "cinnamon stick", amount: 1, unit: "piece" },
      { item: "fish sauce", amount: 3, unit: "tbsp" },
    ],
    instructions: [
      "Simmer bones for 3 hours",
      "Toast spices and add to broth",
      "Cook noodles separately",
      "Assemble bowls with noodles and beef",
      "Pour hot broth over",
      "Serve with herbs and condiments",
    ],
    category: "Soup",
    cuisine: "Vietnamese",
    reviews: [
      {
        id: 12,
        userId: "phoFanatic",
        rating: 5,
        comment: "Worth the effort! Amazing depth of flavor",
        date: "2024-02-25",
      },
    ],
    tags: ["soup", "vietnamese", "beef", "noodles"],
  },
  {
    id: 10,
    name: "Greek Salad",
    description:
      "Fresh and crisp traditional Greek salad with feta cheese and olives",
    imageEmoji: "🥗",
    prepTime: 15,
    cookTime: 0,
    servings: 4,
    difficulty: "Easy",
    ingredients: [
      { item: "cucumber", amount: 1, unit: "large" },
      { item: "tomatoes", amount: 4, unit: "pieces" },
      { item: "red onion", amount: 1, unit: "medium" },
      { item: "feta cheese", amount: 200, unit: "g" },
      { item: "kalamata olives", amount: 100, unit: "g" },
      { item: "olive oil", amount: 60, unit: "ml" },
      { item: "oregano", amount: 1, unit: "tbsp" },
    ],
    instructions: [
      "Chop vegetables into chunks",
      "Add olives and feta",
      "Drizzle with olive oil",
      "Season with oregano and salt",
    ],
    category: "Salad",
    cuisine: "Mediterranean",
    reviews: [
      {
        id: 13,
        userId: "healthyEater",
        rating: 5,
        comment: "Simple and delicious!",
        date: "2024-03-08",
      },
      {
        id: 14,
        userId: "greekGourmet",
        rating: 5,
        comment: "Authentic recipe, just like in Greece",
        date: "2024-03-07",
      },
    ],
    tags: ["salad", "greek", "vegetarian", "fresh"],
  },
  {
    id: 11,
    name: "Miso Ramen",
    description:
      "Warming Japanese ramen with miso broth, fresh noodles, and traditional toppings",
    imageEmoji: "🍜",
    prepTime: 30,
    cookTime: 45,
    servings: 4,
    difficulty: "Medium",
    ingredients: [
      { item: "ramen noodles", amount: 400, unit: "g" },
      { item: "miso paste", amount: 100, unit: "g" },
      { item: "pork belly", amount: 300, unit: "g" },
      { item: "corn", amount: 200, unit: "g" },
      { item: "bamboo shoots", amount: 100, unit: "g" },
      { item: "nori sheets", amount: 4, unit: "pieces" },
      { item: "soft-boiled eggs", amount: 4, unit: "pieces" },
    ],
    instructions: [
      "Prepare miso broth",
      "Cook noodles al dente",
      "Slice chashu pork",
      "Prepare toppings",
      "Assemble bowls",
      "Serve hot",
    ],
    category: "Soup",
    cuisine: "Japanese",
    reviews: [
      {
        id: 15,
        userId: "ramenLover",
        rating: 5,
        comment: "Better than restaurant ramen!",
        date: "2024-03-10",
      },
      {
        id: 16,
        userId: "noodleMaster",
        rating: 4,
        comment: "Great recipe but needs more toppings",
        date: "2024-03-09",
      },
    ],
    tags: ["ramen", "japanese", "soup", "noodles"],
  },
  {
    id: 12,
    name: "Tiramisu",
    description:
      "Classic Italian dessert with layers of coffee-soaked ladyfingers and mascarpone cream",
    imageEmoji: "🍰",
    prepTime: 40,
    cookTime: 0,
    servings: 8,
    difficulty: "Medium",
    ingredients: [
      { item: "ladyfinger cookies", amount: 24, unit: "pieces" },
      { item: "mascarpone", amount: 500, unit: "g" },
      { item: "eggs", amount: 4, unit: "pieces" },
      { item: "strong coffee", amount: 300, unit: "ml" },
      { item: "sugar", amount: 100, unit: "g" },
      { item: "cocoa powder", amount: 30, unit: "g" },
      { item: "marsala wine", amount: 60, unit: "ml" },
    ],
    instructions: [
      "Make coffee and let cool",
      "Prepare mascarpone mixture",
      "Dip ladyfingers in coffee",
      "Layer cookies and cream",
      "Dust with cocoa",
      "Chill for 4 hours",
    ],
    category: "Dessert",
    cuisine: "Italian",
    reviews: [
      {
        id: 17,
        userId: "dessertPro",
        rating: 5,
        comment: "Perfect balance of coffee and cream",
        date: "2024-03-12",
      },
      {
        id: 18,
        userId: "italianDesserts",
        rating: 5,
        comment: "Just like my nonna's recipe!",
        date: "2024-03-11",
      },
      {
        id: 19,
        userId: "coffeeLover",
        rating: 4,
        comment: "Delicious but could use more coffee",
        date: "2024-03-10",
      },
    ],
    tags: ["dessert", "italian", "coffee", "no-bake"],
  },
  {
    id: 13,
    name: "Butter Chicken",
    description:
      "Rich and creamy Indian curry with tender chicken in a tomato-based sauce",
    imageEmoji: "🍛",
    prepTime: 30,
    cookTime: 40,
    servings: 6,
    difficulty: "Medium",
    ingredients: [
      { item: "chicken thighs", amount: 800, unit: "g" },
      { item: "yogurt", amount: 200, unit: "g" },
      { item: "butter", amount: 100, unit: "g" },
      { item: "tomato puree", amount: 400, unit: "g" },
      { item: "heavy cream", amount: 200, unit: "ml" },
      { item: "garam masala", amount: 2, unit: "tbsp" },
      { item: "kasuri methi", amount: 1, unit: "tbsp" },
    ],
    instructions: [
      "Marinate chicken in spiced yogurt",
      "Grill or bake chicken",
      "Prepare makhani sauce",
      "Combine chicken and sauce",
      "Finish with cream and butter",
    ],
    category: "Main Course",
    cuisine: "Indian",
    reviews: [
      {
        id: 20,
        userId: "curryKing",
        rating: 5,
        comment: "Restaurant quality at home!",
        date: "2024-03-15",
      },
      {
        id: 21,
        userId: "indianFoodie",
        rating: 5,
        comment: "Perfect balance of spices",
        date: "2024-03-14",
      },
    ],
    tags: ["curry", "indian", "chicken", "creamy"],
  },
  {
    id: 14,
    name: "Miso Soup",
    description:
      "A traditional Japanese soup with dashi broth, miso paste, tofu, and seaweed",
    imageEmoji: "🍜",
    prepTime: 10,
    cookTime: 10,
    servings: 2,
    difficulty: "Easy",
    ingredients: [
      { item: "dashi stock", amount: 500, unit: "ml" },
      { item: "miso paste", amount: 2, unit: "tbsp" },
      { item: "silken tofu", amount: 150, unit: "g" },
      { item: "wakame seaweed", amount: 2, unit: "tbsp" },
      { item: "green onions", amount: 1, unit: "stalk" },
    ],
    instructions: [
      "Heat dashi stock in a saucepan",
      "Dissolve miso paste in a small amount of the hot stock",
      "Add the miso mixture back to the saucepan",
      "Add tofu and wakame seaweed",
      "Simmer gently for a few minutes",
      "Garnish with sliced green onions",
    ],
    category: "Soup",
    cuisine: "Japanese",
    reviews: [
      {
        id: 22,
        userId: "soupLover",
        rating: 4,
        comment: "Simple and comforting",
        date: "2024-03-16",
      },
    ],
    tags: ["soup", "japanese", "tofu", "seaweed", "healthy"],
  },
  {
    id: 15,
    name: "Caprese Salad",
    description:
      "A simple and refreshing Italian salad with fresh mozzarella, tomatoes, and basil",
    imageEmoji: "🥗",
    prepTime: 10,
    cookTime: 0,
    servings: 2,
    difficulty: "Easy",
    ingredients: [
      { item: "fresh mozzarella", amount: 200, unit: "g" },
      { item: "tomatoes", amount: 2, unit: "pieces" },
      { item: "fresh basil leaves", amount: 1, unit: "cup" },
      { item: "extra virgin olive oil", amount: 2, unit: "tbsp" },
      { item: "balsamic glaze", amount: 1, unit: "tbsp" },
      { item: "salt", amount: 1, unit: "pinch" },
      { item: "black pepper", amount: 1, unit: "pinch" },
    ],
    instructions: [
      "Slice the mozzarella and tomatoes",
      "Arrange the mozzarella, tomatoes, and basil leaves on a plate",
      "Drizzle with olive oil and balsamic glaze",
      "Season with salt and pepper",
    ],
    category: "Salad",
    cuisine: "Italian",
    reviews: [
      {
        id: 23,
        userId: "saladLover",
        rating: 5,
        comment: "So fresh and delicious!",
        date: "2024-03-17",
      },
    ],
    tags: ["salad", "italian", "vegetarian", "quick", "fresh"],
  },
  {
    id: 16,
    name: "Chicken Stir-Fry",
    description:
      "A quick and easy stir-fry with chicken and mixed vegetables in a savory sauce",
    imageEmoji: "🥡",
    prepTime: 15,
    cookTime: 20,
    servings: 4,
    difficulty: "Easy",
    ingredients: [
      { item: "chicken breast", amount: 500, unit: "g" },
      { item: "broccoli florets", amount: 2, unit: "cups" },
      { item: "carrots", amount: 2, unit: "pieces" },
      { item: "soy sauce", amount: 4, unit: "tbsp" },
      { item: "ginger", amount: 1, unit: "tbsp" },
      { item: "garlic", amount: 2, unit: "cloves" },
      { item: "sesame oil", amount: 2, unit: "tbsp" },
    ],
    instructions: [
      "Cut chicken into bite-sized pieces",
      "Heat sesame oil in a wok or large skillet",
      "Add chicken and cook until browned",
      "Add vegetables and stir-fry for 5 minutes",
      "Add soy sauce, ginger, and garlic",
      "Cook until sauce thickens",
    ],
    category: "Main Course",
    cuisine: "Chinese",
    reviews: [
      {
        id: 24,
        userId: "stirFryFan",
        rating: 5,
        comment: "Super easy and delicious!",
        date: "2024-03-18",
      },
      {
        id: 25,
        userId: "veggieLover",
        rating: 4,
        comment: "Great way to get my veggies in!",
        date: "2024-03-17",
      },
    ],
    tags: ["stir-fry", "chinese", "chicken", "vegetables", "quick"],
  },
  {
    id: 17,
    name: "Mango Sticky Rice",
    description:
      "A classic Thai dessert made with sweet sticky rice, fresh mango, and coconut milk",
    imageEmoji: "🥭",
    prepTime: 20,
    cookTime: 30,
    servings: 4,
    difficulty: "Medium",
    ingredients: [
      { item: "sticky rice", amount: 300, unit: "g" },
      { item: "coconut milk", amount: 400, unit: "ml" },
      { item: "sugar", amount: 100, unit: "g" },
      { item: "salt", amount: 0.5, unit: "tsp" },
      { item: "ripe mangoes", amount: 2, unit: "pieces" },
    ],
    instructions: [
      "Soak sticky rice for at least 4 hours or overnight",
      "Steam sticky rice until cooked",
      "Heat coconut milk, sugar, and salt in a saucepan",
      "Simmer until sugar is dissolved",
      "Mix cooked sticky rice with coconut milk mixture",
      "Serve with sliced mangoes",
    ],
    category: "Dessert",
    cuisine: "Thai",
    reviews: [
      {
        id: 28,
        userId: "sweetTooth",
        rating: 5,
        comment: "My favorite Thai dessert!",
        date: "2024-03-22",
      },
      {
        id: 29,
        userId: "mangoFan",
        rating: 4,
        comment: "Perfectly sweet and creamy",
        date: "2024-03-21",
      },
    ],
    tags: ["dessert", "thai", "mango", "coconut", "sweet"],
  },
  {
    id: 18,
    name: "Classic Spaghetti Carbonara",
    description:
      "A traditional Italian pasta dish with eggs, cheese, pancetta and black pepper",
    imageEmoji: "🍝",
    prepTime: 15,
    cookTime: 20,
    servings: 4,
    difficulty: "Medium",
    ingredients: [
      { item: "spaghetti", amount: 400, unit: "g" },
      { item: "pancetta", amount: 200, unit: "g" },
      { item: "egg yolks", amount: 4, unit: "pieces" },
      { item: "Pecorino Romano", amount: 50, unit: "g" },
      { item: "Parmigiano Reggiano", amount: 50, unit: "g" },
      { item: "black pepper", amount: 2, unit: "tsp" },
    ],
    instructions: [
      "Bring a large pot of salted water to boil",
      "Cook spaghetti according to package instructions",
      "While pasta cooks, fry pancetta until crispy",
      "Mix egg yolks with grated cheeses",
      "Combine hot pasta with pancetta, then mix in egg mixture",
      "Season generously with black pepper",
    ],
    category: "Main Course",
    cuisine: "Italian",
    reviews: [
      {
        id: 1,
        userId: "user123",
        rating: 5,
        comment: "Perfect recipe! Just like in Rome!",
        date: "2024-03-15",
      },
      {
        id: 2,
        userId: "chef456",
        rating: 4,
        comment: "Great recipe, but I'd add more pepper",
        date: "2024-03-14",
      },
    ],
    tags: ["pasta", "italian", "quick", "eggs", "cheese"],
  },
];
