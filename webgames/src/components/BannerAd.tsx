import React from "react";
import { useNavigate } from "react-router-dom";

// Predefined set of ads
const ADS = [
  {
    title: "Spaghetti Carbonara",
    emoji: "🍝",
    description:
      "Creamy pasta perfection with pancetta, eggs and Pecorino Romano. Learn this authentic Italian recipe today!",
    backgroundColor: "bg-orange-100",
    textColor: "text-orange-900",
    category: "recipe",
  },
  {
    title: "Thai Green Curry",
    emoji: "🥘",
    description:
      "Aromatic coconut curry with fresh vegetables and tender chicken. Master this takeout favorite at home!",
    backgroundColor: "bg-green-100",
    textColor: "text-green-900",
    category: "recipe",
  },
  {
    title: "Perfect French Croissants",
    emoji: "🥐",
    description:
      "Buttery, flaky layers of pure bliss. Our step-by-step guide makes this classic pastry achievable!",
    backgroundColor: "bg-yellow-100",
    textColor: "text-yellow-900",
    category: "recipe",
  },
  {
    title: "Japanese Ramen From Scratch",
    emoji: "🍜",
    description:
      "Rich tonkotsu broth, handmade noodles, and all the toppings. Restaurant quality ramen at home!",
    backgroundColor: "bg-red-100",
    textColor: "text-red-900",
    category: "recipe",
  },
  {
    title: "Limited Time Offer!",
    emoji: "🎉",
    description:
      "Get 50% off your first month of premium subscription. Don't miss out on this amazing deal!",
    backgroundColor: "bg-purple-100",
    textColor: "text-purple-900",
    category: "general",
  },
  {
    title: "AI Writing Assistant",
    emoji: "🤖",
    description:
      "Write better content 10x faster with our AI-powered writing tool. Try it free for 7 days!",
    backgroundColor: "bg-pink-100",
    textColor: "text-pink-900",
    category: "general",
  },
  {
    title: "Buy stocks now!",
    emoji: "📈",
    description:
      "Get our expert analysis on TSLA, META, MSFT, and more. Start trading with zero fees!",
    backgroundColor: "bg-blue-100",
    textColor: "text-blue-900",
    category: "finance",
  },
];

interface BannerAdProps {
  index?: number; // Optional index to select a specific ad
  category?: "recipe" | "general" | "finance"; // Optional category to filter ads
}

const BannerAd: React.FC<BannerAdProps> = ({ index, category }) => {
  const navigate = useNavigate();

  // Filter ads by category if specified
  const filteredAds = category
    ? ADS.filter((ad) => ad.category === category)
    : ADS;

  // Select an ad either by index or randomly from filtered ads
  const ad =
    index !== undefined
      ? filteredAds[index % filteredAds.length]
      : filteredAds[Math.floor(Math.random() * filteredAds.length)];

  return (
    <div className="relative max-w-2xl mx-auto">
      {/* Vertical "Advertisement" text */}
      <div className="absolute -left-6 top-1/2 -translate-y-1/2 -rotate-90 text-xs tracking-widest text-gray-400 uppercase origin-center select-none">
        Advertisement
      </div>

      <div
        onClick={() => navigate("/ad-clicked")}
        className={`w-full p-6 ${ad.backgroundColor} rounded-lg shadow-lg my-8 ml-4 border-2 border-dashed border-gray-300 cursor-pointer hover:shadow-xl transition-shadow duration-200`}
      >
        <div className="flex flex-col items-center text-center gap-4">
          {/* Emoji */}
          <div className="text-6xl mb-2">{ad.emoji}</div>
          <div className="flex-1">
            <span className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">
              Sponsored
            </span>
            <h3 className={`text-2xl font-extrabold ${ad.textColor} mb-2`}>
              {ad.title}
            </h3>
            <p className={`${ad.textColor} opacity-90 text-lg`}>
              {ad.description}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BannerAd;
