import React, { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";
interface DataPoint {
  time: string;
  price: number;
}

export const TASK_ID_ChartRead = "chart-read";
export const PASSWORD_ChartRead = "CHART_MASTER_2024";

const ChartRead: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ChartRead);
  const [data, setData] = useState<DataPoint[]>([]);
  const [maxPrice, setMaxPrice] = useState("");
  const [maxTime, setMaxTime] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState("");

  // Generate random stock data when component mounts
  useEffect(() => {
    const generateData = () => {
      const points: DataPoint[] = [];
      const maxPoints = 24; // One point per hour

      // Choose a random hour for the spike between hours 6 and 18
      const spikeHour = 6 + Math.floor(Math.random() * 12);

      for (let i = 0; i < maxPoints; i++) {
        let price;

        // Calculate distance from spike
        const distanceFromSpike = Math.abs(i - spikeHour);

        if (i === spikeHour) {
          // The spike point
          price = 250 + Math.random() * 30;
        } else if (distanceFromSpike <= 2) {
          // Points near the spike
          price = 180 - distanceFromSpike * 40 + (Math.random() - 0.5) * 20;
        } else {
          // Base price with small fluctuations
          price = 100 + Math.sin(i * 0.5) * 20 + (Math.random() - 0.5) * 15;
        }

        // Ensure price stays within bounds
        price = Math.max(70, Math.min(280, price));

        const hour = i.toString().padStart(2, "0");
        points.push({
          time: `${hour}:00`,
          price: Math.round(price * 100) / 100,
        });
      }
      return points;
    };

    const newData = generateData();
    setData(newData);
  }, []);

  const actualMax = data.reduce(
    (max, point) => (point.price > max.price ? point : max),
    { time: "", price: -Infinity }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const submittedPrice = parseFloat(maxPrice);
    const priceThreshold = actualMax.price * 0.05; // 5% tolerance

    if (
      Math.abs(submittedPrice - actualMax.price) <= priceThreshold &&
      maxTime === actualMax.time
    ) {
      setIsComplete(true);
      recordSuccess();
      setError("");
    } else {
      setError("Incorrect values. Try again!");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-8">
      {/* Instructions Card */}
      <div className="flex justify-center mb-8">
        <div className="bg-white rounded-xl p-6 max-w-2xl shadow-sm">
          <h1 className="text-3xl font-bold text-center mb-4 text-gray-800">
            Chart Read Challenge
          </h1>
          <p className="text-center text-gray-600">
            Study the stock price chart carefully. Enter the maximum price and
            the time it occurred to reveal the password. The price must be
            within 5% of the actual maximum.
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl p-6 mb-8 shadow-lg">
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#8884d8"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Input Form or Password Reveal */}
      <div className="flex justify-center">
        <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-lg">
          {!isComplete ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Maximum Price
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Enter price..."
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Time of Maximum (HH:00)
                </label>
                <select
                  value={maxTime}
                  onChange={(e) => setMaxTime(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                >
                  <option value="">Select time...</option>
                  {data.map((point) => (
                    <option key={point.time} value={point.time}>
                      {point.time}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Submit
              </button>
              {error && (
                <p className="text-red-500 text-sm text-center">{error}</p>
              )}
            </form>
          ) : (
            <div className="text-center">
              <h2 className="text-2xl font-bold text-green-800 mb-2">
                Congratulations!
              </h2>
              <p className="text-green-700">
                The password is: {PASSWORD_ChartRead}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChartRead;
