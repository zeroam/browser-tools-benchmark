import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";
import { PASSWORD_ShopAdmin, TASK_ID_ShopAdmin } from "./ShopAdmin";
import { Product, products as initialProducts } from "./shopping/products";

interface EditableProduct {
  name: string;
  description: string;
  category: string;
  price: string;
}

export default function ShopAdminEdit() {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ShopAdmin);
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [editedFields, setEditedFields] = useState<EditableProduct>({
    name: "",
    description: "",
    category: "",
    price: "",
  });
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");

  // The target product and price that needs to be changed to complete the challenge
  const targetProduct = initialProducts.find((p) => p.name === "Watermelon");
  const targetPrice = 6.85;

  useEffect(() => {
    const foundProduct = initialProducts.find(
      (p) => p.id === parseInt(productId || "")
    );
    if (foundProduct) {
      setProduct(foundProduct);
      setEditedFields({
        name: foundProduct.name,
        description: foundProduct.description,
        category: foundProduct.category,
        price: foundProduct.price.toString(),
      });
    } else {
      navigate("/shop-admin");
    }
  }, [productId, navigate]);

  const handleInputChange = (field: keyof EditableProduct, value: string) => {
    setEditedFields((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = () => {
    if (!product) return;

    const updatedPrice = parseFloat(editedFields.price);
    if (isNaN(updatedPrice) || updatedPrice < 0) {
      setMessage("Please enter a valid price");
      return;
    }

    // Check if this edit completes the challenge
    if (
      product.id === targetProduct?.id &&
      Math.abs(updatedPrice - targetPrice) < 0.01
    ) {
      setPassword(PASSWORD_ShopAdmin);
      setMessage(
        "Congratulations! You've successfully updated the watermelon price to the correct value!"
      );
      recordSuccess();
    } else {
      navigate("/shop-admin");
    }
  };

  if (!product) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Edit Product</h1>
          <button
            onClick={() => navigate("/shop-admin")}
            className="text-gray-600 hover:text-gray-900"
          >
            Back to Products
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-6">
            <span className="text-4xl mr-4">{product.emoji}</span>
            <div className="flex-1">
              <div className="text-sm text-gray-500 mb-1">
                Product ID: {product.id}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                value={editedFields.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={editedFields.description}
                onChange={(e) =>
                  handleInputChange("description", e.target.value)
                }
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={editedFields.category}
                onChange={(e) => handleInputChange("category", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {Array.from(
                  new Set(initialProducts.map((p) => p.category))
                ).map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-gray-500">$</span>
                <input
                  type="number"
                  step="0.01"
                  value={editedFields.price}
                  onChange={(e) => handleInputChange("price", e.target.value)}
                  className="w-full pl-7 pr-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter price..."
                />
              </div>
            </div>

            {message && (
              <div className="p-4 rounded-lg bg-green-50">
                <p className="text-green-800">{message}</p>
                {password && (
                  <p className="mt-2 font-bold text-green-800">
                    Password: {password}
                  </p>
                )}
              </div>
            )}

            <div className="flex justify-end gap-4 pt-4">
              <button
                onClick={() => navigate("/shop-admin")}
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
