import type { ProductComponentType } from "src/types/shared";
import { getPathString } from "src/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function mapApiProduct(p: any): ProductComponentType {
  const price = p.price_promo ?? p.price_origin ?? 0;
  const discount = p.price_promo ? (p.price_origin ?? 0) - p.price_promo : 0;
  const media = [] as string[];
  if (p.preview_picture && p.preview_picture.w800) media.push(p.preview_picture.w800);
  if (p.color_images && typeof p.color_images === "object") {
    const keys = Object.keys(p.color_images);
    if (keys.length && media.length === 0) {
      const first = p.color_images[keys[0]];
      if (Array.isArray(first) && first[0] && first[0].url) media.push(first[0].url);
    }
  }

  return {
    id: p.slug ?? p.code ?? String(p.id ?? ""),
    title: p.name ?? p.title ?? "",
    price: price,
    discount: discount,
    shippingCost: 0,
    mediaURLs: media.length ? media : ["/assets/images/jordan-1-low.webp"],
    gender: "UNISEX",
    sku: p.code ?? "",
    details: p.desc_short_safe ?? p.desc_safe ?? "",
    salesCount: p.times_purchased ?? 0,
    color: "",
    sizes: [],
    year: undefined,
    type: "LOW",
    ratings: p.product_average_rating ?? 0,
    dateAdded: new Date().toISOString(),
  } as ProductComponentType;
}

export async function fetchProducts(): Promise<ProductComponentType[]> {
  const res = await fetch(`${API_BASE}/api/products/`);
  if (!res.ok) throw new Error(`Products fetch failed ${res.status}`);
  const data = await res.json();
  return data.map(mapApiProduct);
}

export async function fetchProductBySlug(slug: string): Promise<ProductComponentType | null> {
  try {
    const res = await fetch(`${API_BASE}/api/products/${slug}/`);
    if (!res.ok) return null;
    const p = await res.json();
    return mapApiProduct(p);
  } catch (e) {
    return null;
  }
}

export async function fetchProductSlugs(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/products/`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.map((p: any) => p.slug ?? getPathString(`${p.name} ${p.code ?? ""}`));
}
