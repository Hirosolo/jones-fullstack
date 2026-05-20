import { useRouter } from "next/router";
import { useEffect } from "react";
import { getPathString } from "src/utils";
import { categories } from "@Components/header/MenuLists";

export default function CategoryRedirect() {
  const router = useRouter();

  useEffect(() => {
    if (router.query.categoryId) {
      const categorySlug = Array.isArray(router.query.categoryId)
        ? router.query.categoryId.join("/")
        : router.query.categoryId;

      if (categorySlug === "all") {
        // Redirect to products page showing all products
        router.replace("/products");
      } else {
        // Find the category name from the slug
        const categoryName =
          categories.find((c) => getPathString(c) === categorySlug) ||
          categorySlug
            .split("-")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");

        // Redirect to /products with category query param
        router.replace(`/products?category=${encodeURIComponent(categoryName)}`);
      }
    }
  }, [router]);

  return <div>Redirecting...</div>;
}

