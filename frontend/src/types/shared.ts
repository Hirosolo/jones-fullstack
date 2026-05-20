import type { NextApiRequest, NextApiResponse } from "next";

export type HTTPMethods = "GET" | "POST" | "PUT" | "DELETE";

export type AsyncAPIHandler = (
  req: NextApiRequest,
  res: NextApiResponse,
  next: Function
) => Promise<void> | void;

export interface DefaultResponse {
  error?: boolean;
  success?: boolean;
  message: string | string[];
  data?: unknown;
}

export enum Role {
  USER = "USER",
  ADMIN = "ADMIN",
}

export enum Gender {
  MEN = "MEN",
  WOMEN = "WOMEN",
  KIDS = "KIDS",
  BABY = "BABY",
  UNISEX = "UNISEX",
}

export enum Category {
  HIGH = "HIGH",
  MID = "MID",
  LOW = "LOW",
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  phoneNumber?: string;
  deactivated?: boolean;
  firstName?: string;
  lastName?: string;
  avatarURL?: string;
}

export interface Product {
  id: string;
  title: string;
  price: number;
  discount: number;
  shippingCost: number;
  mediaURLs: string[];
  gender: Gender;
  sku: string;
  details: string;
  salesCount: number;
  color: string;
  sizes: number[];
  year?: number;
  type: Category;
}

export interface Wishlist {
  userId: string;
  productId: string;
}

export interface CartItem {
  cartId: number;
  productId: string;
  size: number;
  quantity: number;
  total: number;
}

export interface Review {
  userId: string;
  productId: string;
  comment?: string;
  rating: number;
  addedAt: string;
}

export type WishlistType = Wishlist & { product: Product };
export type CartType = CartItem & { product: Product };

export interface UserProducts<T extends WishlistType | CartType> {
  productIds: string[];
  items: { [productId: string]: T };
  count: number;
  total: number;
  shippingTotal: number;
}

export type UserTypeNormalized = Partial<User> & {
  wishlist: UserProducts<WishlistType>;
  cart: UserProducts<CartType>;
  isAuth: boolean;
  processing: boolean;
};

export type UserType = Partial<User> & {
  wishlist: WishlistType[];
  cart: CartType[];
  isAuth: boolean;
};

export interface ProductComponentType extends Product {
  small?: boolean;
  blurDataUrl?: string;
  ratings: number;
  dateAdded: string;
}
