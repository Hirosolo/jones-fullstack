import { ProductComponentType, Gender, Category, Role } from "../types/shared";

export const MOCK_PRODUCTS: ProductComponentType[] = [
  {
    id: "1",
    title: "Air Jordan High Top",
    price: 65,
    discount: 15,
    shippingCost: 0,
    mediaURLs: ["/assets/images/air-jordan-1-high.webp"],
    gender: Gender.MEN,
    sku: "SHOE-001",
    details:
      "A clean high-top silhouette with premium materials and all-day comfort.",
    salesCount: 980,
    color: "Red",
    sizes: [8, 9, 10, 11, 12, 13],
    year: 2025,
    type: Category.HIGH,
    ratings: 4.8,
    dateAdded: new Date().toISOString(),
  },
  {
    id: "2",
    title: "Street Runner Mid",
    price: 140,
    discount: 10,
    shippingCost: 0,
    mediaURLs: ["/assets/images/jordan-1-mid.webp"],
    gender: Gender.WOMEN,
    sku: "SHOE-002",
    details:
      "Mid-top styling with a versatile profile that works with casual fits.",
    salesCount: 760,
    color: "Grey",
    sizes: [6, 7, 8, 9, 10],
    year: 2024,
    type: Category.MID,
    ratings: 4.6,
    dateAdded: new Date().toISOString(),
  },
  {
    id: "3",
    title: "Everyday Low Sneaker",
    price: 110,
    discount: 0,
    shippingCost: 0,
    mediaURLs: ["/assets/images/jordan-1-low.webp"],
    gender: Gender.UNISEX,
    sku: "SHOE-003",
    details:
      "A low-profile sneaker with a minimal shape and easy daily wearability.",
    salesCount: 1420,
    color: "White",
    sizes: [6, 7, 8, 9, 10, 11],
    year: 2024,
    type: Category.LOW,
    ratings: 4.7,
    dateAdded: new Date().toISOString(),
  }
];

export const MOCK_RATES = [
  { symbol: "USD", rate: 1 },
  { symbol: "EUR", rate: 0.92 },
  { symbol: "GBP", rate: 0.79 },
  { symbol: "JPY", rate: 150.5 }
];

export const MOCK_USER = {
  id: "mock-user-id",
  username: "Guest User",
  email: "guest@example.com",
  role: Role.USER,
  isAuth: false,
  wishlist: [],
  cart: [],
};
