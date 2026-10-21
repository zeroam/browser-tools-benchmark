export default function AdClicked() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="text-6xl mb-4">🎯</div>
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Advertisement Clicked
        </h1>
        <p className="text-gray-600 mb-6">
          This is a demo advertisement. In a real application, this would lead
          to an advertiser's landing page.
        </p>
      </div>
    </div>
  );
}
