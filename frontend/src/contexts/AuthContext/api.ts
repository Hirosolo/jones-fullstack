import type { DefaultResponse } from "src/types/shared";

export async function postWishlistItem(id: string): Promise<DefaultResponse> {
  return { success: true, message: "Added to wishlist (Mock)" };
}

export async function deleteWishlistItem(id: string): Promise<DefaultResponse> {
  return { success: true, message: "Removed from wishlist (Mock)" };
}

export async function postCartItem(
  id: string,
  quantity: number,
  size: number
): Promise<DefaultResponse> {
  return { 
    success: true, 
    message: "Added to cart (Mock)",
    data: { productId: id, quantity, size, total: 0 } // Basic stub
  };
}

export async function deleteCartItem(id: string): Promise<DefaultResponse> {
  return { success: true, message: "Removed from cart (Mock)" };
}

export async function emptyUserCart(): Promise<DefaultResponse> {
  return { success: true, message: "Cart emptied (Mock)" };
}
